"""M2 语义分析模块（SPEC §6 M2）。

职责：RawTable → SemanticTable（SPEC §5.3）。执行 §5.0 全部规范化规则：
- 缺失标记词表 → None（C-3，仅数值类列生效，维度列保留原字符串）；
- percent 判定（列名含 % 或 ≥60% 非空单元格带 % 后缀），值 = 数值部分 ÷ 100（§5.1 小数形态，
  全链路唯一转换点）；
- 中文单位（亿/万）换算为数值，unit 记录原始单位（yi/wan/count），保留显示量级；
- 混合单位不自动折算：异类单元格置 None 并记列级 warnings（MVP 已知限制）；
- NaN/inf 出口强制清洗为 None。
"""
from __future__ import annotations

import math
import re
from typing import Any

# SPEC §5.0 默认缺失标记词表（允许扩展；空串命中不计入 missing_tokens_hit）
MISSING_TOKENS: tuple[str, ...] = (
    "未披露",
    "未公布",
    "暂无",
    "无",
    "—",
    "--",
    "-",
    "N/A",
    "n/a",
    "NA",
    "null",
    "",
)

_NUMERIC_RE = re.compile(r"^([+-]?\d+(?:\.\d+)?)\s*(亿|万|%)?$")
_SUFFIX_TO_UNIT = {"亿": "yi", "万": "wan"}
_MIN_PATTERN_RATIO = 0.6
_DIMENSION_MAX_LEN = 20
_DIMENSION_MAX_DISTINCT_RATIO = 0.8
_PERCENT_DECIMALS = 10

SemanticTable = dict[str, Any]


def _match_numeric(cell: str) -> tuple[float, str | None] | None:
    """匹配 `数值 + 可选单位后缀`。返回 (value, suffix)，不匹配返回 None。"""
    match = _NUMERIC_RE.match(cell)
    if not match:
        return None
    return float(match.group(1)), match.group(2)


def _clean_number(value: float) -> float | None:
    """NaN/inf → None（SPEC §5.0 出口强制清洗）；其余做 round 避免浮点尾巴。"""
    if math.isnan(value) or math.isinf(value):
        return None
    return round(value, _PERCENT_DECIMALS)


def _analyze_column(
    name: str,
    raw_cells: list[str | None],
    *,
    is_first_column: bool,
) -> tuple[dict[str, Any], list[Any]]:
    """分析单列。返回 (column_meta, parsed_values)。"""
    warnings: list[str] = []
    missing_hits: list[str] = []

    # 1) 缺失标记 → None（词表命中；空串命中不记录 token）
    nonempty: list[str] = []
    missing_mask: list[bool] = []
    for cell in raw_cells:
        if cell is None:
            missing_mask.append(True)
            continue
        stripped = cell.strip()
        if stripped in MISSING_TOKENS:
            missing_mask.append(True)
            if stripped and stripped not in missing_hits:
                missing_hits.append(stripped)
        else:
            missing_mask.append(False)
            nonempty.append(stripped)

    null_count = sum(missing_mask)

    # 2) 数值匹配统计
    matched: list[tuple[int, float, str | None]] = []  # (行号, 数值, 后缀)
    for idx, cell in enumerate(raw_cells):
        if missing_mask[idx]:
            continue
        result = _match_numeric(cell.strip())  # type: ignore[union-attr]
        if result is not None:
            matched.append((idx, result[0], result[1]))

    nonempty_count = len(nonempty)
    match_ratio = (len(matched) / nonempty_count) if nonempty_count else 0.0
    percent_hit_count = sum(1 for _, _, suffix in matched if suffix == "%")
    percent_ratio = (percent_hit_count / nonempty_count) if nonempty_count else 0.0

    # 3) role 判定
    is_percent = ("%" in name) or (percent_ratio >= _MIN_PATTERN_RATIO)
    is_numeric_column = match_ratio >= _MIN_PATTERN_RATIO

    parsed: list[Any] = [None] * len(raw_cells)

    if is_percent and is_numeric_column:
        role, unit = "percent", "percent"
        values: list[float] = []
        for idx, value, _suffix in matched:
            converted = _clean_number(value / 100)
            parsed[idx] = converted
            if converted is not None:
                values.append(converted)
        unparseable = nonempty_count - len(matched)
        if unparseable:
            warnings.append(f'列 "{name}" 有 {unparseable} 个非空单元格无法解析为数值，已置空')
            null_count += unparseable
    elif is_numeric_column:
        role = "measure"
        # 列主单位：按后缀占比最高；裸数值视为与列主单位一致（SPEC §5.0）
        suffix_counts = {"亿": 0, "万": 0, None: 0}
        for _, _, suffix in matched:
            suffix_counts[suffix] += 1
        dominant_suffix = max(suffix_counts, key=lambda s: suffix_counts[s])
        unit = _SUFFIX_TO_UNIT.get(dominant_suffix, "count")

        values = []
        for idx, value, suffix in matched:
            if suffix in (dominant_suffix, None):
                cleaned = _clean_number(value)
                parsed[idx] = cleaned
                if cleaned is not None:
                    values.append(cleaned)
            else:
                raw_cell = (raw_cells[idx] or "").strip()
                warnings.append(
                    f'列 "{name}" 主单位为 {unit}，单元格 "{raw_cell}" 未自动折算，已置空'
                )
                null_count += 1
        unparseable = nonempty_count - len(matched)
        if unparseable:
            warnings.append(f'列 "{name}" 有 {unparseable} 个非空单元格无法解析为数值，已置空')
            null_count += unparseable
    else:
        # 文本列：短且低基数 → dimension，否则 meta；首列强制 dimension
        unit = "text"
        distinct_text = set(nonempty)
        max_len = max((len(s) for s in nonempty), default=0)
        distinct_ratio = (len(distinct_text) / nonempty_count) if nonempty_count else 0.0
        if is_first_column or (
            nonempty_count > 0
            and distinct_ratio <= _DIMENSION_MAX_DISTINCT_RATIO
            and max_len <= _DIMENSION_MAX_LEN
        ):
            role = "dimension"
        else:
            role = "meta"
        values = []
        for idx, cell in enumerate(raw_cells):
            if not missing_mask[idx] and cell is not None:
                parsed[idx] = cell.strip()

    distinct_values = {v for v in parsed if v is not None}
    column_meta: dict[str, Any] = {
        "name": name,
        "role": role,
        "unit": unit,
        "nullable": null_count > 0,
        "missing_tokens_hit": missing_hits,
        "warnings": warnings,
        "stats": {
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "null_count": null_count,
            "distinct_count": len(distinct_values),
        },
    }
    return column_meta, parsed


def analyze_table(raw: dict[str, Any]) -> SemanticTable:
    """M2 主入口：RawTable（SPEC §5.2）→ SemanticTable（SPEC §5.3）。"""
    columns: list[str] = raw["columns"]
    raw_rows: list[list[str | None]] = raw["rows"]

    column_metas: list[dict[str, Any]] = []
    parsed_columns: list[list[Any]] = []
    for col_idx, name in enumerate(columns):
        raw_cells = [row[col_idx] if col_idx < len(row) else None for row in raw_rows]
        meta, parsed = _analyze_column(name, raw_cells, is_first_column=(col_idx == 0))
        column_metas.append(meta)
        parsed_columns.append(parsed)

    # 按行重组：rows[i][j] 为第 j 列在第 i 行的解析值
    rows: list[list[Any]] = [
        [parsed_columns[col_idx][row_idx] for col_idx in range(len(columns))]
        for row_idx in range(len(raw_rows))
    ]

    return {"columns": column_metas, "rows": rows}
