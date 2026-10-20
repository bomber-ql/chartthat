"""M4 PPT 生成模块（SPEC §6 M4，v1.6 单图导出契约，十三图型全覆盖）。

入口：build_pptx(request: dict) -> bytes
- 接收自描述单图请求 {chart_type, config?, data:{categories, series[]}}（§5.6）；
- bar/hbar/line/area/stacked/slope/radar 走 python-pptx add_chart + CategoryChartData
  （slope 按两期 LINE_MARKERS，R-4；hbar=BAR_CLUSTERED、stacked=COLUMN_STACKED、radar=RADAR_MARKERS）；
- scatter 走 XyChartData（无效点剔除）；pie/donut/sunburst 走 PIE/DOUGHNUT（null 扇区剔除，
  sunburst 降级 DOUGHNUT，R-5）；waterfall 走 COLUMN_STACKED 透明底座等价（R-5）；
- combo 走 ablechart.create_combo_chart（bar 主轴 + percent line 副轴）；
- 全程 None 空点（C-3），line/slope 显式 dispBlanksAs=gap；
- 副轴 0.0%、主轴带单位（yi -> 0.0"亿"）（§5.1 / C-4）；
- 保存前断所有外部数据链接（C-2 等价实现，R-2）；
- v1.11：标准导出恒为纯静态原生图表；动效版改由独立 GIF 端点提供
  （gif_builder.py，SPEC §5.6a/§6a，R-6）。
"""
from __future__ import annotations

import io
from typing import Any

import pandas as pd
from lxml import etree
from pptx import Presentation
from pptx.chart.chart import Chart
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

import ablechart

from app.modules.parser import ParseError

C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
NSMAP = {"c": C_NS}

SUPPORTED_TYPES = {
    "bar", "hbar", "line", "area", "combo", "stacked", "slope",
    "scatter", "waterfall", "radar", "pie", "donut", "sunburst",
}  # v1.6 十三型全覆盖
# percent 序列禁止出现的图型（与 M3/validators 口径一致）
_NO_PERCENT_TYPES = {"slope", "scatter", "pie", "donut", "sunburst", "stacked", "waterfall", "radar"}
SERIES_UNITS = {"count", "yi", "wan", "percent"}
SERIES_KINDS = {"line", "bar", "scatter"}
AXES = {"primary", "secondary"}

# 主/次轴单位对应的轴 tick label 数字格式（§6 M4 规则 4）。
_AXIS_FORMAT = {"count": "General", "yi": '0.0"亿"', "wan": '0.0"万"', "percent": "0.0%"}


class PptxValidationError(ParseError):
    """M4 入参校验错误（HTTP 400）。"""


