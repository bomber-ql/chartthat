"""使用统计埋点测试（SPEC v1.19 §7.1）。

覆盖：
1. record_event / get_stats 单元口径（totals/langs/chart_types/daily 结构）；
2. /api/stats 端点保护（未配置或错误 token 一律 404，正确 token 200）；
3. 业务端点集成（parse/recommend/generate-pptx 成功后各记一条事件）；
4. 隐私口径（X-Lang 透传、CF-IPCountry XX/T1 记为 NULL）；
5. 埋点失败静默降级，不影响业务响应。

每个测试经 monkeypatch DATA_DIR 指向 tmp_path 隔离数据库。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.analytics as analytics
from app.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "sample.md"

BAR_REQUEST = {
    "chart_type": "bar",
    "title": "各平台 2025 MAU",
    "config": {"dimension": "平台"},
    "data": {
        "categories": ["微信", "抖音", "快手"],
        "series": [
            {"name": "2025 MAU", "kind": "bar", "axis": "primary", "unit": "yi",
             "data": [14.2, 11.7, 7.0]},
        ],
    },
}


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    analytics._reset_for_tests()
    yield tmp_path
    analytics._reset_for_tests()


def _rows(db_path: Path) -> list[sqlite3.Row]:
    db_file = db_path / "analytics.db"
    if not db_file.exists():
        return []  # 埋点从未触发（如业务失败路径），库文件未创建
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM events ORDER BY id").fetchall()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# record_event / get_stats 单元口径
# --------------------------------------------------------------------------- #

def test_record_and_stats_roundtrip(tmp_path: Path) -> None:
    analytics.record_event("parse", lang="zh", country="DE",
                           meta={"source": "text", "rows": 6, "cols": 5})
    analytics.record_event("recommend", lang="en",
                           meta={"degraded": True, "count": 3, "chart_types": ["bar", "line"]})
    analytics.record_event("generate-pptx", meta={"chart_type": "bar", "show_labels": False})
    analytics.record_event("generate-pptx", meta={"chart_type": "combo", "show_labels": True})

    stats = analytics.get_stats()
    assert stats["totals"] == {"parse": 1, "recommend": 1, "generate-pptx": 2}
    assert stats["today"]["parse"] == 1
    assert stats["last_30d"]["generate-pptx"] == 2
    assert stats["langs"] == {"en": 1}  # langs 仅统计 recommend 事件
    assert stats["chart_types"] == {"bar": 1, "combo": 1}
    assert {d["event"] for d in stats["daily"]} == {"parse", "recommend", "generate-pptx"}


def test_record_event_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> None:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(analytics, "_get_conn", _boom)
    analytics.record_event("parse")  # 不抛错即通过


def test_country_and_lang_nullable(tmp_path: Path) -> None:
    analytics.record_event("parse")
    rows = _rows(tmp_path)
    assert rows[0]["lang"] is None and rows[0]["country"] is None and rows[0]["meta"] is None


# --------------------------------------------------------------------------- #
# /api/stats 端点保护
# --------------------------------------------------------------------------- #

def test_stats_404_without_token_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.settings", SimpleNamespace(stats_token=""))
    client = TestClient(app)
    assert client.get("/api/stats").status_code == 404
    assert client.get("/api/stats", params={"token": "anything"}).status_code == 404


def test_stats_404_with_wrong_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.settings", SimpleNamespace(stats_token="secret"))
    client = TestClient(app)
    assert client.get("/api/stats").status_code == 404
    assert client.get("/api/stats", params={"token": "wrong"}).status_code == 404


def test_stats_200_with_correct_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.settings", SimpleNamespace(stats_token="secret"))
    analytics.record_event("parse", meta={"source": "text", "rows": 6, "cols": 5})
    client = TestClient(app)
    res = client.get("/api/stats", params={"token": "secret"})
    assert res.status_code == 200
    body: dict[str, Any] = res.json()
    assert body["totals"] == {"parse": 1}
    assert set(body) == {"totals", "today", "last_30d", "daily", "langs", "chart_types"}


# --------------------------------------------------------------------------- #
# 业务端点集成（成功响应才计数）
# --------------------------------------------------------------------------- #

def test_parse_endpoint_tracked(tmp_path: Path) -> None:
    client = TestClient(app)
    res = client.post("/api/parse", json={"text": FIXTURE.read_text(encoding="utf-8")},
                      headers={"X-Lang": "fr", "CF-IPCountry": "de"})
    assert res.status_code == 200
    rows = _rows(tmp_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["event"] == "parse"
    assert row["lang"] == "fr"
    assert row["country"] == "DE"  # 统一大写存储
    assert '"source": "text"' in row["meta"]
    assert '"rows": 6' in row["meta"]  # §12 夹具为 6 行数据


def test_parse_failure_not_tracked(tmp_path: Path) -> None:
    client = TestClient(app)
    res = client.post("/api/parse", json={"text": ""})
    assert res.status_code == 400
    assert _rows(tmp_path) == []


def test_recommend_endpoint_tracked(tmp_path: Path) -> None:
    client = TestClient(app)
    table = client.post("/api/parse", json={"text": FIXTURE.read_text(encoding="utf-8")}).json()
    res = client.post("/api/recommend", json={**table, "lang": "zh"})
    assert res.status_code == 200
    rows = _rows(tmp_path)
    rec = [r for r in rows if r["event"] == "recommend"]
    assert len(rec) == 1
    assert rec[0]["lang"] == "zh"  # 归一化后的生成语言
    assert '"chart_types": [' in rec[0]["meta"]

    stats = analytics.get_stats()
    assert stats["langs"] == {"zh": 1}


def test_generate_pptx_endpoint_tracked(tmp_path: Path) -> None:
    client = TestClient(app)
    res = client.post("/api/generate-pptx", json=BAR_REQUEST, headers={"X-Lang": "en"})
    assert res.status_code == 200
    rows = _rows(tmp_path)
    assert len(rows) == 1 and rows[0]["event"] == "generate-pptx"
    assert '"chart_type": "bar"' in rows[0]["meta"]

    stats = analytics.get_stats()
    assert stats["chart_types"] == {"bar": 1}
