"""M2 语义分析模块测试（SPEC §6 A-2.x + C-3/C-4 核心约束）。

验收基准与 SPEC §5.3「期望输出」逐字段一致（v1.2：percent 为小数形态，
11.2% → 0.112；M4 写入 pptx 时不再换算）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.modules import parse_input

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.md"


@pytest.fixture(scope="module")
def table() -> dict[str, Any]:
    return parse_input(FIXTURE_PATH.read_text(encoding="utf-8"))


def _column(table: dict[str, Any], name: str) -> dict[str, Any]:
    return next(c for c in table["columns"] if c["name"] == name)


def _row(table: dict[str, Any], platform: str) -> list[Any]:
    return next(r for r in table["rows"] if r[0] == platform)


# ---------------------------------------------------------------- A-2.1 期望输出全字段比对


def test_full_expectation(table: dict[str, Any]) -> None:
    """A-2.1：8 列 × 6 行，role/unit/nullable/stats 与 SPEC §5.3 期望输出一致。"""
    assert [c["name"] for c in table["columns"]] == [
        "平台", "2024 MAU", "2025 MAU", "同比", "2024 DAU", "2025 DAU", "梯队", "平台态势",
    ]
    assert len(table["rows"]) == 6
    assert all(len(row) == 8 for row in table["rows"])

    expected_columns = [
        # name, role, unit, nullable, min, max, null_count, distinct_count
        ("平台", "dimension", "text", False, None, None, 0, 6),
        ("2024 MAU", "measure", "yi", False, 3.2, 13.9, 0, 6),
        ("2025 MAU", "measure", "yi", False, 3.5, 14.2, 0, 6),
        ("同比", "percent", "percent", False, -0.039, 0.112, 0, 6),
        ("2024 DAU", "measure", "yi", True, 1.0, 7.0, 2, 4),
        ("2025 DAU", "measure", "yi", True, 1.1, 7.6, 2, 4),
        ("梯队", "dimension", "text", False, None, None, 0, 3),
        ("平台态势", "meta", "text", False, None, None, 0, 5),
    ]
    for col, (name, role, unit, nullable, vmin, vmax, null_count, distinct) in zip(
        table["columns"], expected_columns
    ):
        assert col["name"] == name
        assert col["role"] == role, name
        assert col["unit"] == unit, name
        assert col["nullable"] is nullable, name
        assert col["stats"]["null_count"] == null_count, name
        assert col["stats"]["distinct_count"] == distinct, name
        if vmin is None:
            assert col["stats"]["min"] is None and col["stats"]["max"] is None, name
        else:
            assert col["stats"]["min"] == pytest.approx(vmin), name
            assert col["stats"]["max"] == pytest.approx(vmax), name

    # 数值行全量比对（percent 小数形态；DAU 缺失为 None）
    assert _row(table, "微信") == [
        "微信", 13.9, 14.2, pytest.approx(0.024), None, None, "第二梯队", "稳健",
    ]
    assert _row(table, "抖音") == [
        "抖音", 10.5, 11.7, pytest.approx(0.112), 7.0, 7.6, "第一梯队", "高增长",
    ]
    assert _row(table, "快手")[3] == pytest.approx(-0.028)
    assert _row(table, "微博")[3] == pytest.approx(-0.039)
    assert _row(table, "B站")[3] == pytest.approx(0.088)
    assert _row(table, "小红书")[3] == pytest.approx(0.094)


# ---------------------------------------------------------------- C-4 percent 识别（用户专项）


def test_percent_column_recognition(table: dict[str, Any]) -> None:
    """C-4 / A-2.1：同比列被识别为 percent，+11.2% → 0.112、-3.9% → -0.039。"""
    col = _column(table, "同比")
    assert col["role"] == "percent"
    assert col["unit"] == "percent"
    assert col["nullable"] is False

    values = [row[3] for row in table["rows"]]
    assert values == pytest.approx([0.024, 0.112, -0.028, -0.039, 0.088, 0.094])
    # 负同比保留符号（C-4：-3.9% → -0.039，不是 0.039、不是 None）
    assert _row(table, "微博")[3] == pytest.approx(-0.039)


def test_percent_by_column_header() -> None:
    """列名含 % 时，裸数字单元格同样按百分比解析（SPEC §5.3 role 判定规则）。"""
    result = parse_input("平台,增长率(%)\n微信,11.2\n微博,-3.9\n")
    col = _column(result, "增长率(%)")
    assert col["role"] == "percent"
    assert [row[1] for row in result["rows"]] == pytest.approx([0.112, -0.039])


# ---------------------------------------------------------------- C-3 缺失值（用户专项）


def test_missing_values_are_null_not_zero(table: dict[str, Any]) -> None:
    """C-3 / A-2.1：DAU 全缺失平台（微信、小红书）为 None，不得转为 0；
    DAU 完整平台（抖音等）保留真实数值。"""
    wechat = _row(table, "微信")
    xiaohongshu = _row(table, "小红书")
    assert wechat[4] is None and wechat[5] is None
    assert xiaohongshu[4] is None and xiaohongshu[5] is None

    douyin = _row(table, "抖音")
    assert douyin[4] == 7.0 and douyin[5] == 7.6

    # DAU 两列中不存在任何 0 值（缺失没有被转成 0）
    for row in table["rows"]:
        for idx in (4, 5):
            assert row[idx] is None or row[idx] != 0

    for name in ("2024 DAU", "2025 DAU"):
        col = _column(table, name)
        assert col["nullable"] is True
        assert col["missing_tokens_hit"] == ["未披露"]
        assert col["stats"]["null_count"] == 2


def test_missing_token_wu() -> None:
    """缺失词「无」映射为 None（SPEC §5.0 词表，v1.2 新增）。"""
    result = parse_input("平台,MAU\n微信,13.9亿\n抖音,无\n")
    assert result["rows"][1][1] is None
    col = _column(result, "MAU")
    assert col["nullable"] is True
    assert col["missing_tokens_hit"] == ["无"]


def test_json_serialization_no_nan(table: dict[str, Any]) -> None:
    """A-2.2：序列化为合法 JSON，不存在 NaN/Infinity，缺失为 null。"""
    payload = json.dumps(table, ensure_ascii=False, allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload
    assert '"未披露"' not in json.dumps(table["rows"], ensure_ascii=False)


# ---------------------------------------------------------------- A-2.3 role 判定


def test_role_classification(table: dict[str, Any]) -> None:
    """A-2.3：平台/梯队为 dimension，平台态势为 meta。"""
    assert _column(table, "平台")["role"] == "dimension"
    assert _column(table, "梯队")["role"] == "dimension"
    assert _column(table, "平台态势")["role"] == "meta"


# ---------------------------------------------------------------- A-2.4 混合单位不折算（MVP 已知限制）


def test_mixed_units_not_converted() -> None:
    """A-2.4：同列混合 亿/万 不自动折算——按列主单位 yi，7000万 置 None 并记 warning，
    任何字段不得出现 0.7。"""
    result = parse_input("平台,MAU\n微信,13.9亿\n抖音,7000万\n")

    col = _column(result, "MAU")
    assert col["unit"] == "yi"
    assert result["rows"][0][1] == 13.9
    assert result["rows"][1][1] is None
    assert any("未自动折算" in w for w in col["warnings"])

    payload = json.dumps(result)
    assert "0.7" not in payload
    assert "0.0007" not in payload