# --------------------------------------------------------------------------
# 校验（SPEC §5.6 入参校验规则）
# --------------------------------------------------------------------------
def _validate_request(req: Any) -> dict[str, Any]:
    if not isinstance(req, dict):
        raise PptxValidationError("VALIDATION_FAILED", "请求体必须为 JSON 对象 {chart_type, config, data}")

    chart_type = req.get("chart_type")
    if not isinstance(chart_type, str):
        raise PptxValidationError("VALIDATION_FAILED", "缺少字段 chart_type")
    if chart_type not in SUPPORTED_TYPES:
        raise PptxValidationError("VALIDATION_FAILED", f"未知 chart_type：{chart_type}")

    data = req.get("data")
    if not isinstance(data, dict):
        raise PptxValidationError("VALIDATION_FAILED", "缺少字段 data：{categories, series}")

    categories = data.get("categories")
    if not isinstance(categories, list) or not categories or not all(isinstance(c, str) for c in categories):
        raise PptxValidationError("VALIDATION_FAILED", "data.categories 必须为非空字符串数组")

    raw_series = data.get("series")
    if not isinstance(raw_series, list) or not raw_series:
        raise PptxValidationError("VALIDATION_FAILED", "data.series 必须为非空数组")

    n = len(categories)
    norm: list[dict[str, Any]] = []
    for i, s in enumerate(raw_series):
        if not isinstance(s, dict):
            raise PptxValidationError("VALIDATION_FAILED", f"series[{i}] 必须为对象")
        name = s.get("name")
        if not isinstance(name, str) or not name:
            raise PptxValidationError("VALIDATION_FAILED", f"series[{i}].name 必须为非空字符串")
        values = s.get("data")
        if not isinstance(values, list) or len(values) != n:
            raise PptxValidationError(
                "VALIDATION_FAILED", f"series[{i}].data 长度必须等于 categories 长度（{n}）"
            )
        clean: list[float | None] = []
        for v in values:
            if v is None:
                clean.append(None)
            elif isinstance(v, bool) or not isinstance(v, (int, float)):
                raise PptxValidationError("VALIDATION_FAILED", f"series[{i}].data 只允许 number 或 null")
            else:
                clean.append(float(v))
        unit = s.get("unit", "count")
        if unit not in SERIES_UNITS:
            raise PptxValidationError("VALIDATION_FAILED", f"series[{i}].unit 非法：{unit}")
        axis = s.get("axis", "primary")
        if axis not in AXES:
            raise PptxValidationError("VALIDATION_FAILED", f"series[{i}].axis 非法：{axis}")
        kind = s.get("kind")
        if kind is not None and kind not in SERIES_KINDS:
            raise PptxValidationError("VALIDATION_FAILED", f"series[{i}].kind 非法：{kind}")
        # percent 形态宽松校验：拦截 11.2 这种未除以 100 的值（§5.1）。
        if unit == "percent":
            for v in clean:
                if v is not None and abs(v) > 1.5:
                    raise PptxValidationError(
                        "VALIDATION_FAILED",
                        f"series[{i}] 为 percent，数值应为小数形态（如 11.2% -> 0.112），收到 {v}",
                    )
        norm.append({"name": name, "data": clean, "unit": unit, "axis": axis, "kind": kind})

    if chart_type == "combo":
        kinds = {(s["kind"] or "bar") for s in norm}
        if len(norm) < 2 or not {"bar", "line"} <= kinds:
            raise PptxValidationError(
                "VALIDATION_FAILED", "combo 至少需 2 个系列，且同时包含 kind=bar 与 kind=line"
            )
        for i, s in enumerate(norm):
            if s["unit"] == "percent" and not (s["kind"] == "line" and s["axis"] == "secondary"):
                raise PptxValidationError(
                    "VALIDATION_FAILED", f"combo 的 percent 系列必须 kind=line 且 axis=secondary（series[{i}]）"
                )
        primary_units = {s["unit"] for s in norm if s["axis"] == "primary"}
        secondary_units = {s["unit"] for s in norm if s["axis"] == "secondary"}
        if primary_units & secondary_units:
            raise PptxValidationError("VALIDATION_FAILED", "主、副轴 unit 不得相同（V-3 / C-4）")

    # 形态约束（§5.6 入参校验规则 + V-9~V-12，v1.6）
    if chart_type == "scatter" and len(norm) != 2:
        raise PptxValidationError("VALIDATION_FAILED", "scatter 需恰好 2 个系列（x、y）")
    if chart_type == "pie" and len(norm) != 1:
        raise PptxValidationError("VALIDATION_FAILED", "pie 需恰好 1 个系列")
    if chart_type in {"donut", "sunburst", "waterfall"} and len(norm) != 1:
        raise PptxValidationError("VALIDATION_FAILED", f"{chart_type} 需恰好 1 个系列")
    if chart_type == "stacked":
        if len(norm) < 2:
            raise PptxValidationError("VALIDATION_FAILED", "stacked 至少需 2 个系列")
        if len({s["unit"] for s in norm}) != 1:
            raise PptxValidationError("VALIDATION_FAILED", "stacked 所有系列单位必须一致")
    if chart_type == "radar":
        if len(norm) < 3:
            raise PptxValidationError("VALIDATION_FAILED", "radar 至少需 3 个系列（指标 ≥3）")
        if len({s["unit"] for s in norm}) != 1:
            raise PptxValidationError("VALIDATION_FAILED", "radar 所有系列单位必须一致")
    if chart_type in _NO_PERCENT_TYPES:
        for i, s in enumerate(norm):
            if s["unit"] == "percent":
                raise PptxValidationError(
                    "VALIDATION_FAILED", f"{chart_type} 不允许 percent 系列（series[{i}]，与 M3 口径一致）"
                )

    config = req.get("config") or {}
    if not isinstance(config, dict):
        raise PptxValidationError("VALIDATION_FAILED", "config 必须为对象")
    title = config.get("title")
    if title is not None and not isinstance(title, str):
        raise PptxValidationError("VALIDATION_FAILED", "config.title 必须为字符串或 null")

    return {"chart_type": chart_type, "categories": categories, "series": norm, "title": title}


