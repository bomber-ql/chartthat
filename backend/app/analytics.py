"""轻量使用统计埋点（SPEC v1.19 §7.1）。

SQLite 单文件存储，五个业务端点成功响应时各记一条事件。
隐私红线（不可违反）：
- 不记录 IP、UA、Referer、请求体原文、用户表格数据、图表标题与列名；
- lang 取前端 X-Lang 请求头（recommend 以 body.lang 归一化值为准）；
- country 仅取 Cloudflare CF-IPCountry 两位国家码（无代理时为 NULL）；
- meta 只放产品维度（source/rows/cols、degraded/chart_types、chart_type、frames 等）。

埋点写入失败静默降级（warning 日志），绝不影响业务响应。
单连接 + 模块级锁保证线程安全；写入为微秒级同步调用。
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    event   TEXT NOT NULL,
    lang    TEXT,
    country TEXT,
    meta    TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_event ON events(event);
"""


def _db_path() -> Path:
    data_dir = os.getenv("DATA_DIR", "").strip()
    base = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base / "analytics.db"


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_db_path(), check_same_thread=False)
        _conn.executescript(_SCHEMA)
    return _conn


def _reset_for_tests() -> None:
    """测试钩子：关闭并重置模块级连接（配合 monkeypatch DATA_DIR 使用）。"""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None


def record_event(
    event: str,
    *,
    lang: str | None = None,
    country: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """记录一条使用事件；任何失败仅记日志，不向调用方抛错。"""
    try:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = json.dumps(meta, ensure_ascii=False) if meta else None
        with _lock:
            _get_conn().execute(
                "INSERT INTO events (ts, event, lang, country, meta) VALUES (?, ?, ?, ?, ?)",
                (ts, event, lang or None, country or None, payload),
            )
            _get_conn().commit()
    except Exception:  # noqa: BLE001 - 埋点绝不影响业务
        logger.warning("analytics: record_event(%s) failed", event, exc_info=True)


def _counts_by_event(where: str = "", params: tuple[Any, ...] = ()) -> dict[str, int]:
    rows = _get_conn().execute(
        f"SELECT event, COUNT(*) FROM events {where} GROUP BY event", params
    ).fetchall()
    return {str(ev): int(n) for ev, n in rows}


def get_stats() -> dict[str, Any]:
    """汇总统计（§7.1）：累计/今日/近 30 天、近 14 天按日、语言与图型分布。"""
    with _lock:
        conn = _get_conn()
        totals = _counts_by_event()

        now = datetime.now(timezone.utc)
        today_start = now.strftime("%Y-%m-%d") + "T00:00:00Z"
        today = _counts_by_event("WHERE ts >= ?", (today_start,))

        since_30d = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        last_30d = _counts_by_event("WHERE ts >= ?", (since_30d,))

        since_14d = (now - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
        daily_rows = conn.execute(
            "SELECT substr(ts, 1, 10) AS day, event, COUNT(*) FROM events "
            "WHERE ts >= ? GROUP BY day, event ORDER BY day",
            (since_14d,),
        ).fetchall()
        daily = [{"day": str(d), "event": str(ev), "n": int(n)} for d, ev, n in daily_rows]

        lang_rows = conn.execute(
            "SELECT lang, COUNT(*) FROM events WHERE event = 'recommend' AND lang IS NOT NULL "
            "GROUP BY lang ORDER BY COUNT(*) DESC"
        ).fetchall()
        langs = {str(lg): int(n) for lg, n in lang_rows}

        type_rows = conn.execute(
            "SELECT json_extract(meta, '$.chart_type'), COUNT(*) FROM events "
            "WHERE event = 'generate-pptx' AND meta IS NOT NULL "
            "GROUP BY json_extract(meta, '$.chart_type') ORDER BY COUNT(*) DESC"
        ).fetchall()
        chart_types = {str(ct): int(n) for ct, n in type_rows if ct is not None}

    return {
        "totals": totals,
        "today": today,
        "last_30d": last_30d,
        "daily": daily,
        "langs": langs,
        "chart_types": chart_types,
    }
