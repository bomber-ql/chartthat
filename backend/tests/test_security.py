"""安全中间件测试（SPEC v1.24 §7.2）：限流与请求体上限。"""
from __future__ import annotations

import time

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app import security
from app.security import (
    BodySizeLimitMiddleware,
    FixedWindowLimiter,
    RateLimitMiddleware,
    client_identity,
)


@pytest.fixture(autouse=True)
def _reset_limiter():
    security.limiter.reset()
    yield
    security.limiter.reset()


def _app_with_middlewares(*, max_bytes: int = 100, enabled: bool = True) -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_bytes)
    app.add_middleware(RateLimitMiddleware, enabled=enabled)

    @app.post("/api/recommend")
    async def recommend():
        return {"ok": True}

    @app.post("/api/parse")
    async def parse(request: Request):
        # 模拟真实端点消费请求体（触发 chunked receive 累计）
        await request.body()
        return {"ok": True}

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


class TestFixedWindowLimiter:
    def test_allows_up_to_limit_then_blocks(self):
        limiter = FixedWindowLimiter(window_seconds=60)
        results = [limiter.hit("1.1.1.1", "/api/recommend", 3)[0] for _ in range(5)]
        assert results == [True, True, True, False, False]

    def test_window_resets(self):
        limiter = FixedWindowLimiter(window_seconds=60)
        assert limiter.hit("ip", "b", 1, now=100.0)[0] is True
        assert limiter.hit("ip", "b", 1, now=159.0)[0] is False
        assert limiter.hit("ip", "b", 1, now=160.0)[0] is True

    def test_keys_isolated_by_identity_and_bucket(self):
        limiter = FixedWindowLimiter()
        assert limiter.hit("a", "/api/recommend", 1)[0] is True
        assert limiter.hit("a", "/api/recommend", 1)[0] is False
        # 不同 IP
        assert limiter.hit("b", "/api/recommend", 1)[0] is True
        # 同 IP 不同档位
        assert limiter.hit("a", "/api/parse", 1)[0] is True

    def test_retry_after_positive(self):
        limiter = FixedWindowLimiter(window_seconds=60)
        _, retry = limiter.hit("ip", "b", 1, now=time.monotonic())
        assert 1 <= retry <= 61


class TestClientIdentity:
    def test_cf_connecting_ip_preferred(self):
        headers = {"cf-connecting-ip": "203.0.113.5", "x-forwarded-for": "10.0.0.1"}
        assert client_identity(headers, "172.17.0.1") == "203.0.113.5"

    def test_xff_fallback(self):
        headers = {"x-forwarded-for": "8.8.8.8, 1.1.1.1"}
        assert client_identity(headers, "172.17.0.1") == "8.8.8.8"

    def test_peer_last_resort(self):
        assert client_identity({}, "198.51.100.1") == "198.51.100.1"
        assert client_identity({}, None) == "unknown"


class TestRateLimitEndpoint:
    def test_recommend_tier_429_after_limit(self):
        client = TestClient(_app_with_middlewares())
        # 环回豁免：测试客户端 peer 是 testclient，非环回，但 TestClient 默认无代理头
        # peer host 为 "testclient"（starlette 固定值），会被计数。
        codes = [client.post("/api/recommend").status_code for _ in range(security.TIERS[0][1] + 3)]
        assert codes.count(200) == 20
        assert codes[-1] == 429
        resp = client.post("/api/recommend")
        assert resp.status_code == 429
        body = resp.json()
        assert body["code"] == "RATE_LIMITED"
        assert "retry_after_seconds" in body["details"]
        assert int(resp.headers["Retry-After"]) >= 1

    def test_tiers_independent(self):
        client = TestClient(_app_with_middlewares())
        # recommend 打满
        for _ in range(20):
            assert client.post("/api/recommend").status_code == 200
        assert client.post("/api/recommend").status_code == 429
        # parse 档位独立，仍可用
        assert client.post("/api/parse").status_code == 200

    def test_health_exempt(self):
        client = TestClient(_app_with_middlewares())
        for _ in range(80):
            assert client.get("/api/health").status_code == 200

    def test_disabled_via_config(self):
        client = TestClient(_app_with_middlewares(enabled=False))
        for _ in range(30):
            assert client.post("/api/recommend").status_code == 200

    def test_cf_ip_separates_clients(self):
        client = TestClient(_app_with_middlewares())
        # IP A 打满
        for _ in range(20):
            client.post("/api/recommend", headers={"CF-Connecting-IP": "9.9.9.9"})
        assert client.post("/api/recommend", headers={"CF-Connecting-IP": "9.9.9.9"}).status_code == 429
        # 另一 IP 不受影响
        assert client.post("/api/recommend", headers={"CF-Connecting-IP": "8.8.8.8"}).status_code == 200


class TestBodySizeLimit:
    def test_oversize_content_length_rejected_before_read(self):
        client = TestClient(_app_with_middlewares(max_bytes=100))
        resp = client.post("/api/parse", content=b"x" * 101)
        assert resp.status_code == 413
        assert resp.json()["code"] == "PAYLOAD_TOO_LARGE"

    def test_body_within_limit_passes(self):
        client = TestClient(_app_with_middlewares(max_bytes=100))
        resp = client.post("/api/parse", content=b"x" * 50)
        assert resp.status_code == 200

    def test_get_not_affected(self):
        client = TestClient(_app_with_middlewares(max_bytes=10))
        assert client.get("/api/health").status_code == 200

    def test_chunked_oversize_rejected(self):
        # 不发 content-length 的原始 ASGI 分块请求：receive 累计超限 → 413
        import asyncio

        app = _app_with_middlewares(max_bytes=20)

        async def call():
            chunks = [b"x" * 15, b"x" * 15]
            idx = {"i": 0}

            async def receive():
                i = idx["i"]
                idx["i"] += 1
                if i < len(chunks):
                    return {"type": "http.request", "body": chunks[i], "more_body": i < len(chunks) - 1}
                return {"type": "http.request", "body": b"", "more_body": False}

            status = {}

            async def send(msg):
                if msg["type"] == "http.response.start":
                    status["code"] = msg["status"]

            scope = {
                "type": "http",
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/api/parse",
                "raw_path": b"/api/parse",
                "query_string": b"",
                "headers": [(b"host", b"test")],
                "client": ("1.2.3.4", 1),
                "server": ("test", 80),
                "root_path": "",
                "app": app,
            }
            await app(scope, receive, send)
            return status["code"]

        assert asyncio.run(call()) == 413
