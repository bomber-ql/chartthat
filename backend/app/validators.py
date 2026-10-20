"""ChartSpec 不变式校验（SPEC §5.4 V-1 ~ V-8）。

M3 投影后、M4 入口处均调用 validate_chart_spec；返回错误字符串列表，
空列表表示通过。校验基于投影后的 ChartSpec 与其来源 SemanticTable。
"""

from __future__ import annotations

from typing import Any

CHART_TYPES = {"bar", "line", "combo", "slope", "scatter", "pie"}
SERIES_KINDS = {"line", "bar", "scatter"}
AXES = {"primary", "secondary"}
NUMERIC_UNITS = {"count", "yi", "wan", "percent"}


def _column_index(table: dict[str, Any], name: str) -> int | None:
    for i, col in enumerate(table.get("columns", [])):
        if col.get("name") == name:
            return i
    return None


def validate_chart_spec(spec: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """返回错误列表；为空表示 ChartSpec 合法。"""
    errors: list[str] = []

    chart_type = spec.get("chart_type")
    if chart_type not in CHART_TYPES:
        errors.append(f"V-2: 未知 chart_type={chart_type!r}，仅允许 {sorted(CHART_TYPES)}")
        return errors  # 类型未知时后续校验无意义

    title = spec.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title 必须为非空字符串")

    categories = spec.get("categories")
    series = spec.get("series")
    if not isinstance(categories, list) or not categories:
        errors.append("categories 必须为非空数组")
        categories = []
    if not isinstance(series, list) or not series:
        errors.append("series 必须为非空数组")
        return errors

    n_cat = len(categories)
    seen_columns: dict[str, dict[str, Any]] = {}

    for idx, s in enumerate(series):
        prefix = f"series[{idx}]({s.get('source_column', '?')})"
        col_name = s.get("source_column")
        col_idx = _column_index(table, col_name) if isinstance(col_name, str) else None
        if col_idx is None:
            errors.append(f"V-5: {prefix} 的 source_column={col_name!r} 在 SemanticTable 中不存在")
            continue
        src_col = table["columns"][col_idx]
        seen_columns[col_name] = src_col

        if src_col.get("role") not in ("measure", "percent"):
            errors.append(f"V-5: {prefix} 源列 role={src_col.get('role')}，必须为 measure/percent")
        if s.get("unit") != src_col.get("unit"):
            errors.append(
                f"V-5: {prefix} unit={s.get('unit')} 与源列 unit={src_col.get('unit')} 不一致"
            )
        if s.get("unit") not in NUMERIC_UNITS:
            errors.append(f"{prefix} unit={s.get('unit')} 非法")
        if s.get("axis") not in AXES:
            errors.append(f"{prefix} axis={s.get('axis')} 非法")
        if s.get("kind") not in SERIES_KINDS:
            errors.append(f"{prefix} kind={s.get('kind')} 非法")

        data = s.get("data")
        if not isinstance(data, list):
            errors.append(f"{prefix} data 必须为数组")
            continue
        if chart_type != "scatter" and len(data) != n_cat:
            errors.append(f"V-1: {prefix} data 长度 {len(data)} != categories 长度 {n_cat}")
        if any(v is not None and not isinstance(v, (int, float)) for v in data):
            errors.append(f"{prefix} data 只允许 number/null（禁止字符串与 0 顶替缺失）")

    # 轴配置存在性
    axes = spec.get("axes") or {}
    if "primary" not in axes:
        errors.append("axes.primary 必填")

    percent_series = [s for s in series if s.get("unit") == "percent"]
    non_percent_series = [s for s in series if s.get("unit") != "percent"]

    # V-3：混图时 percent 必须挂副轴；主副轴 unit 不得相同
    if percent_series and non_percent_series:
        for s in percent_series:
            if s.get("axis") != "secondary":
                errors.append(f"V-3: percent 序列 {s.get('source_column')} 必须挂副轴 secondary")
        secondary_unit = (axes.get("secondary") or {}).get("unit")
        if secondary_unit != "percent":
            errors.append("V-3: 存在 percent 副轴序列时 axes.secondary.unit 必须为 percent")
        primary_units = {s.get("unit") for s in non_percent_series}
        if "percent" in primary_units or len(primary_units) > 1:
            errors.append("V-3: 主轴序列单位必须统一且不得为 percent")

    # V-4：combo
    if chart_type == "combo":
        if len(series) < 2:
            errors.append("V-4: combo 至少 2 个序列")
        kinds = {s.get("kind") for s in series}
        if len(kinds) < 2:
            errors.append("V-4: combo 必须包含至少两种不同 kind")
        for s in percent_series:
            if s.get("kind") != "line":
                errors.append(f"V-4: combo 中 percent 序列 {s.get('source_column')} kind 必须为 line")

    # V-6：slope —— 实体为 categories，series 为各期同单位 measure 快照
    if chart_type == "slope":
        if len(series) < 2:
            errors.append("V-6: slope 至少 2 个序列（两期快照）")
        units = {s.get("unit") for s in series}
        roles = {seen_columns.get(s.get("source_column"), {}).get("role") for s in series}
        if len(units) != 1 or "percent" in units:
            errors.append("V-6: slope 所有序列必须为同一非 percent 单位")
        if roles != {"measure"}:
            errors.append("V-6: slope 序列必须全部来自 measure 列")

    # V-7：scatter —— 恰好 2 个 measure 序列
    if chart_type == "scatter":
        if len(series) != 2:
            errors.append("V-7: scatter 必须恰好 2 个序列（X/Y）")
        if any(s.get("kind") != "scatter" for s in series):
            errors.append("V-7: scatter 序列 kind 必须为 scatter")
        if any(seen_columns.get(s.get("source_column"), {}).get("role") != "measure" for s in series):
            errors.append("V-7: scatter 两个序列必须来自 measure 列")

    # V-8：pie —— 恰好 1 个 measure 序列
    if chart_type == "pie":
        if len(series) != 1:
            errors.append("V-8: pie 必须恰好 1 个序列")
        elif seen_columns.get(series[0].get("source_column"), {}).get("role") != "measure":
            errors.append("V-8: pie 序列必须来自 measure 列")

    return errors