# --------------------------------------------------------------------------
# 数字格式（§6 M4 规则 4）
# --------------------------------------------------------------------------
def _set_axis_numfmt(chart: Chart, axis_index: int, fmt: str) -> None:
    """设置第 axis_index 个 c:valAx 的 tick label 数字格式（0=主轴，1=副轴）。"""
    chart_space = chart._chartSpace  # noqa: SLF001 - python-pptx 未提供公共轴格式 API
    val_axes = chart_space.findall(".//c:valAx", NSMAP)
    if axis_index >= len(val_axes):
        return
    val_ax = val_axes[axis_index]
    num_fmt = val_ax.find("c:numFmt", NSMAP)
    if num_fmt is None:
        # 插入到 valAx 开头（schema 中 numFmt 位于 axId/scaling 之后较宽松，直接 append 也可被 Office 接受；
        # 稳妥起见放在 scaling 之后）。
        num_fmt = etree.SubElement(val_ax, f"{{{C_NS}}}numFmt")
        scaling = val_ax.find("c:scaling", NSMAP)
        if scaling is not None:
            scaling.addnext(num_fmt)
    num_fmt.set("formatCode", fmt)
    num_fmt.set("sourceLinked", "0")


def _set_gap_for_nulls(chart: Chart) -> None:
    """line 图：显式 c:dispBlanksAs val=gap（C-3，空点断线不当 0）。"""
    chart_space = chart._chartSpace  # noqa: SLF001
    for parent in chart_space.findall(".//c:lineChart", NSMAP):
        disp = parent.find("c:dispBlanksAs", NSMAP)
        if disp is None:
            disp = etree.SubElement(parent, f"{{{C_NS}}}dispBlanksAs")
            # dispBlanksAs 在 CT_LineChart 中位于 smooth 之后、axId 之前。
            anchor = parent.find("c:smooth", NSMAP)
            if anchor is not None:
                anchor.addnext(disp)
        disp.set("val", "gap")


# --------------------------------------------------------------------------
# C-2：断开外部数据链接（等价 BreakLink，R-2）
# --------------------------------------------------------------------------
def break_external_chart_links(prs: Presentation) -> None:
    """遍历所有 has_chart shape：删除外部关系 + 移除悬空的 c:externalData 引用。

    保留内部嵌入 workbook 的 package 关系（双击编辑依赖它）；仅 IsLinked（外部）
    语义的部分被断开。
    """
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_chart:
                continue
            chart = shape.chart
            part = chart.part
            external_rids = [rid for rid, rel in part.rels.items() if rel.is_external]
            for rid in external_rids:
                part.drop_rel(rid)

            chart_space = chart._chartSpace  # noqa: SLF001
            chart_el = chart_space.find("c:chart", NSMAP)
            if chart_el is None:
                continue
            for ext in chart_el.findall("c:externalData", NSMAP):
                rid = ext.get(f"{{http://schemas.openxmlformats.org/officeDocument/2006/relationships}}id")
                # 引用已不存在（外部链已删）或本就悬空 -> 移除空引用节点。
                if rid is None or rid not in part.rels:
                    chart_el.remove(ext)


