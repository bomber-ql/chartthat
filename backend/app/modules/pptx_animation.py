"""M4 v1.10 放映动效注入：在 slide XML 中插入 <p:timing>。

v1.9 关键修正（经 WPS 实测 + OpenXML 文档核实）：
- ``<a:bldChart bld="...">`` 只是动画窗格里的「构建声明」，不决定播放分段。
- 真正决定播放时图表按类别/系列逐段出现的，是 mainSeq 里**每个动画 effect 的
  target**：``<p:spTgt spid="..."><p:oleChartEl type="category|series" lvl="N"/>``。
  没有 oleChartEl 时（v1.7/v1.8），动画目标恒为整图，播放器（含 WPS）只能整图进入。
- 时序树结构（ECMA-376）：mainSeq 下只有**一个触发组顶层 par**（id=3，
  delay=indefinite），其 childTnLst 内一个容器 par（id=4，delay=0），再里面并排放
  所有动画段 par：首段 nodeType=``clickEffect``（等待点击），其余段
  nodeType=``afterEffect`` + ``<p:stCondLst><p:cond delay="0"/></p:stCondLst>``
  （afterEffect 语义=上一段播完自动接续，无需逐段点击）。每段的 set / animEffect
  target 都挂对应类别的 oleChartEl（lvl=类别下标）。

v1.10 修正（XML 合法性，WPS 实测完全无动画）：
- v1.9 给 afterEffect 段误用了**不存在的元素 ``<p:beginCondLst>``**（OOXML 时间节点
  条件列表只有 ``<p:stCondLst>``/``<p:endCondLst>``），WPS 解析到非法节点将整段
  ``<p:timing>`` 丢弃 → 放映完全无动画。v1.10 改为合法 ``<p:stCondLst>``。

参考：
- ECMA-376 / ISO-IEC 29500-1 §19.5.52 ``oleChartEl``（type: ST_TLChartSubelementType）
- DocumentFormat.OpenXml.Presentation.OleChartElement 官方示例。
"""
from __future__ import annotations

# (filter, build target kind, bldChart value)
#   target_kind: "category" -> 每段作用到一个类别（lvl=类别下标）
#                "series"   -> 每段作用到一个系列（lvl=系列下标）
#                "whole"    -> 单系列整图（饼图配合 wheel 轮扫）
_ANIM_BY_CHART_TYPE: dict[str, tuple[str, str, str]] = {
    "bar": ("wipe(up)", "category", "category"),
    "hbar": ("wipe(r)", "category", "category"),
    "stacked": ("wipe(up)", "category", "category"),
    "area": ("wipe(up)", "category", "category"),
    "combo": ("wipe(up)", "category", "category"),
    "waterfall": ("wipe(up)", "category", "category"),
    "radar": ("fade", "category", "category"),
    "line": ("wipe(r)", "series", "series"),
    "slope": ("wipe(r)", "series", "series"),
    "scatter": ("fade", "series", "series"),
    "pie": ("wheel(1)", "whole", "series"),
    "donut": ("wheel(1)", "whole", "series"),
    "sunburst": ("wheel(1)", "whole", "series"),
}

_STEP_MS = 500

_TIMING_HEAD = (
    '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    '<p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
    '<p:childTnLst><p:seq concurrent="1" nextAc="seek">'
    '<p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
    # 单个触发组：顶层 par(id=3, indefinite) > 容器 par(id=4, delay=0) > 各动画段
    '<p:par><p:cTn id="3" fill="hold">'
    '<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
    '<p:childTnLst><p:par><p:cTn id="4" fill="hold">'
    '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
    '<p:childTnLst>'
)
_TIMING_TAIL = (
    "</p:childTnLst></p:cTn></p:par>"
    "</p:childTnLst></p:cTn></p:par>"
    "</p:childTnLst></p:cTn>"
    '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
    '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
    "</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>"
)


def _sp_target(spid: int, ole_type: str | None, lvl: int) -> str:
    if ole_type is not None:
        return (
            f'<p:tgtEl><p:spTgt spid="{spid}">'
            f'<p:oleChartEl type="{ole_type}" lvl="{lvl}"/>'
            f"</p:spTgt></p:tgtEl>"
        )
    return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'


