"""M3 图表推荐模块（SPEC §6 M3 / §5.4 / §5.5，v1.3）。

流程：构造 prompt → 调用 OpenAI 兼容 LLM（模型名走环境变量）→
容错解析裸 JSON 数组（剥围栏 / 兼容旧包装）→ Schema 与引用校验（失败重试 1 次）→
轴归一 → 数据投影（null 原样保留）→ V-1~V-8 校验 → 缺失系列确定性标注 →
三语义层覆盖补齐（降级）→ 去重截断 1~6 条。

数据全部来自 SemanticTable 投影，LLM 给的任何数值都不会进入 ChartSpec。
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

import httpx

from app.config import settings
from app.validators import CHART_TYPES, PERCENT_ALLOWED_TYPES, validate_chart_spec
LAYERS = {"trend", "comparison", "rate"}
MAX_RECOMMENDATIONS = 8

# v1.14：title/reasoning/模板按界面语言输出；列名等数据始终保持原文。
# v1.17：界面语言扩为 zh/en/fr/de/es，后端仍维护 zh/en 两套模板——
# 仅 "zh" 走中文，其余一切取值（fr/de/es/非法值/缺省）统一回退英文（出海默认英文）。
LANGS = ("zh", "en")
DEFAULT_LANG = "en"
INCOMPLETE_NOTE = {
    "zh": "该系列数据不完整，建议不纳入",
    "en": "Incomplete data for this series; exclude with caution",
}
DEGRADED_NOTE = {
    "zh": "启发式降级推荐（LLM 不可用或结果不完整）",
    "en": "Heuristic recommendation (LLM unavailable or incomplete)",
}


def normalize_lang(lang: Any) -> str:
    """归一化界面语言：仅 zh 走中文，其余（含 fr/de/es 与非法/缺省值）统一回退 en（v1.17）。"""
    return "zh" if lang == "zh" else DEFAULT_LANG


# LLM 可调用签名：(messages) -> 文本。测试通过注入 mock 替换。
LLMCallable = Callable[[list[dict[str, str]]], str]


class RecommendationError(Exception):
    """LLM 与降级均无法产出任何合法推荐。"""


# --------------------------------------------------------------------------- #
# 表辅助
# --------------------------------------------------------------------------- #

def _columns_by_name(table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["name"]: c for c in table["columns"]}


def _column_values(table: dict[str, Any], name: str) -> list[Any]:
    idx = next(i for i, c in enumerate(table["columns"]) if c["name"] == name)
    return [row[idx] for row in table["rows"]]


def _pick_dimension(table: dict[str, Any], preferred: str | None) -> str | None:
    cols = table["columns"]
    if preferred and preferred in _columns_by_name(table):
        col = _columns_by_name(table)[preferred]
        if col["role"] == "dimension":
            return preferred
    dims = [c["name"] for c in cols if c["role"] == "dimension"]
    return dims[0] if dims else None


# --------------------------------------------------------------------------- #
# LLM 调用与容错解析
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT_ZH = """你是数据图表推荐引擎。根据用户给出的表结构摘要，推荐 1~6 个图表。
硬性规则：
1. 只输出严格 JSON 数组，顶层必须是 [ ... ]，禁止 Markdown 代码围栏、禁止任何解释文字。
2. 每个元素形如 {"chart_type","title","reasoning","config"}，字段缺一不可，不得额外加字段。
3. chart_type 只能取：bar、hbar、line、area、combo、stacked、slope、scatter、waterfall、radar、pie、donut、sunburst。
4. config = {"dimension": 维度列名, "semantic_layer": "trend"|"comparison"|"rate", "series":[{"column": 数值列名, "kind"?: "line"|"bar"|"scatter", "axis"?: "primary"|"secondary"}]}。
5. 你只能引用表中真实存在的列，且禁止输出任何数据值；数据由系统投影。列名与维度取值必须原样引用，不得翻译。
6. 百分比列（unit=percent）只能出现在 bar、hbar、line、area、combo 中；combo 中须作副轴折线（kind=line）；
   stacked、waterfall、radar、slope、scatter、pie、donut、sunburst 不得使用百分比列。
7. 推荐必须尽量覆盖三个语义层：trend（趋势，如多期折线/面积/斜率）、comparison（体量对比，柱/条/堆叠/饼/圆环/雷达/散点/旭日）、
   rate（变化率，百分比副轴组合图）。null_count>0 的列可以使用，但要在 reasoning 中提示数据不完整。