# --------------------------------------------------------------------------
# 各图型构建
# --------------------------------------------------------------------------
def _add_title(slide: Any, title: str) -> None:
    if not title:
        return
    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
    frame = box.text_frame
    frame.text = title
    para = frame.paragraphs[0]
    para.font.size = Inches(0.32)  # ~23pt
    para.font.bold = True


def _build_category_chart(prs: Presentation, spec: dict[str, Any], chart_type: str) -> Chart:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_title(slide, spec["title"] or "")

    chart_data = CategoryChartData()
    chart_data.categories = spec["categories"]
    for s in spec["series"]:
        chart_data.add_series(s["name"], tuple(s["data"]))

    # slope 按两期 LINE_MARKERS 实现（R-4）；line 同型。
    _XL = {
        "line": XL_CHART_TYPE.LINE_MARKERS,
        "slope": XL_CHART_TYPE.LINE_MARKERS,
        "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "hbar": XL_CHART_TYPE.BAR_CLUSTERED,
        "area": XL_CHART_TYPE.AREA,
        "stacked": XL_CHART_TYPE.COLUMN_STACKED,
        "radar": XL_CHART_TYPE.RADAR_MARKERS,
    }
    xl_type = _XL[chart_type]
    top = Inches(1.2) if spec["title"] else Inches(0.5)
    graphic = slide.shapes.add_chart(
        xl_type, Inches(0.5), top, Inches(12.3), Inches(5.6), chart_data
    )
    chart = graphic.chart

    primary_unit = spec["series"][0]["unit"]
    _set_axis_numfmt(chart, 0, _AXIS_FORMAT[primary_unit])
    if chart_type in {"line", "slope"}:
        _set_gap_for_nulls(chart)
    return chart


def _build_waterfall(prs: Presentation, spec: dict[str, Any]) -> Chart:
    """waterfall 等价实现（R-5）：COLUMN_STACKED，底座系列透明 + 增量系列。

    取值口径（§6 M4 映射表）：底座 = min(前值累计, 后值累计)，增量 = |原始增量|。
    堆叠图负值会回落零轴下方独立渲染，负增量必须翻转为正值段并以下界垫高，
    否则瀑布形态断裂。None 增量保持空点（C-3），底座对应位补 0（透明不可见）。
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_title(slide, spec["title"] or "")

    s = spec["series"][0]
    base: list[float] = []
    delta: list[float | None] = []
    run = 0.0
    for v in s["data"]:
        if v is None:
            base.append(0.0)
            delta.append(None)
            continue
        base.append(min(run, run + v))
        delta.append(abs(v))
        run += v

    chart_data = CategoryChartData()
    chart_data.categories = spec["categories"]
    chart_data.add_series("底座", tuple(base))
    chart_data.add_series(s["name"], tuple(delta))

    top = Inches(1.2) if spec["title"] else Inches(0.5)
    graphic = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_STACKED, Inches(0.5), top, Inches(12.3), Inches(5.6), chart_data
    )
    chart = graphic.chart
    chart.series[0].format.fill.background()  # 底座透明，仅起垫高作用
    _set_axis_numfmt(chart, 0, _AXIS_FORMAT[s["unit"]])
    return chart


def _build_scatter(prs: Presentation, spec: dict[str, Any]) -> Chart:
    """scatter：XyChartData，任一坐标为 None 的点整体剔除（C-3）。"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_title(slide, spec["title"] or "")

    x_series, y_series = spec["series"][0], spec["series"][1]
    points = [
        (xv, yv)
        for xv, yv in zip(x_series["data"], y_series["data"])
        if xv is not None and yv is not None
    ]
    if not points:
        raise PptxValidationError("VALIDATION_FAILED", "scatter 有效数据点为空（全部坐标缺失）")

    chart_data = XyChartData()
    xy = chart_data.add_series(f"{x_series['name']} × {y_series['name']}")
    for xv, yv in points:
        xy.add_data_point(xv, yv)

    top = Inches(1.2) if spec["title"] else Inches(0.5)
    graphic = slide.shapes.add_chart(
        XL_CHART_TYPE.XY_SCATTER, Inches(0.5), top, Inches(12.3), Inches(5.6), chart_data
    )
    chart = graphic.chart
    # x 轴为 valAx[0]，y 轴为 valAx[1]，按对应系列 unit 设数字格式。
    _set_axis_numfmt(chart, 0, _AXIS_FORMAT[x_series["unit"]])
    _set_axis_numfmt(chart, 1, _AXIS_FORMAT[y_series["unit"]])
    return chart


