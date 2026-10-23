"""HTTP 路由层（SPEC §7）。

已实现：
- GET  /api/health         健康检查
- POST /api/parse          M1+M2：文本/CSV/Excel → SemanticTable（SPEC §5.3）
- POST /api/recommend      M3：SemanticTable → ChartSpec[]（SPEC §5.4/§6 M3）
- POST /api/generate-pptx  M4：单图自描述请求 → .pptx 文件流（SPEC §5.6/§6 M4）
- POST /api/generate-gif           M4b：GIF 帧序列 → 直出 .gif（SPEC §5.6a/§6a，v1.12）
- POST /api/generate-animated-pptx  M4b：GIF 帧序列 → 动效版 .pptx（SPEC §5.6a/§6a，v1.11）
- GET  /api/stats          使用统计（SPEC §7.1，v1.19；STATS_TOKEN 保护，不匹配 404）

待实现（随里程碑推进）：/api/generate（多图 deck，§5.6b）。
错误响应统一为 ApiError（SPEC §5.7）：{"code", "message", "details"}。
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import anyio
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from starlette.datastructures import UploadFile

from app.analytics import get_stats, record_event
from app.config import settings
from app.modules import ParseError, analyze_table, parse_bytes, parse_text
from app.modules.gif_builder import build_animated_gif, build_animated_pptx
from app.modules.pptx_builder import PptxValidationError, build_pptx
from app.modules.recommender import RecommendationError, normalize_lang, recommend_charts

router = APIRouter(prefix="/api")


def _client_lang(request: Request) -> str | None:
    """埋点语言：前端 X-Lang 头（非法值丢弃，不做归一化——统计原始分布）。"""
    raw = request.headers.get("x-lang", "").strip().lower()
    return raw or None


def _client_country(request: Request) -> str | None:
    """埋点国家：仅取 Cloudflare CF-IPCountry 两位国家码；XX（未知）/T1（Tor）记为 NULL。"""
    raw = request.headers.get("cf-ipcountry", "").strip().upper()
    if not raw or raw in ("XX", "T1"):
        return None
    return raw


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
    "UNSUPPORTED_CHART": 400,
    "PARSE_TOO_LARGE": 413,
    "LLM_INVALID_JSON": 502,
    "LLM_UNAVAILABLE": 502,
    "PPTX_BUILD_FAILED": 500,
}

PPTX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)


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
            source = (file.filename or "").rsplit(".", 1)[-1].lower() or "file"
        else:
            try:
                body: Any = await request.json()
            except Exception as exc:  # noqa: BLE001 - 统一转为契约错误
                raise ParseError("PARSE_EMPTY", "请求体不是合法 JSON") from exc
            if not isinstance(body, dict) or not isinstance(body.get("text"), str):
                raise ParseError("PARSE_EMPTY", "请求体应为 JSON：{\"text\": \"...\"}")
            raw = parse_text(body["text"])
            source = "text"
        table = analyze_table(raw)
        record_event(
            "parse",
            lang=_client_lang(request),
            country=_client_country(request),
            meta={"source": source, "rows": len(table.get("rows", [])), "cols": len(table.get("columns", []))},
        )
        return JSONResponse(content=table)
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
        # v1.14/v1.17：可选界面语言（与 columns/rows 同级），决定 title/reasoning 语言；
        # 列名等数据保持原文。缺省/非 zh 一律回退英文（出海默认英文）
        lang = body.get("lang", "en")
        table = {k: v for k, v in body.items() if k != "lang"}
        # recommend_charts 为同步实现（内部 httpx.Client），交由线程池执行
        result = await anyio.to_thread.run_sync(
            lambda: recommend_charts(table, lang=lang)  # type: ignore[misc]
        )
        recs = result.get("recommendations") or []
        record_event(
            "recommend",
            lang=normalize_lang(lang),  # 以归一化后的生成语言为准（SPEC v1.19）
            country=_client_country(request),
            meta={
                "degraded": bool(result.get("degraded")),
                "count": len(recs),
                "chart_types": [r.get("chart_type") for r in recs if isinstance(r, dict)],
            },
        )
        return JSONResponse(content=result)
    except RecommendationError as exc:
        return _error_response(ParseError("VALIDATION_FAILED", str(exc)))
    except ParseError as exc:
        return _error_response(exc)


@router.post("/generate-pptx")
async def generate_pptx_endpoint(request: Request):
    """SPEC §5.6/§6 M4：{chart_type, config?, data} → .pptx 文件流。"""
    try:
        try:
            body: Any = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise PptxValidationError("VALIDATION_FAILED", "请求体不是合法 JSON") from exc

        def _build() -> bytes:
            return build_pptx(body if isinstance(body, dict) else {})

        try:
            blob = await anyio.to_thread.run_sync(_build)
        except ParseError as exc:
            # 契约/校验类错误（含不支持的图型）→ 400，保留细分 code
            return _error_response(exc)

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # v1.11：标准导出恒为 chart-*.pptx；动效版走 /api/generate-animated-pptx（§5.6a）。
        headers = {"Content-Disposition": f'attachment; filename="chart-{stamp}.pptx"'}
        payload = body if isinstance(body, dict) else {}
        record_event(
            "generate-pptx",
            lang=_client_lang(request),
            country=_client_country(request),
            meta={"chart_type": payload.get("chart_type"), "show_labels": bool(payload.get("show_labels", False))},
        )
        return Response(content=blob, media_type=PPTX_MEDIA_TYPE, headers=headers)
    except ParseError as exc:
        return _error_response(exc)


@router.post("/generate-gif")
async def generate_gif_endpoint(request: Request):
    """SPEC §5.6a/§6a（v1.12 主形态，R-6）：{frames, frame_ms?, transparent?} → .gif 文件流。"""
    try:
        try:
            body: Any = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise PptxValidationError("VALIDATION_FAILED", "请求体不是合法 JSON") from exc

        def _build() -> bytes:
            return build_animated_gif(body if isinstance(body, dict) else {})

        try:
            blob = await anyio.to_thread.run_sync(_build)
        except ParseError as exc:
            return _error_response(exc)

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        headers = {"Content-Disposition": f'attachment; filename="chart-{stamp}.gif"'}
        payload = body if isinstance(body, dict) else {}
        record_event(
            "generate-gif",
            lang=_client_lang(request),
            country=_client_country(request),
            meta={
                "frames": len(payload.get("frames") or []),
                "frame_ms": payload.get("frame_ms", 100),
                "transparent": bool(payload.get("transparent", False)),
            },
        )
        return Response(content=blob, media_type="image/gif", headers=headers)
    except ParseError as exc:
        return _error_response(exc)


@router.post("/generate-animated-pptx")
async def generate_animated_pptx_endpoint(request: Request):
    """SPEC §5.6a/§6a（v1.11 保留，R-6）：{title?, frames, frame_ms?, transparent?} → 动效版 .pptx。"""
    try:
        try:
            body: Any = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise PptxValidationError("VALIDATION_FAILED", "请求体不是合法 JSON") from exc

        def _build() -> bytes:
            return build_animated_pptx(body if isinstance(body, dict) else {})

        try:
            blob = await anyio.to_thread.run_sync(_build)
        except ParseError as exc:
            return _error_response(exc)

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        headers = {"Content-Disposition": f'attachment; filename="chart-animated-{stamp}.pptx"'}
        payload = body if isinstance(body, dict) else {}
        record_event(
            "generate-animated-pptx",
            lang=_client_lang(request),
            country=_client_country(request),
            meta={
                "frames": len(payload.get("frames") or []),
                "frame_ms": payload.get("frame_ms", 100),
                "transparent": bool(payload.get("transparent", False)),
                "has_title": bool(payload.get("title")),
            },
        )
        return Response(content=blob, media_type=PPTX_MEDIA_TYPE, headers=headers)
    except ParseError as exc:
        return _error_response(exc)


@router.get("/stats")
async def stats_endpoint(token: str = Query(default="")) -> JSONResponse:
    """SPEC §7.1（v1.19）：使用统计。token 未配置或不匹配一律 404，不暴露端点存在性。"""
    if not settings.stats_token or token != settings.stats_token:
        raise HTTPException(status_code=404)
    return JSONResponse(content=await anyio.to_thread.run_sync(get_stats))
