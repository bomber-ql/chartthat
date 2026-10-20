"""M1 数据解析模块测试（SPEC §6 A-1.x）。

夹具：tests/fixtures/sample.md 与 SPEC §12 六行样例一致；
csv/xlsx 由同内容在测试中动态生成（仓库 .gitignore 忽略 *.csv/*.xlsx，不落盘）。
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest

from app.modules import parser
from app.modules.parser import ParseError, parse_bytes, parse_text

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.md"
EXPECTED_HEADER = ["平台", "2024 MAU", "2025 MAU", "同比", "2024 DAU", "2025 DAU", "梯队", "平台态势"]
EXPECTED_FIRST_ROW = ["微信", "13.9亿", "14.2亿", "+2.4%", "未披露", "未披露", "第二梯队", "稳健"]


@pytest.fixture(scope="module")
def sample_md() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sample_rows() -> list[list[str]]:
    """与 sample.md 同内容的二维数据（不含表头），用于生成 csv/xlsx。"""
    return [
        ["微信", "13.9亿", "14.2亿", "+2.4%", "未披露", "未披露", "第二梯队", "稳健"],
        ["抖音", "10.5亿", "11.7亿", "+11.2%", "7.0亿", "7.6亿", "第一梯队", "高增长"],
        ["快手", "7.2亿", "7.0亿", "-2.8%", "4.1亿", "4.0亿", "第二梯队", "轻微下滑"],
        ["微博", "5.9亿", "5.8亿", "-3.9%", "2.6亿", "2.5亿", "第三梯队", "持续下滑"],
        ["B站", "3.4亿", "3.7亿", "+8.8%", "1.0亿", "1.1亿", "第三梯队", "增长"],
        ["小红书", "3.2亿", "3.5亿", "+9.4%", "未披露", "未披露", "第三梯队", "增长"],
    ]


# ---------------------------------------------------------------- A-1.1


def test_parse_markdown_shape(sample_md: str) -> None:
    """A-1.1：样例 Markdown 解析为 8 列 × 6 行，原始字符串保持不切分不规范化。"""
    table = parse_text(sample_md)

    assert table["source"] == "text"
    assert table["columns"] == EXPECTED_HEADER
    assert len(table["rows"]) == 6
    assert all(len(row) == 8 for row in table["rows"])
    # 原始字符串保留（数值规范化是 M2 的职责）
    assert table["rows"][0] == EXPECTED_FIRST_ROW
    assert table["rows"][1][3] == "+11.2%"
    assert table["rows"][3][3] == "-3.9%"
    assert table["rows"][5][4] == "未披露"


def test_parse_tab_and_comma_text(sample_rows: list[list[str]]) -> None:
    """制表符 / 逗号分隔文本嗅探正确，输出一致。"""
    tsv = "\t".join(EXPECTED_HEADER) + "\n" + "\n".join("\t".join(r) for r in sample_rows)
    csv_text = ",".join(EXPECTED_HEADER) + "\n" + "\n".join(",".join(r) for r in sample_rows)

    tsv_table = parse_text(tsv)
    csv_table = parse_text(csv_text)

    assert tsv_table["meta"]["delimiter_detected"] == "\t"
    assert csv_table["meta"]["delimiter_detected"] == ","
    assert tsv_table["columns"] == csv_table["columns"] == EXPECTED_HEADER
    assert tsv_table["rows"] == csv_table["rows"]


# ---------------------------------------------------------------- A-1.2


def test_parse_csv_encodings(sample_md: str, sample_rows: list[list[str]]) -> None:
    """A-1.2：utf-8-sig 与 gbk 两种编码的 CSV 与 Markdown 解析结果一致。"""
    csv_text = ",".join(EXPECTED_HEADER) + "\n" + "\n".join(",".join(r) for r in sample_rows)
    md_table = parse_text(sample_md)

    utf8_table = parse_bytes(csv_text.encode("utf-8-sig"), "sample.csv")
    gbk_table = parse_bytes(csv_text.encode("gbk"), "sample.csv")

    assert utf8_table["source"] == gbk_table["source"] == "csv"
    assert utf8_table["meta"]["encoding"] == "utf-8-sig"
    assert gbk_table["meta"]["encoding"] == "gbk"
    for table in (utf8_table, gbk_table):
        assert table["columns"] == md_table["columns"]
        assert table["rows"] == md_table["rows"]


def test_parse_xlsx(sample_md: str, sample_rows: list[list[str]]) -> None:
    """A-1.2：xlsx 上传与 Markdown 解析结果一致，sheet_name 正确返回。"""
    buf = io.BytesIO()
    pd.DataFrame(sample_rows, columns=EXPECTED_HEADER).to_excel(buf, index=False, sheet_name="数据")

    table = parse_bytes(buf.getvalue(), "sample.xlsx")

    assert table["source"] == "xlsx"
    assert table["sheet_name"] == "数据"
    md_table = parse_text(sample_md)
    assert table["columns"] == md_table["columns"]
    assert table["rows"] == md_table["rows"]


def test_parse_xlsx_missing_sheet(sample_rows: list[list[str]]) -> None:
    buf = io.BytesIO()
    pd.DataFrame(sample_rows, columns=EXPECTED_HEADER).to_excel(buf, index=False)

    with pytest.raises(ParseError) as exc_info:
        parse_bytes(buf.getvalue(), "sample.xlsx", sheet_name="不存在")
    assert exc_info.value.code == "PARSE_EMPTY"


# ---------------------------------------------------------------- A-1.3


def test_ragged_rows_padded_and_truncated() -> None:
    """A-1.3：字段不足补 null、字段过多截断，均记 warning 且不抛异常。"""
    text = "平台,MAU,同比\n微信,13.9亿\n抖音,10.5亿,+11.2%,多余字段\n"

    table = parse_text(text)

    assert table["rows"][0] == ["微信", "13.9亿", None]
    assert table["rows"][1] == ["抖音", "10.5亿", "+11.2%"]
    warnings = table["meta"]["warnings"]
    assert any("补 null" in w for w in warnings)
    assert any("截断" in w for w in warnings)


def test_empty_input() -> None:
    """A-1.3：全空输入与仅表头输入均返回 PARSE_EMPTY。"""
    with pytest.raises(ParseError) as exc_info:
        parse_text("   \n  \n")
    assert exc_info.value.code == "PARSE_EMPTY"

    with pytest.raises(ParseError) as exc_info:
        parse_text("平台,MAU,同比")
    assert exc_info.value.code == "PARSE_EMPTY"


def test_unsupported_file_type() -> None:
    with pytest.raises(ParseError) as exc_info:
        parse_bytes(b"%PDF-1.4 fake", "report.pdf")
    assert exc_info.value.code == "PARSE_UNSUPPORTED"


def test_too_large(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(parser, "MAX_UPLOAD_BYTES", 16)
    with pytest.raises(ParseError) as exc_info:
        parse_bytes(b"a,b,c,d,e,f,g,h,i,j", "sample.csv")
    assert exc_info.value.code == "PARSE_TOO_LARGE"


def test_too_many_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(parser, "MAX_DATA_ROWS", 2)
    text = "平台,MAU\n微信,13.9亿\n抖音,10.5亿\n快手,7.2亿\n"
    with pytest.raises(ParseError) as exc_info:
        parse_text(text)
    assert exc_info.value.code == "PARSE_TOO_LARGE"
