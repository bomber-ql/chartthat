"""M1 数据解析模块（SPEC §6 M1）。

职责：把文本粘贴 / CSV / Excel 三种来源的输入规整为 RawTable（SPEC §5.2）。
只做「切分」，不做数值规范化——语义识别（percent/单位/缺失值）在 M2 semantic.py。

实现说明：
- 文本/CSV 路径使用标准库 csv 逐行读取，以精准实现 SPEC 的「不足补 null、
  超长截断并记 warning」规则（pandas read_csv 无法区分这两类坏行）；
- Excel 路径使用 pandas + openpyxl；
- Markdown 表格先预处理为 TSV 再走统一文本路径。
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any

import pandas as pd

# ---- 错误（错误码对齐 SPEC §11） ----


class ParseError(Exception):
    """数据解析错误。code 取值见 SPEC §11：PARSE_EMPTY / PARSE_TOO_LARGE / PARSE_UNSUPPORTED。"""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DATA_ROWS = 10_000

_MD_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|?)+\s*$")
_DELIMITER_CANDIDATES = ("\t", ",", ";", "|")
_EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xls"}
_CSV_SUFFIXES = {".csv", ".tsv", ".txt"}

RawTable = dict[str, Any]


# ---------------------------------------------------------------- 文本路径


def _split_nonempty_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line for line in normalized.split("\n") if line.strip() != ""]


def _is_markdown_table(lines: list[str]) -> bool:
    return (
        len(lines) >= 2
        and lines[0].lstrip().startswith("|")
        and bool(_MD_SEPARATOR_RE.match(lines[1]))
    )


def _markdown_to_tsv(lines: list[str]) -> list[str]:
    """Markdown 表格行 → TSV 行（去 | 边框、跳过 |---| 分隔行）。"""
    out: list[str] = []
    for idx, line in enumerate(lines):
        if idx >= 1 and _MD_SEPARATOR_RE.match(line):
            continue
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        cells = [cell.strip().replace("\t", " ") for cell in stripped.split("|")]
        out.append("\t".join(cells))
    return out


def _sniff_delimiter(header_line: str) -> str:
    """按表头行中各候选分隔符出现次数嗅探；均无则按单列（返回逗号占位）。"""
    counts = {d: header_line.count(d) for d in _DELIMITER_CANDIDATES}
    best = max(counts, key=lambda d: counts[d])
    return best if counts[best] > 0 else ","


def _build_raw_table(
    header: list[str],
    data_rows: list[list[str | None]],
    *,
    source: str,
    sheet_name: str | None,
    delimiter: str | None,
    encoding: str | None,
    warnings: list[str],
    truncated_rows: int,
) -> RawTable:
    if not data_rows:
        raise ParseError("PARSE_EMPTY", "表格只有表头，没有数据行")
    if len(data_rows) > MAX_DATA_ROWS:
        raise ParseError(
            "PARSE_TOO_LARGE",
            f"数据行数 {len(data_rows)} 超过上限 {MAX_DATA_ROWS}",
            {"rows": len(data_rows), "max_rows": MAX_DATA_ROWS},
        )
    return {
        "source": source,
        "sheet_name": sheet_name,
        "columns": header,
        "rows": data_rows,
        "meta": {
            "delimiter_detected": delimiter,
            "encoding": encoding,
            "dropped_rows": 0,
            "warnings": warnings + ([f"{truncated_rows} 行字段数多于表头，已截断"] if truncated_rows else []),
        },
    }


def _normalize_header(raw_header: list[str], warnings: list[str]) -> list[str]:
    header: list[str] = []
    for idx, name in enumerate(raw_header):
        clean = name.strip()
        if not clean:
            clean = f"col_{idx + 1}"
            warnings.append(f"第 {idx + 1} 列表头为空，已命名为 {clean}")
        header.append(clean)
    return header


def _normalize_rows(
    raw_rows: list[list[str]],
    ncols: int,
    warnings: list[str],
) -> tuple[list[list[str | None]], int]:
    """不足补 None、超长截断（SPEC §6 M1）。返回 (rows, truncated_count)。"""
    rows: list[list[str | None]] = []
    truncated = 0
    padded = 0
    for raw in raw_rows:
        cells: list[str | None] = [c.strip() for c in raw]
        if len(cells) < ncols:
            cells = cells + [None] * (ncols - len(cells))
            padded += 1
        elif len(cells) > ncols:
            cells = cells[:ncols]
            truncated += 1
        rows.append(cells)
    if padded:
        warnings.append(f"{padded} 行字段数不足表头，已补 null")
    return rows, truncated


def parse_text(raw_text: str) -> RawTable:
    """M1 入口（文本粘贴）：Markdown 表格 / 制表符 / 逗号 / 分号分隔文本 → RawTable。"""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ParseError("PARSE_EMPTY", "输入为空，无法识别表格")

    lines = _split_nonempty_lines(raw_text)
    if not lines:
        raise ParseError("PARSE_EMPTY", "输入为空，无法识别表格")

    warnings: list[str] = []
    if _is_markdown_table(lines):
        lines = _markdown_to_tsv(lines)
        delimiter: str | None = "\t"
    else:
        delimiter = _sniff_delimiter(lines[0])

    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    raw_rows = [row for row in reader if any(cell.strip() for cell in row)]
    if len(raw_rows) < 2:
        raise ParseError("PARSE_EMPTY", "无法识别出包含表头与数据行的表格")

    header = _normalize_header(raw_rows[0], warnings)
    rows, truncated = _normalize_rows(raw_rows[1:], len(header), warnings)
    return _build_raw_table(
        header,
        rows,
        source="text",
        sheet_name=None,
        delimiter=delimiter,
        encoding=None,
        warnings=warnings,
        truncated_rows=truncated,
    )


# ---------------------------------------------------------------- 文件路径


def _decode_csv_bytes(data: bytes) -> tuple[str, str]:
    """按 utf-8-sig → gbk 顺序回退解码（SPEC §6 M1）。返回 (text, encoding)。"""
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ParseError("PARSE_UNSUPPORTED", "无法识别文件编码（仅支持 UTF-8 / GBK）")


def _parse_csv_bytes(data: bytes) -> RawTable:
    text, encoding = _decode_csv_bytes(data)
    table = parse_text(text)
    table["source"] = "csv"
    table["meta"]["encoding"] = encoding
    return table


def _parse_excel_bytes(data: bytes, sheet_name: str | None) -> RawTable:
    warnings: list[str] = []
    try:
        book = pd.ExcelFile(io.BytesIO(data), engine="openpyxl")
    except Exception as exc:  # noqa: BLE001 - 统一转为契约错误
        raise ParseError("PARSE_UNSUPPORTED", f"无法读取 Excel 文件：{exc}") from exc

    if not book.sheet_names:
        raise ParseError("PARSE_EMPTY", "Excel 中没有任何工作表")

    actual_sheet = sheet_name or book.sheet_names[0]
    if actual_sheet not in book.sheet_names:
        raise ParseError(
            "PARSE_EMPTY",
            f"工作表 {actual_sheet!r} 不存在，可用工作表：{book.sheet_names}",
            {"sheet_names": book.sheet_names},
        )

    df = book.parse(sheet_name=actual_sheet, dtype=str, keep_default_na=False)
    if df.shape[1] == 0:
        raise ParseError("PARSE_EMPTY", f"工作表 {actual_sheet!r} 为空")

    header = _normalize_header([str(c) for c in df.columns], warnings)
    raw_rows = [["" if pd.isna(v) else str(v) for v in row] for row in df.values.tolist()]
    raw_rows = [row for row in raw_rows if any(cell.strip() for cell in row)]
    rows, truncated = _normalize_rows(raw_rows, len(header), warnings)
    return _build_raw_table(
        header,
        rows,
        source="xlsx",
        sheet_name=actual_sheet,
        delimiter=None,
        encoding=None,
        warnings=warnings,
        truncated_rows=truncated,
    )


def parse_bytes(data: bytes, filename: str, sheet_name: str | None = None) -> RawTable:
    """M1 入口（文件上传）：按扩展名分发 CSV / Excel。"""
    if not data:
        raise ParseError("PARSE_EMPTY", "上传文件为空")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ParseError(
            "PARSE_TOO_LARGE",
            f"文件大小 {len(data)} 字节超过上限 {MAX_UPLOAD_BYTES} 字节（10MB）",
            {"bytes": len(data), "max_bytes": MAX_UPLOAD_BYTES},
        )

    suffix = Path(filename or "").suffix.lower()
    if suffix in _EXCEL_SUFFIXES:
        return _parse_excel_bytes(data, sheet_name)
    if suffix in _CSV_SUFFIXES or not suffix:
        return _parse_csv_bytes(data)
    raise ParseError(
        "PARSE_UNSUPPORTED",
        f"不支持的文件类型 {suffix!r}，仅支持 .csv/.tsv/.txt/.xlsx/.xlsm/.xls",
        {"suffix": suffix},
    )
