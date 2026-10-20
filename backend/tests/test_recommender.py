"""M3 recommender 测试（SPEC §6 M3 验收 A-3.1 ~ A-3.6）。

LLM 一律 mock（不发真实网络请求）：通过向 recommend_charts 注入 llm_call 实现。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.modules import parse_input
from app.modules.recommender import (
    INCOMPLETE_NOTE,
    RecommendationError,
    parse_llm_json,
    recommend_charts,
)
from app.validators import validate_chart_spec

FIXTURE = Path(__file__).parent / "fixtures" / "sample.md"
LLM_ITEMS: list[dict[str, Any]] = []  # 测试内动态构造


@pytest.fixture(scope="module")
def table() -> dict[str, Any]:
    return parse_input(FIXTURE.read_text(encoding="utf-8"))


def _combo_item(with_dau: bool = False) -> dict[str, Any]:
    series = [
        {"column": "2024 MAU", "kind": "bar"},
        {"column": "2025 MAU", "kind": "bar"},
        {"column": "同比", "kind": "line"},
    ]
    if with_dau:
        series.append({"column": "2024 DAU", "kind": "bar"})
    return {
        "chart_type": "combo",
        "title": "各平台 MAU 规模与同比增速",
        "reasoning": "体量与增速双轴呈现",
        "config": {"dimension": "平台", "semantic_layer": "rate", "series": series},
    }


def _bar_item() -> dict[str, Any]:
    return {
        "chart_type": "bar",
        "title": "2025 MAU 体量对比",
        "reasoning": "柱图对比各平台体量",
        "config": {"dimension": "平台", "semantic_layer": "comparison",
                   "series": [{"column": "2025 MAU"}]},
    }


# --------------------------------------------------------------------------- #
# parse_llm_json 容错
# --------------------------------------------------------------------------- #

def test_parse_plain_array() -> None:
    items = parse_llm_json('[{"chart_type":"bar","title":"t","reasoning":"r",'
                           '"config":{"dimension":"d","series":[{"column":"c"}]}}]')
    assert len(items) == 1 and items[0]["chart_type"] == "bar"


def test_parse_strips_markdown_fence() -> None:
    raw = "```json\n[{\"chart_type\": \"bar\", \"title\": \"t\", \"reasoning\": \"r\"," \
          " \"config\": {\"dimension\": \"d\", \"series\": [{\"column\": \"c\"}]}}]\n```"
    assert len(parse_llm_json(raw)) == 1


def test_parse_wrapped_recommendations() -> None:
    raw = '{"recommendations": [{"chart_type":"bar","title":"t","reasoning":"r",' \
          '"config":{"dimension":"d","series":[{"column":"c"}]}}]}'
    assert len(parse_llm_json(raw)) == 1


@pytest.mark.parametrize("bad", ["not json at all", "{}", "[1, 2]", '{"a": 1}'])
def test_parse_invalid_raises(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_llm_json(bad)


# --------------------------------------------------------------------------- #
# A-3.1：合法裸数组 → ChartSpec 全过 V-1~V-8
# --------------------------------------------------------------------------- #

def test_valid_llm_output_passes_validators(table: dict[str, Any]) -> None:
    import json

    def llm(_messages: list[dict[str, str]]) -> str:
        return json.dumps([_combo_item(), _bar_item()], ensure_ascii=False)

    result = recommend_charts(table, llm_call=llm)
    assert result["degraded"] is False
    specs = result["recommendations"]
    assert len(specs) >= 2
    for spec in specs:
        assert validate_chart_spec(spec, table) == []
        assert spec["chart_type"] in {"bar", "line", "combo", "slope", "scatter", "pie"}
        assert spec["reasoning"]


# --------------------------------------------------------------------------- #
# A-3.2：首次非 JSON、二次合法 → 恰好 2 次调用
# --------------------------------------------------------------------------- #

def test_retry_once_then_success(table: dict[str, Any]) -> None:
    import json

    calls: list[list[dict[str, str]]] = []

    def llm(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        if len(calls) == 1:
            return "抱歉，我无法理解"  # 非 JSON
        return json.dumps([_bar_item()], ensure_ascii=False)

    result = recommend_charts(table, llm_call=llm)
    assert len(calls) == 2
    assert result["degraded"] is False
    assert result["recommendations"][0]["chart_type"] == "bar"


def test_invalid_entries_are_dropped(table: dict[str, Any]) -> None:
    import json

    bad_type = {**_bar_item(), "chart_type": "radar"}
    missing_col = {
        "chart_type": "bar",
        "title": "x",
        "reasoning": "r",
        "config": {"dimension": "平台", "series": [{"column": "不存在的列"}]},
    }

    def llm(_m: list[dict[str, str]]) -> str:
        return json.dumps([bad_type, missing_col, _bar_item()], ensure_ascii=False)

    result = recommend_charts(table, llm_call=llm)
    types = [s["chart_type"] for s in result["recommendations"]]
    assert "radar" not in types
    assert "bar" in types


# --------------------------------------------------------------------------- #
# A-3.3：LLM 持续失败 → 降级且覆盖三语义层
# --------------------------------------------------------------------------- #

def test_fallback_covers_three_layers(table: dict[str, Any]) -> None:
    def llm(_m: list[dict[str, str]]) -> str:
        raise RuntimeError("llm down")

    result = recommend_charts(table, llm_call=llm)
    assert result["degraded"] is True
    specs = result["recommendations"]
    layers = {s["semantic_layer"] for s in specs}
    assert {"trend", "comparison", "rate"} <= layers
    combo = next(s for s in specs if s["chart_type"] == "combo")
    pct = next(s for s in combo["series"] if s["source_column"] == "同比")
    assert pct["axis"] == "secondary" and pct["kind"] == "line"
    # 面积图序列 kind 恒为 line（v1.8 修复：降级路径曾误置 bar，前端渲染成柱状图）
    area = next(s for s in specs if s["chart_type"] == "area")
    assert all(s["kind"] == "line" for s in area["series"])
    for spec in specs:
        assert validate_chart_spec(spec, table) == []


def test_no_numeric_columns_raises() -> None:
    t = {
        "columns": [
            {"name": "城市", "role": "dimension", "unit": "text", "nullable": False,
             "missing_tokens_hit": [], "warnings": [], "stats": {"null_count": 0, "distinct_count": 2}},
            {"name": "备注", "role": "meta", "unit": "text", "nullable": False,
             "missing_tokens_hit": [], "warnings": [], "stats": {"null_count": 0, "distinct_count": 2}},
        ],
        "rows": [["北京", "晴"], ["上海", "雨"]],
    }

    def llm(_m: list[dict[str, str]]) -> str:
        raise RuntimeError("down")

    with pytest.raises(RecommendationError):
        recommend_charts(t, llm_call=llm)


# --------------------------------------------------------------------------- #
# A-3.4：percent 强制副轴 line；null 保留；小数形态
# --------------------------------------------------------------------------- #

def test_percent_axis_and_decimal_form(table: dict[str, Any]) -> None:
    import json

    def llm(_m: list[dict[str, str]]) -> str:
        # 故意把 percent 说成主轴 bar，后端必须强制纠正
        item = {
            "chart_type": "combo",
            "title": "t",
            "reasoning": "r",
            "config": {"dimension": "平台", "series": [
                {"column": "2025 MAU", "kind": "bar", "axis": "primary"},
                {"column": "同比", "kind": "bar", "axis": "primary"},  # 违规
            ]},
        }
        return json.dumps([item], ensure_ascii=False)

    spec = recommend_charts(table, llm_call=llm)["recommendations"][0]
    pct = next(s for s in spec["series"] if s["source_column"] == "同比")
    assert pct["axis"] == "secondary" and pct["kind"] == "line"
    assert pct["data"][:3] == [pytest.approx(0.024), pytest.approx(0.112), pytest.approx(-0.028)]
    assert all(abs(v) < 1 for v in pct["data"] if v is not None)  # 小数形态，不出现 11.2


# --------------------------------------------------------------------------- #
# A-3.5：LLM 伪造数据无效，data 全部来自投影
# --------------------------------------------------------------------------- #

def test_llm_data_is_ignored(table: dict[str, Any]) -> None:
    import json

    def llm(_m: list[dict[str, str]]) -> str:
        item = _bar_item()
        item["config"]["series"][0]["data"] = [999.0] * 6  # 伪造数据
        item["data"] = [1, 2, 3]
        return json.dumps([item], ensure_ascii=False)

    spec = recommend_charts(table, llm_call=llm)["recommendations"][0]
    # 2025 MAU：微信 14.2、抖音 11.7、快手 7.0、微博 5.7、B站 3.7、小红书 3.5（SPEC §5.3）
    assert spec["series"][0]["data"] == [14.2, 11.7, 7.0, 5.7, 3.7, 3.5]
    assert 999.0 not in spec["series"][0]["data"]


# --------------------------------------------------------------------------- #
# A-3.6：含 null 系列被确定性标注，null 不转 0；已有提示不重复
# --------------------------------------------------------------------------- #

def test_incomplete_series_annotation(table: dict[str, Any]) -> None:
    import json

    def llm(_m: list[dict[str, str]]) -> str:
        return json.dumps([_combo_item(with_dau=True)], ensure_ascii=False)

    spec = recommend_charts(table, llm_call=llm)["recommendations"][0]
    dau = next(s for s in spec["series"] if s["source_column"] == "2024 DAU")
    assert dau["data"][0] is None and dau["data"][5] is None  # 微信/小红书
    assert dau["data"][1] == 7.0                              # 抖音完整
    assert 0 not in dau["data"]                               # 禁止 0 顶替
    assert INCOMPLETE_NOTE in spec["reasoning"]
    assert "2024 DAU" in spec["reasoning"]


def test_annotation_not_duplicated(table: dict[str, Any]) -> None:
    import json

    def llm(_m: list[dict[str, str]]) -> str:
        item = _combo_item(with_dau=True)
        item["reasoning"] = f"DAU 缺失较多，{INCOMPLETE_NOTE}"
        return json.dumps([item], ensure_ascii=False)

    spec = recommend_charts(table, llm_call=llm)["recommendations"][0]
    assert spec["reasoning"].count(INCOMPLETE_NOTE) == 1
