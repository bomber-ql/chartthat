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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

app = FastAPI(title="智能数据图表 PPT 生成器", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """容器/探活用健康检查（不带 /api 前缀，避免与前端路由混淆）。"""
    return {"status": "ok"}


# ---- 生产环境：托管前端构建产物（SPA） ----
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        # API 路径不应进入静态回退
        if full_path.startswith("api/"):
            return FileResponse(FRONTEND_DIST / "index.html")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