def _segment_par(seg_id: int, set_id: int, beh_id: int, spid: int,
                 anim_filter: str, *, click: bool,
                 ole_type: str | None, lvl: int) -> str:
    """生成容器 par(id=4) 内的单个动画段。

    首段 clickEffect（delay=indefinite，等待点击）；其余 afterEffect
    （stCondLst delay=0，上一段播完自动接续）。
    set 与 animEffect 的 target 都带 oleChartEl（whole 时为纯 spTgt）。
    """
    if click:
        node_type = "clickEffect"
        trigger = '<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
    else:
        # afterEffect 语义=「上一动画之后」自动接续；起始条件只需 delay=0。
        # 注意：合法元素是 <p:stCondLst>（不是 <p:beginCondLst>，OOXML 无此元素，
        # v1.9 误用导致 WPS 将整段 timing 判非法丢弃 → 完全无动画）。
        node_type = "afterEffect"
        trigger = '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'

    target = _sp_target(spid, ole_type, lvl)

    return (
        f'<p:par><p:cTn id="{seg_id}" fill="hold" nodeType="{node_type}">{trigger}'
        f"<p:childTnLst>"
        # set visibility visible（作用于本段子元素）
        f"<p:set><p:cBhvr>"
        f'<p:cTn id="{set_id}" dur="1" fill="hold"><p:stCondLst>'
        f'<p:cond delay="0"/></p:stCondLst></p:cTn>'
        f"{target}"
        f"<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>"
        f"</p:cBhvr><p:to><p:strVal val=\"visible\"/></p:to></p:set>"
        # 进入动画（作用于本段子元素）
        f'<p:animEffect transition="in" filter="{anim_filter}"><p:cBhvr>'
        f'<p:cTn id="{beh_id}" dur="{_STEP_MS}"/>'
        f"{target}"
        f"</p:cBhvr></p:animEffect>"
        f"</p:childTnLst></p:cTn></p:par>"
    )


def _bld_lst(spid: int, bld: str) -> str:
    return (
        "<p:bldLst>"
        f'<p:bldGraphic spid="{spid}" grpId="0">'
        f'<p:bldSub><a:bldChart bld="{bld}"/></p:bldSub>'
        "</p:bldGraphic>"
        "</p:bldLst>"
    )


def build_animation_timing(spid: int, chart_type: str, *,
                           n_categories: int, n_series: int) -> str:
    """返回可直接 append 到 slide 元素末尾（clrMapOvr 之后）的 <p:timing> XML。"""
    anim_filter, target_kind, bld = _ANIM_BY_CHART_TYPE[chart_type]

    if target_kind == "category":
        n_steps = max(1, n_categories)
        ole_type: str | None = "category"
    elif target_kind == "series":
        n_steps = max(1, n_series)
        ole_type = "series"
    else:  # whole（单系列饼/环/旭日）：wheel 轮扫整图
        n_steps = 1
        ole_type = None

    segments = []
    next_id = 5
    for i in range(n_steps):
        seg_id, set_id, beh_id = next_id, next_id + 1, next_id + 2
        next_id += 3
        segments.append(
            _segment_par(
                seg_id, set_id, beh_id, spid, anim_filter,
                click=(i == 0), ole_type=ole_type, lvl=i,
            )
        )

    return (
        _TIMING_HEAD
        + "".join(segments)
        + _TIMING_TAIL
        + _bld_lst(spid, bld)
        + "</p:timing>"
    )


def inject_chart_animation(slide, spid: int, chart_type: str, *,
                           n_categories: int, n_series: int) -> None:
    """构造 <p:timing> 并挂到 slide 元素末尾（clrMapOvr 之后）。"""
    from lxml import etree

    timing_xml = build_animation_timing(
        spid, chart_type,
        n_categories=n_categories, n_series=n_series,
    )
    timing_el = etree.fromstring(timing_xml)
    slide.element.append(timing_el)
