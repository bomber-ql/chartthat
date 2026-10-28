"""FastAPI 应用入口。

部署形态（与 .coze 对应）：
- dev：Vite dev server 监听对外端口（DEPLOY_RUN_PORT，默认 5000），
  并将 /api 代理到本服务（BACKEND_PORT，默认 8000），支持 HMR；
- prod：本服务直接监听 DEPLOY_RUN_PORT，并托管 frontend/dist 静态产物。
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings
from app.security import BodySizeLimitMiddleware, RateLimitMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

app = FastAPI(title="智能数据图表 PPT 生成器", version="0.1.0")

# 中间件为洋葱模型：最后 add 的在最外层。期望执行顺序
# CORS 预检/头 → 限流 → body 上限 → 业务，因此按反序注册。
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    # 通配 origin 下不可带 credentials（浏览器规范）；显式白名单才开启。
    allow_credentials=settings.cors_origins != ("*",),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, enabled=settings.rate_limit_enabled)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_bytes)

app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """容器/探活用健康检查（不带 /api 前缀，避免与前端路由混淆）。"""
    return {"status": "ok"}


# ---- 生产环境：托管前端构建产物（多页静态站，无前端路由） ----
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    not_found_page = FRONTEND_DIST / "404.html"

    @app.get("/{full_path:path}")
    async def static_fallback(full_path: str) -> Response:
        # 未注册的 API 路径：JSON 404。回 HTML 200 会让集成方与爬虫误判（v1.28）
        if full_path.startswith("api/"):
            return JSONResponse(
                {"code": "NOT_FOUND", "message": "Unknown API endpoint.", "details": None},
                status_code=404,
            )
        dist_root = FRONTEND_DIST.resolve()
        candidate = (FRONTEND_DIST / full_path).resolve()
        # 越界校验：candidate 必须等于 dist 根（根路径 "/"）或位于其内部
        in_dist = candidate == dist_root or dist_root in candidate.parents
        if in_dist and candidate.is_file():
            return FileResponse(candidate)
        # 目录形式（如 /guides/、/make/）命中其 index.html（多页静态索引）
        if in_dist and candidate.is_dir():
            dir_index = candidate / "index.html"
            if dir_index.is_file():
                return FileResponse(dir_index)
        # 本站无前端路由，未知路径必须真 404：回 index.html+200 是 soft-404，
        # 会被搜索引擎降权（GSC 覆盖报告 "Soft 404"）并稀释站点质量分（v1.28）
        if not_found_page.is_file():
            return FileResponse(not_found_page, status_code=404)
        return HTMLResponse(
            "<!doctype html><title>404 Not Found</title><h1>404 Not Found</h1>",
            status_code=404,
        )
