"""HTTP 路由层。

当前为应用骨架阶段（SPEC v1.0 待确认后实现业务模块）：
- GET /api/health 已可用；
- /api/parse、/api/recommend、/api/generate 待 SPEC 确认后按 SPEC §7 实现。
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
