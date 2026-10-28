"""生产静态托管回退行为（v1.28 soft-404 修复）：

- 未知页面路径 → 真 404（不再回 index.html+200 的 soft-404）
- 未注册 /api/* → JSON 404（不回 HTML）
- 首页 / 目录索引 / 既有静态页回归 200

依赖 frontend/dist 构建产物；未构建则整文件跳过（dev 沙箱 pnpm build 后存在）。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import FRONTEND_DIST, app

pytestmark = pytest.mark.skipif(
    not FRONTEND_DIST.is_dir(), reason="frontend/dist 未构建，静态回退路由未注册"
)

client = TestClient(app)


def test_unknown_page_returns_real_404() -> None:
    resp = client.get("/definitely-not-a-page-xyz")
    assert resp.status_code == 404
    # 404 页为 HTML 且带 noindex（dist 含 404.html 时）
    if (FRONTEND_DIST / "404.html").is_file():
        assert "noindex" in resp.text
        assert "404" in resp.text


def test_unknown_api_returns_json_404() -> None:
    resp = client.get("/api/definitely-not-an-endpoint")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["code"] == "NOT_FOUND"


def test_home_serves_index() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_directory_index_served() -> None:
    # /guides/ 目录索引（AdSense 内容页依赖）
    resp = client.get("/guides/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_existing_static_page_served() -> None:
    resp = client.get("/about.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_path_traversal_rejected() -> None:
    # 越过 dist 根的路径不得命中文件（resolve + parents 校验）
    resp = client.get("/../backend/app/main.py")
    assert resp.status_code in (404, 422)
