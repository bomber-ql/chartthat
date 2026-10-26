"""安全中间件：内存速率限制 + 请求体大小硬上限（SPEC v1.24 §7.2）。

设计要点：
- 限流为单机固定窗口（单容器部署足够；未来多副本时上 Redis）。
- 真实客户端 IP 优先取 Cloudflare 注入的 CF-Connecting-IP（app 端口不对宿主
  发布，只经 Caddy 回源，该头可信）；其次 X-Forwarded-For 首段，最后回退
  到直连 peer。环回地址豁免，便于容器内网探活与本地测试。
- LLM 端点（/api/recommend）档位最紧；生成类次之；解析类稍宽；
  /api/health、/api/stats、静态资源不计数。
- body 限制为纯 ASGI 包装：content-length 预检 + receive 流式累计兜底，
  覆盖不发 content-length 的分块请求。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

from starlette.responses import JSONResponse, Response

# ---- 限流档位（次 / 60 秒窗口） ----
WINDOW_SECONDS = 60
TIERS: tuple[tuple[str, int], ...] = (
    ("/api/recommend", 20),               # 最贵：可能触发 LLM token 计费
    ("/api/generate-gif", 15),            # CPU/内存密集
    ("/api/generate-animated-pptx", 15),
    ("/api/generate-pptx", 20),
    ("/api/parse", 30),
)
GLOBAL_LIMIT = 60                        # 任意 /api 调用兜底上限
EXEMPT_PREFIXES = ("/api/health", "/api/stats", "/healthz")

_LOOPBACK = ("127.0.0.1", "::1", "localhost")


@dataclass
class _Window:
    started_at: float
    count: int = 0


@dataclass
class FixedWindowLimiter:
    """固定窗口计数器；identity=客户端 IP，bucket=端点档位键。"""

    window_seconds: int = WINDOW_SECONDS
    _buckets: dict[tuple[str, str], _Window] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def hit(self, identity: str, bucket: str, limit: int, now: float | None = None) -> tuple[bool, int]:
        """返回 (是否放行, 距窗口重置秒数)。"""
        now = now if now is not None else time.monotonic()
        key = (identity, bucket)
        with self._lock:
            win = self._buckets.get(key)
            if win is None or now - win.started_at >= self.window_seconds:
                win = _Window(started_at=now)
                self._buckets[key] = win
                self._gc(now)
            win.count += 1
            retry_after = int(self.window_seconds - (now - win.started_at)) + 1
            return win.count <= limit, retry_after

    def _gc(self, now: float) -> None:
        """惰性清理过期窗口，防止内存无限增长。"""
        stale = [k for k, w in self._buckets.items() if now - w.started_at >= self.window_seconds]
        for k in stale:
            self._buckets.pop(k, None)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


limiter = FixedWindowLimiter()


def client_identity(headers, peer_host: str | None) -> str:
    """提取限流身份。app 仅经 Caddy 回源，CF-Connecting-IP 可信。"""
    cf = headers.get("cf-connecting-ip", "").strip()
    if cf:
        return cf
    xff = headers.get("x-forwarded-for", "").strip()
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return peer_host or "unknown"


def _tier_for(path: str) -> tuple[str, int]:
    for prefix, limit in TIERS:
        if path.startswith(prefix):
            return prefix, limit
    return "__global__", GLOBAL_LIMIT


def _is_loopback(identity: str) -> bool:
    return identity in _LOOPBACK


def rate_limit_response(retry_after: int) -> Response:
    return JSONResponse(
        status_code=429,
        content={
            "code": "RATE_LIMITED",
            "message": "Too many requests, please slow down.",
            "details": {"retry_after_seconds": retry_after},
        },
        headers={"Retry-After": str(retry_after)},
    )


class RateLimitMiddleware:
    """ASGI 限流中间件：超限直接回 429，不进入业务层。"""

    def __init__(self, app, enabled: bool = True):
        self.app = app
        self.enabled = enabled

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/") or any(path.startswith(p) for p in EXEMPT_PREFIXES):
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        peer = (scope.get("client") or (None, 0))[0]
        identity = client_identity(headers, peer)

        if _is_loopback(identity):
            await self.app(scope, receive, send)
            return

        bucket, limit = _tier_for(path)
        allowed, retry_after = limiter.hit(identity, bucket, limit)
        if not allowed:
            response = rate_limit_response(retry_after)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class _BodyTooLarge(Exception):
    """chunked 请求累计超限时在业务层读取 body 时抛出，由中间件统一回 413。"""


class BodySizeLimitMiddleware:
    """ASGI 请求体上限：content-length 预检 + receive 累计兜底。"""

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        if method not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return

        declared = 0
        for k, v in scope.get("headers", []):
            if k == b"content-length":
                try:
                    declared = int(v.decode())
                except ValueError:
                    declared = 0
                break

        if declared > self.max_bytes:
            await self._reject(scope, receive, send)
            return

        total = 0

        async def limited_receive():
            nonlocal total
            msg = await receive()
            if msg.get("type") == "http.request":
                total += len(msg.get("body", b""))
                if total > self.max_bytes:
                    raise _BodyTooLarge
            return msg

        if declared:
            # 有 content-length 且已通过预检，无需累计开销
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await self._reject(scope, receive, send)

    async def _reject(self, scope, receive, send) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"Request body exceeds the maximum allowed size ({self.max_bytes} bytes).",
            },
        )
        await response(scope, receive, send)
