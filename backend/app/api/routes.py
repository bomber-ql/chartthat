"""HTTP 路由层（SPEC §7）。

已实现：
- GET  /api/health    健康检查
- POST /api/parse     M1+M2：文本/CSV/Excel → SemanticTable（SPEC §5.3）
- POST /api/recommend M3：SemanticTable → ChartSpec[]（SPEC §5.4/§6 M3）

待实现（随里程碑推进）：/api/generate（M4）。
错误响应统一为 ApiError（SPEC §5.7）：{"code", "message", "details"}。
"""
from __future__ import annotations

from typing import Any

import anyio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from app.modules import ParseError, analyze_table, parse_bytes, parse_text
from app.modules.recommender import RecommendationError, recommend_charts

router = APIRouter(prefix="/api")


def _is_semantic_table(body: Any) -> bool:
    """轻量结构检查；字段级契约由 M2 输出保证，M3 validators 兜底。"""
    if not isinstance(body, dict):
        return False
    cols = body.get("columns")
    rows = body.get("rows")
    if not isinstance(cols, list) or not cols or not isinstance(rows, list) or not rows:
        return False
    return all(
        isinstance(c, dict) and isinstance(c.get("name"), str) and c.get("role") in
        ("dimension", "measure", "percent", "meta")
        for c in cols
    )

_ERROR_HTTP_STATUS = {
    "PARSE_EMPTY": 400,
    "PARSE_UNSUPPORTED": 400,
    "VALIDATION_FAILED": 400,
    "PARSE_TOO_LARGE": 413,
    "LLM_INVALID_JSON": 502,
    "LLM_UNAVAILABLE": 502,
    "PPTX_BUILD_FAILED": 500,
}


def _error_response(exc: ParseError) -> JSONResponse:
    status = _ERROR_HTTP_STATUS.get(exc.code, 500)
    return JSONResponse(
        status_code=status,
        content={"code": exc.code, "message": exc.message, "details": exc.details},
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/parse")
async def parse_endpoint(request: Request) -> JSONResponse:
    """SPEC §7 /api/parse：multipart 文件上传 或 JSON {"text", "sheet_name"?}。"""
    try:
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            form = await request.form()
            file = form.get("file")
            if not isinstance(file, UploadFile):
                raise ParseError("PARSE_EMPTY", "未接收到文件（字段名应为 file）")
            data = await file.read()
            sheet_name_raw = form.get("sheet_name")
            sheet_name = str(sheet_name_raw) if sheet_name_raw else None
            raw = parse_bytes(data, file.filename or "upload", sheet_name)
        else:
            try:
                body: Any = await request.json()
            except Exception as exc:  # noqa: BLE001 - 统一转为契约错误
                raise ParseError("PARSE_EMPTY", "请求体不是合法 JSON") from exc
            if not isinstance(body, dict) or not isinstance(body.get("text"), str):
                raise ParseError("PARSE_EMPTY", "请求体应为 JSON：{\"text\": \"...\"}")
            raw = parse_text(body["text"])
        return JSONResponse(content=analyze_table(raw))
    except ParseError as exc:
        return _error_response(exc)


@router.post("/recommend")
async def recommend_endpoint(request: Request) -> JSONResponse:
    """SPEC §7 /api/recommend：入参为 SemanticTable，出参 {recommendations, degraded}。"""
    try:
        try:
            body: Any = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise ParseError("VALIDATION_FAILED", "请求体不是合法 JSON") from exc
        if not _is_semantic_table(body):
            raise ParseError("VALIDATION_FAILED", "请求体必须为 SemanticTable：{columns:[...], rows:[...]}")
        # recommend_charts 为同步实现（内部 httpx.Client），交由线程池执行
        result = await anyio.to_thread.run_sync(recommend_charts, body)
        return JSONResponse(content=result)
    except RecommendationError as exc:
        return _error_response(ParseError("VALIDATION_FAILED", str(exc)))
    except ParseError as exc:
        return _error_response(exc)