8. title 不超过 60 字，reasoning 不超过 200 字，均使用中文。
9. 形态约束：combo ≥2 列；stacked ≥2 个同单位列；scatter 恰好 2 列；pie/donut/sunburst/waterfall 恰好 1 列；radar ≥3 个同单位列。"""

SYSTEM_PROMPT_EN = """You are a data-chart recommendation engine. Based on the table schema summary given by the user, recommend 1~6 charts.
Hard rules:
1. Output ONLY a strict JSON array; the top level must be [ ... ]. No Markdown code fences, no explanatory text.
2. Each element has the shape {"chart_type","title","reasoning","config"}; all fields are required and no extra fields are allowed.
3. chart_type must be one of: bar, hbar, line, area, combo, stacked, slope, scatter, waterfall, radar, pie, donut, sunburst.
4. config = {"dimension": dimension column name, "semantic_layer": "trend"|"comparison"|"rate", "series":[{"column": numeric column name, "kind"?: "line"|"bar"|"scatter", "axis"?: "primary"|"secondary"}]}.
5. Only reference columns that actually exist in the table, and never output any data values; the system projects the data. Column names and dimension values must be quoted verbatim and MUST NOT be translated.
6. Percent columns (unit=percent) may only appear in bar, hbar, line, area, combo; in combo they must be a secondary-axis line (kind=line).
   stacked, waterfall, radar, slope, scatter, pie, donut, sunburst must not use percent columns.
7. Recommendations should cover three semantic layers as much as possible: trend (multi-period line/area/slope), comparison (bar/hbar/stacked/pie/donut/radar/scatter/sunburst for magnitude),
   and rate (percent secondary-axis combo). Columns with null_count>0 may be used, but mention the incomplete data in reasoning.
