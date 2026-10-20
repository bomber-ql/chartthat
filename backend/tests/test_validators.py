"""ChartSpec 不变式校验测试（SPEC §5.4，v1.6 新增 V-9 ~ V-12 与 percent 口径）。

直接构造最小 SemanticTable / ChartSpec dict，不走解析管线。
"""
from __future__ import annotations

from typing import Any

from app.validators import validate_chart_spec

# 最小 SemanticTable：dimension + 三个同单位 measure + 异单位 measure + percent
_COLUMNS = [
    {"name": "平台", "role": "dimension", "unit": "count"},
    {"name": "2023 MAU", "role": "measure", "unit": "yi"},
    {"name": "2024 MAU", "role": "measure", "unit": "yi"},
    {"name": "2025 MAU", "role": "measure", "unit": "yi"},
    {"name": "规模万", "role": "measure", "unit": "wan"},
    {"name": "同比", "role": "percent", "unit": "percent"},
]
TABLE: dict[str, Any] = {"columns": _COLUMNS, "rows": []}
_UNIT = {c["name"]: c["unit"] for c in _COLUMNS}


def _series(col: str, data: list[float | None], kind: str = "bar") -> dict[str, Any]:
    return {"source_column": col, "unit": _UNIT[col], "axis": "primary", "kind": kind, "data": data}


def _spec(chart_type: str, series: list[dict[str, Any]], n_cat: int = 3) -> dict[str, Any]:
    primary_unit = series[0]["unit"]
    return {
        "chart_type": chart_type,
        "title": "测试图表",
        "categories": [f"c{i}" for i in range(n_cat)],
        "series": series,
        "axes": {"primary": {"unit": primary_unit}},
    }


def _errors(chart_type: str, series: list[dict[str, Any]]) -> list[str]:
    return validate_chart_spec(_spec(chart_type, series), TABLE)


# ---------- V-9：stacked ≥2 个同单位 measure 序列（非 percent） ----------

def test_stacked_valid() -> None:
    errs = _errors("stacked", [_series("2024 MAU", [1.0, 2.0, 3.0]), _series("2025 MAU", [2.0, 3.0, 4.0])])
    assert errs == []


def test_stacked_rejects_single_series() -> None:
    errs = _errors("stacked", [_series("2025 MAU", [1.0, 2.0, 3.0])])
    assert any("V-9" in e for e in errs)


def test_stacked_rejects_mixed_units() -> None:
    errs = _errors("stacked", [_series("2025 MAU", [1.0, 2.0, 3.0]), _series("规模万", [10.0, 20.0, 30.0])])
    assert any("V-9" in e for e in errs)


def test_stacked_rejects_percent() -> None:
    errs = _errors("stacked", [_series("同比", [0.1, 0.2, 0.3]), _series("同比", [0.1, 0.2, 0.3])])
    assert errs  # V-9 同单位检查 + 新类型 percent 口径双重拦截


# ---------- V-10：waterfall 恰好 1 个 measure 序列（非 percent） ----------

def test_waterfall_valid() -> None:
    assert _errors("waterfall", [_series("2025 MAU", [10.0, -3.0, 1.0])]) == []


def test_waterfall_rejects_two_series() -> None:
    errs = _errors("waterfall", [_series("2024 MAU", [1.0, 2.0, 3.0]), _series("2025 MAU", [2.0, 3.0, 4.0])])
    assert any("V-10" in e for e in errs)


def test_waterfall_rejects_percent() -> None:
    errs = _errors("waterfall", [_series("同比", [0.1, 0.2, 0.3])])
    assert errs


# ---------- V-11：radar ≥3 个同单位 measure 序列（非 percent） ----------

def test_radar_valid() -> None:
    series = [_series(c, [1.0, 2.0, 3.0], kind="line") for c in ("2023 MAU", "2024 MAU", "2025 MAU")]
    assert _errors("radar", series) == []


def test_radar_rejects_less_than_three() -> None:
    series = [_series("2024 MAU", [1.0, 2.0, 3.0]), _series("2025 MAU", [2.0, 3.0, 4.0])]
    errs = _errors("radar", series)
    assert any("V-11" in e for e in errs)


def test_radar_rejects_mixed_units() -> None:
    series = [_series("2023 MAU", [1.0, 2.0, 3.0]), _series("2024 MAU", [1.0, 2.0, 3.0]),
              _series("规模万", [10.0, 20.0, 30.0])]
    errs = _errors("radar", series)
    assert any("V-11" in e for e in errs)


def test_radar_rejects_percent() -> None:
    series = [_series("同比", [0.1, 0.2, 0.3])] * 3
    errs = _errors("radar", series)
    assert errs


# ---------- V-12：donut / sunburst 同 V-8 pie 口径（恰好 1 个 measure 序列） ----------

def test_donut_and_sunburst_valid() -> None:
    for t in ("donut", "sunburst"):
        assert _errors(t, [_series("2025 MAU", [1.0, 2.0, 3.0])]) == []


def test_donut_rejects_two_series() -> None:
    errs = _errors("donut", [_series("2024 MAU", [1.0, 2.0, 3.0]), _series("2025 MAU", [2.0, 3.0, 4.0])])
    assert any("V-12" in e for e in errs)


def test_sunburst_rejects_two_series() -> None:
    errs = _errors("sunburst", [_series("2024 MAU", [1.0, 2.0, 3.0]), _series("2025 MAU", [2.0, 3.0, 4.0])])
    assert any("V-12" in e for e in errs)


def test_donut_rejects_percent() -> None:
    errs = _errors("donut", [_series("同比", [0.1, 0.2, 0.3])])
    assert errs


# ---------- 新类型 percent 口径：仅 bar / hbar / line / area / combo 允许 ----------

def test_hbar_and_area_allow_percent() -> None:
    for t in ("bar", "hbar", "line", "area"):
        assert _errors(t, [_series("同比", [0.1, 0.2, 0.3])]) == [], f"{t} 应允许纯 percent 序列"


def test_unknown_chart_type_still_rejected() -> None:
    errs = _errors("funnel", [_series("2025 MAU", [1.0, 2.0, 3.0])])
    assert any("V-2" in e for e in errs)