def _build_pie(prs: Presentation, spec: dict[str, Any], chart_type: str = "pie") -> Chart:
    """pie/donut/sunburst：CategoryChartData，值为 None 的扇区整体剔除（C-3）。

    sunburst 按 R-5 降级为 DOUGHNUT 近似导出。
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_title(slide, spec["title"] or "")

    s = spec["series"][0]
    pairs = [(c, v) for c, v in zip(spec["categories"], s["data"]) if v is not None]
    if not pairs:
        raise PptxValidationError("VALIDATION_FAILED", f"{chart_type} 有效扇区为空（全部数值缺失）")

    chart_data = CategoryChartData()
    chart_data.categories = [c for c, _ in pairs]
    chart_data.add_series(s["name"], tuple(v for _, v in pairs))

    xl_type = XL_CHART_TYPE.PIE if chart_type == "pie" else XL_CHART_TYPE.DOUGHNUT
    top = Inches(1.2) if spec["title"] else Inches(0.5)
    graphic = slide.shapes.add_chart(
        xl_type, Inches(0.5), top, Inches(12.3), Inches(5.6), chart_data
    )
    return graphic.chart


def _build_combo(prs: Presentation, spec: dict[str, Any]) -> Chart:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_title(slide, spec["title"] or "")

    # DataFrame：None -> NaN，ablechart 写为空点（C-3）。
    frame_data: dict[str, Any] = {"__cat__": spec["categories"]}
    for s in spec["series"]:
        frame_data[s["name"]] = [None if v is None else v for v in s["data"]]
    df = pd.DataFrame(frame_data)

    series_config = [
        {
            "key": s["name"],
            "name": s["name"],
            "type": s["kind"] or "bar",
            "axis": s["axis"],
        }
        for s in spec["series"]
    ]
    top = Inches(1.2) if spec["title"] else Inches(0.5)
    chart = ablechart.create_combo_chart(
        slide=slide,
        df=df,
        categories_col="__cat__",
        series_config=series_config,
        position=(Inches(0.5), top),
        size=(Inches(12.3), Inches(5.6)),
        polish=False,
    )

    # 主/副轴数字格式（按各轴上系列的 unit；combo 校验保证同轴 unit 一致）。
    primary_units = {s["unit"] for s in spec["series"] if s["axis"] == "primary"}
    secondary_units = {s["unit"] for s in spec["series"] if s["axis"] == "secondary"}
    if primary_units:
        _set_axis_numfmt(chart, 0, _AXIS_FORMAT[next(iter(primary_units))])
    if secondary_units:
        _set_axis_numfmt(chart, 1, _AXIS_FORMAT[next(iter(secondary_units))])
    return chart


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def build_pptx(request: dict[str, Any]) -> bytes:
    """GeneratePptxRequest -> .pptx 字节流（SPEC §5.6 / §6 M4）。"""
    spec = _validate_request(request)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    if spec["chart_type"] == "combo":
        _build_combo(prs, spec)
    elif spec["chart_type"] == "scatter":
        _build_scatter(prs, spec)
    elif spec["chart_type"] == "waterfall":
        _build_waterfall(prs, spec)
    elif spec["chart_type"] in {"pie", "donut", "sunburst"}:
        _build_pie(prs, spec, spec["chart_type"])
    else:  # bar / hbar / line / area / stacked / slope / radar
        _build_category_chart(prs, spec, spec["chart_type"])

    break_external_chart_links(prs)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()