8. title is at most 80 characters and reasoning at most 280 characters; BOTH must be written in English.
9. Shape constraints: combo >=2 columns; stacked >=2 same-unit columns; scatter exactly 2 columns; pie/donut/sunburst/waterfall exactly 1 column; radar >=3 same-unit columns."""


def _system_prompt(lang: str) -> str:
    return SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_ZH


def _build_user_prompt(table: dict[str, Any], lang: str = DEFAULT_LANG) -> str:
    summary = []
    for c in table["columns"]:
        s = c["stats"]
        summary.append(
            f"- {c['name']}: role={c['role']}, unit={c['unit']}, "
            f"null_count={s['null_count']}, distinct={s['distinct_count']}"
        )
    if lang == "en":
        lines = ["Table schema summary:", *summary, "", "Sample rows (up to 10):"]
        lines.append(" | ".join(c["name"] for c in table["columns"]))
        for row in table["rows"][:10]:
            lines.append(" | ".join("" if v is None else str(v) for v in row))
        lines.append("")
        lines.append("Output a strict JSON array.")
    else:
        lines = ["表结构摘要：", *summary, "", "抽样数据（最多 10 行）："]
        lines.append(" | ".join(c["name"] for c in table["columns"]))
        for row in table["rows"][:10]:
            lines.append(" | ".join("" if v is None else str(v) for v in row))
        lines.append("")
        lines.append("请输出严格 JSON 数组。")
    return "\n".join(lines)


def call_llm(messages: list[dict[str, str]]) -> str:
    """真实 OpenAI 兼容调用。LLM_API_KEY 未配置时直接失败（由上层走降级）。"""
    if not settings.llm_api_key:
        raise RecommendationError("LLM_API_KEY 未配置")
    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "messages": messages,
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_llm_json(raw: str) -> list[dict[str, Any]]:
    """容错解析：直接 parse → 剥 Markdown 围栏 → 兼容 {"recommendations":[...]} 包装。

    成功返回 list；失败抛 ValueError（触发重试）。
    """
    text = raw.strip()

    def _try(t: str) -> Any:
        return json.loads(t)

    candidates = [text]
    m = _FENCE_RE.search(text)
    if m:
        candidates.append(m.group(1).strip())

    for cand in candidates:
        try:
            obj = _try(cand)
            break
        except (json.JSONDecodeError, TypeError):
            obj = None
    else:
        obj = None
    if obj is None:
        raise ValueError("LLM 输出无法解析为 JSON")

    if isinstance(obj, dict) and isinstance(obj.get("recommendations"), list):
        obj = obj["recommendations"]
    if not isinstance(obj, list):
        raise ValueError("LLM 输出顶层必须是 JSON 数组")
    if not all(isinstance(item, dict) for item in obj):
        raise ValueError("LLM 数组元素必须全部为对象")
    return obj


# --------------------------------------------------------------------------- #
# 单条 LLM 推荐 → ChartSpec 投影
# --------------------------------------------------------------------------- #

def _validate_item_shape(item: dict[str, Any]) -> None:
    for key in ("chart_type", "title", "config", "reasoning"):
        if key not in item:
            raise ValueError(f"推荐缺少字段 {key}")
    if item["chart_type"] not in CHART_TYPES:
        raise ValueError(f"非法 chart_type={item['chart_type']!r}")
    config = item["config"]
    if not isinstance(config, dict) or not isinstance(config.get("series"), list) or not config["series"]:
        raise ValueError("config.series 必须为非空数组")
    if not isinstance(item["title"], str) or not item["title"].strip():
        raise ValueError("title 必须为非空字符串")


def _project_spec(item: dict[str, Any], table: dict[str, Any], seq: int,
                  lang: str = DEFAULT_LANG) -> dict[str, Any] | None:
    """把一条合法 LLM 推荐投影为完整 ChartSpec；任何环节非法返回 None。"""
    try:
        _validate_item_shape(item)
    except ValueError:
        return None

    chart_type = item["chart_type"]
    cols = _columns_by_name(table)
    dimension = _pick_dimension(table, item["config"].get("dimension"))
    if dimension is None:
        return None

    raw_series = item["config"]["series"]
    projected: list[dict[str, Any]] = []
    used: set[str] = set()

    for ref in raw_series:
        if not isinstance(ref, dict) or not isinstance(ref.get("column"), str):
            return None
        name = ref["column"]
        if name in used or name not in cols:
            return None
        src = cols[name]
        if src["role"] not in ("measure", "percent"):
            return None
        used.add(name)

        is_percent = src["unit"] == "percent"
        # 类型-单位硬约束（SPEC §5.4 新类型 percent 口径）
        if is_percent and chart_type not in PERCENT_ALLOWED_TYPES:
            return None

        if chart_type == "scatter":
            kind, axis = "scatter", "primary"
        elif chart_type in ("pie", "donut", "sunburst"):
            kind, axis = "bar", "primary"
        elif is_percent:
            kind = "line"                       # percent 强制副轴折线
            axis = "secondary"
        elif chart_type == "combo":
            kind = ref.get("kind") if ref.get("kind") in ("line", "bar") else "bar"
            axis = "primary"
        else:
            kind = "line" if chart_type in ("line", "slope", "area") else "bar"
            axis = "primary"

        projected.append({
            "name": name,
            "source_column": name,
            "kind": kind,
            "unit": src["unit"],
            "axis": axis,
            "data": _column_values(table, name),
        })

    # 类型形态约束
    if chart_type == "scatter" and len(projected) != 2:
        return None
    if chart_type in ("pie", "donut", "sunburst", "waterfall") and len(projected) != 1:
        return None
    if chart_type == "stacked" and len(projected) < 2:
        return None
    if chart_type == "radar" and len(projected) < 3:
        return None

    categories = [str(v) for v in _column_values(table, dimension)]
    units_in_axis = {s["unit"] for s in projected if s["axis"] == "primary"}
    axes: dict[str, Any] = {"primary": {"unit": next(iter(units_in_axis)), "title": None}}
    if any(s["axis"] == "secondary" for s in projected):
        axes["secondary"] = {"unit": "percent", "title": None}

    layer = item["config"].get("semantic_layer")
    spec = {
        "id": f"rec-{seq:02d}",
        "chart_type": chart_type,
        "title": item["title"].strip(),
        "subtitle": None,
        "reasoning": str(item.get("reasoning", ""))[:200],
        "semantic_layer": layer if layer in LAYERS else _infer_layer(chart_type, projected),
        "dimension_column": dimension,
        "categories": categories,
        "series": projected,
        "axes": axes,
    }
    if validate_chart_spec(spec, table):
        return None
    _annotate_incomplete(spec, lang)
    return spec


def _infer_layer(chart_type: str, series: list[dict[str, Any]]) -> str:
    if any(s["unit"] == "percent" for s in series):
        return "rate"
    if chart_type in ("line", "slope", "area"):
        return "trend"
    return "comparison"


def _annotate_incomplete(spec: dict[str, Any], lang: str = DEFAULT_LANG) -> None:
    """SPEC §6 M3 规则 5：含 null 的系列确定性追加提示（v1.14 双语），禁止编造数值。"""
    note = INCOMPLETE_NOTE[lang]
    sep = "; " if lang == "en" else "；"
    prefix = ": " if lang == "en" else "："
    notes = [
        f"{s['source_column']}{prefix}{note}"
        for s in spec["series"]
        if any(v is None for v in s["data"])
    ]
    if not notes:
        return
    reasoning = spec.get("reasoning", "")
    # 任一语言的固定短语出现过都视为已注明，避免重复追加
    if note in reasoning or INCOMPLETE_NOTE["zh"] in reasoning:
        return
    addition = sep.join(notes)
    spec["reasoning"] = f"{reasoning}{sep}{addition}" if reasoning else addition


# --------------------------------------------------------------------------- #
# 降级（启发式 + 三语义层补齐）
# --------------------------------------------------------------------------- #

def _fallback_specs(table: dict[str, Any], lang: str = DEFAULT_LANG) -> list[dict[str, Any]]:
    cols = table["columns"]
    dim = next((c["name"] for c in cols if c["role"] == "dimension"), None)
    measures = [c["name"] for c in cols if c["role"] == "measure"]
    percents = [c["name"] for c in cols if c["role"] == "percent"]
    if dim is None or (not measures and not percents):
        return []

    categories = [str(v) for v in _column_values(table, dim)]
    seq = 0

    def make(
        chart_type: str,
        title: str,
        col_names: list[str],
        layer: str,
        kinds: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        nonlocal seq
        seq += 1
        kinds = kinds or {}
        series = []
        for name in col_names:
            unit = _columns_by_name(table)[name]["unit"]
            is_pct = unit == "percent"
            if name in kinds:
                default_kind = kinds[name]
            elif chart_type == "scatter":
                default_kind = "scatter"
            elif is_pct or chart_type in ("line", "slope", "area"):
                default_kind = "line"
            else:
                default_kind = "bar"
            series.append({
                "name": name,
                "source_column": name,
                "kind": default_kind,
                "unit": unit,
                "axis": "secondary" if is_pct else "primary",
                "data": _column_values(table, name),
            })
        primary_units = {s["unit"] for s in series if s["axis"] == "primary"}
        axes: dict[str, Any] = {"primary": {"unit": next(iter(primary_units)), "title": None}}
        if any(s["axis"] == "secondary" for s in series):
            axes["secondary"] = {"unit": "percent", "title": None}
        spec = {
            "id": f"rec-{seq:02d}",
            "chart_type": chart_type,
            "title": title,
            "subtitle": None,
            "reasoning": DEGRADED_NOTE[lang],
            "semantic_layer": layer,
            "dimension_column": dim,
            "categories": categories,
            "series": series,
            "axes": axes,
        }
        _annotate_incomplete(spec, lang)
        return spec

    out: list[dict[str, Any]] = []

    # rate：measure + percent → combo 双轴
    if measures and percents:
        title_en = f"{measures[0]} and {percents[0]} by {dim}" if lang == "en" else \
            f"{dim}{measures[0]}规模与{percents[0]}"
        out.append(make("combo", title_en, [*measures[:2], percents[0]], "rate"))

    # trend：≥2 同单位 measure → line；恰两期补 slope；再补 area 变体
    unit_groups: dict[str, list[str]] = {}
    for name in measures:
        unit_groups.setdefault(_columns_by_name(table)[name]["unit"], []).append(name)
    for unit, names in unit_groups.items():
        if len(names) >= 2:
            title_line = f"{dim} trend across periods" if lang == "en" else f"{dim}各期指标趋势"
            title_area = f"{dim} area across periods" if lang == "en" else f"{dim}各期指标面积"
            title_stack = f"Stacked composition by {dim}" if lang == "en" else f"各{dim}指标堆叠构成"
            out.append(make("line", title_line, names[:4], "trend"))
            out.append(make("area", title_area, names[:2], "trend"))
            out.append(make("stacked", title_stack, names[:3], "comparison"))
            if len(names) == 2:
                title_slope = f"{dim} two-period slope" if lang == "en" else f"{dim}两期变化斜率"
                out.append(make("slope", title_slope, names, "trend"))
            if len(names) >= 3:
                title_radar = f"{dim} radar" if lang == "en" else f"{dim}指标雷达"
                out.append(make("radar", title_radar, names[:5], "comparison"))
            break

    # comparison：bar（每实体一个 measure）+ 占比类
    if measures:
        title_bar = f"{measures[0]} by {dim}" if lang == "en" else f"各{dim}{measures[0]}对比"
        title_donut = f"{measures[0]} share by {dim}" if lang == "en" else f"各{dim}{measures[0]}占比构成"
        out.append(make("bar", title_bar, [measures[0]], "comparison"))
        out.append(make("donut", title_donut, [measures[0]], "comparison"))
        if len(measures) >= 2:
            title_scatter = f"{measures[0]} vs {measures[1]}" if lang == "en" else f"{measures[0]}与{measures[1]}相关性"
            out.append(make("scatter", title_scatter, measures[:2], "comparison"))
        else:
            title_pie = f"{measures[0]} proportion by {dim}" if lang == "en" else f"各{dim}{measures[0]}占比"
            out.append(make("pie", title_pie, [measures[0]], "comparison"))

    # 只过 validator 保护
    return [s for s in out if not validate_chart_spec(s, table)]


def _ensure_layers(specs: list[dict[str, Any]], table: dict[str, Any],
                   lang: str = DEFAULT_LANG) -> list[dict[str, Any]]:
    """补齐 trend/comparison/rate 三层（数据支持时）。"""
    covered = {s["semantic_layer"] for s in specs}
    existing_keys = {(s["chart_type"], tuple(s["source_column"] for s in s["series"])) for s in specs}
    for fb in _fallback_specs(table, lang):
        if fb["semantic_layer"] not in covered:
            key = (fb["chart_type"], tuple(s["source_column"] for s in fb["series"]))
            if key not in existing_keys:
                specs.append(fb)
                existing_keys.add(key)
                covered.add(fb["semantic_layer"])
    return specs


def _dedupe(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for spec in specs:
        key = (spec["chart_type"], tuple(s["source_column"] for s in spec["series"]),
               spec["dimension_column"])
        if key in seen:
            continue
        seen.add(key)
        # 重新编号
        spec["id"] = f"rec-{len(out) + 1:02d}"
        out.append(spec)
    return out[:MAX_RECOMMENDATIONS]


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #

def recommend_charts(
    table: dict[str, Any],
    llm_call: LLMCallable | None = None,
    lang: str = DEFAULT_LANG,
) -> dict[str, Any]:
    """SemanticTable → {recommendations: ChartSpec[], degraded: bool}。

    llm_call 可注入（测试 mock）；默认走真实 OpenAI 兼容接口。
    未配置 key / 调用失败 / 两轮解析失败时降级，degraded=True。
    lang（v1.14/v1.17）决定 title/reasoning 与降级模板语言：仅 "zh" 走中文，
    其余取值（含 fr/de/es 与非法值）统一回退英文；列名等数据保持原文。
    """
    lang = normalize_lang(lang)
    llm_call = llm_call or call_llm
    messages = [
        {"role": "system", "content": _system_prompt(lang)},
        {"role": "user", "content": _build_user_prompt(table, lang)},
    ]

    specs: list[dict[str, Any]] = []
    degraded = False
    last_error = ""

    for attempt in range(2):  # 初次 + 重试 1 次（SPEC C-5）
        try:
            retry_nudge = (
                f"The previous output was unusable ({last_error or 'unknown error'}); "
                "output ONLY a bare JSON array following the rules."
                if lang == "en"
                else f"上一次输出无法使用（{last_error or '未知错误'}），"
                     "请严格按规则只输出裸 JSON 数组。"
            )
            raw = llm_call(messages if attempt == 0 else messages + [
                {"role": "user", "content": retry_nudge},
            ])
            items = parse_llm_json(raw)
        except Exception as exc:  # noqa: BLE001 - LLM 侧任何异常都应触发重试/降级
            last_error = str(exc)
            continue

        for i, item in enumerate(items, start=1):
            spec = _project_spec(item, table, i, lang)
            if spec is not None:
                specs.append(spec)
        if specs:
            break
        last_error = "所有推荐条目均未通过引用/不变式校验"

    if not specs:
        # LLM 两轮均无任何合法产出 → 完全降级
        degraded = True
        specs = _fallback_specs(table, lang)
    else:
        # LLM 已产出，仅对未覆盖的语义层用启发式补齐，degraded 保持 False
        specs = _ensure_layers(specs, table, lang)

    if not specs:
        msg = ("No plottable numeric columns in the data; cannot recommend any chart."
               if lang == "en"
               else "数据中没有可绘图的数值列，无法推荐任何图表")
        raise RecommendationError(msg)

    return {"recommendations": _dedupe(specs), "degraded": degraded}
