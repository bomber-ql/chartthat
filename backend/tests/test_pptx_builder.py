"""M4 pptx_builder 测试（SPEC §6 M4 验收 A-4.x / §5.6）。

覆盖用户要求的三条断言：
1. 所有 has_chart shape 的 chart_data.IsLinked 均为 False（无外部链接）；
2. combo 请求生成的对象同时含 barChart + lineChart + 副轴；
3. replace_data 修改内嵌数据后，图表可更新（读回验证并重新落盘）。

另覆盖：null → dispBlanksAs=gap、副轴 0.0% / 主轴「亿」、非法请求 400、HTTP 端点冒烟。
"""
from __future__ import annotations

import io
import zipfile

import pytest
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from fastapi.testclient import TestClient

from app.main import app
from app.modules.pptx_builder import PptxValidationError, build_pptx


COMBO_REQUEST = {
    "chart_type": "combo",
    "title": "规模与同比",
    "config": {"dimension": "平台"},
    "data": {
        "categories": ["微信", "抖音", "快手", "微博"],
        "series": [
            {"name": "2025 MAU", "kind": "bar", "axis": "primary", "unit": "yi",
             "data": [14.2, 11.7, 7.0, 5.7]},
            {"name": "同比", "kind": "line", "axis": "secondary", "unit": "percent",
             "data": [0.024, 0.112, -0.028, -0.039]},
        ],
    },
}

LINE_REQUEST = {
    "chart_type": "line",
    "title": "趋势",
    "config": {"dimension": "平台"},
    "data": {
        "categories": ["微信", "抖音", "快手"],
        "series": [
            {"name": "2024 DAU", "kind": "line", "unit": "yi",
             "data": [None, 7.0, 4.1]},
        ],
    },
}


def _chart_xml(blob: bytes) -> str:
    """从 pptx 中取出唯一 chart XML（测试请求均为单图）。"""
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.startswith("ppt/charts/chart") and n.endswith(".xml")]
        assert names, "pptx 内未找到 chart XML"
        return zf.read(names[0]).decode("utf-8")


def _charts(blob: bytes):
    prs = Presentation(io.BytesIO(blob))
    slide = prs.slides[0]
    return prs, slide, [sh.chart for sh in slide.shapes if sh.has_chart]


# ---------- 断言 1：全部图表 IsLinked=False（无「外部」链接，内嵌 xlsx 保留） ----------

def _external_link_targets(blob: bytes) -> list[str]:
    """收集 chart part 指向外部文件（TargetMode=External）的关系，即 IsLinked=True。

    指向内部 ../embeddings/*.xlsx 的 package 关系是内嵌工作簿，IsLinked=False，
    且是 WPS 双击编辑数据的依据，必须保留。
    """
    prs = Presentation(io.BytesIO(blob))
    external: list[str] = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_chart:
                continue
            for rel in shape.chart.part.rels.values():
                if rel.is_external:
                    external.append(rel.target_ref)
    return external


def test_all_charts_unlinked_combo():
    blob = build_pptx(COMBO_REQUEST)
    assert _external_link_targets(blob) == []
    # 内嵌工作簿仍在（可双击编辑），且不含指向包外文件的链接
    _, _, charts = _charts(blob)
    assert charts, "至少存在 1 个图表"
    xml = _chart_xml(blob)
    assert "TargetMode=\"External\"" not in xml


def test_all_charts_unlinked_line():
    blob = build_pptx(LINE_REQUEST)
    assert _external_link_targets(blob) == []


# ---------- 断言 2：combo 对象含 barChart + lineChart + 副轴 ----------

def test_combo_chart_structure():
    blob = build_pptx(COMBO_REQUEST)
    xml = _chart_xml(blob)
    assert "<c:barChart>" in xml
    assert "<c:lineChart>" in xml
    # 双值轴：主轴 + 次轴（副轴 axPos=left 是 ablechart 的表达方式，共两个 c:valAx）
    assert xml.count("<c:valAx>") == 2
    # 副轴百分比格式 0.0%
    assert 'formatCode="0.0%"' in xml
    # 主轴「亿」自定义格式
    assert '"0.0\\"' in xml or '亿' in xml
    _, _, charts = _charts(blob)
    assert len(charts) == 1
    # 两个系列：柱 + 线
    assert len(charts[0].series) == 2


# ---------- 断言 3：replace_data 修改内嵌数据后图表可更新 ----------

def test_replace_data_updates_chart_and_persists():
    blob = build_pptx(COMBO_REQUEST)
    prs, slide, _ = _charts(blob)
    chart = next(sh.chart for sh in slide.shapes if sh.has_chart)
    assert list(chart.series[0].values)[:4] == [14.2, 11.7, 7.0, 5.7]

    new_data = CategoryChartData()
    new_data.categories = ["微信", "抖音", "快手", "微博"]
    new_data.add_series("2025 MAU", (20.0, 18.0, 9.0, 6.0))
    new_data.add_series("同比", (0.05, 0.20, -0.01, -0.08))
    chart.replace_data(new_data)

    # 内存对象立即反映
    assert list(chart.series[0].values) == [20.0, 18.0, 9.0, 6.0]

    # 重新落盘再读回，确认内嵌 workbook 与图表同步更新
    out = io.BytesIO()
    prs.save(out)
    _, _, reopened = _charts(out.getvalue())
    assert list(reopened[0].series[0].values) == [20.0, 18.0, 9.0, 6.0]
    assert list(reopened[0].series[1].values) == [0.05, 0.20, -0.01, -0.08]


# ---------- C-3：null 断线 gap，不把空值当 0 ----------

def test_line_null_becomes_gap_not_zero():
    blob = build_pptx(LINE_REQUEST)
    xml = _chart_xml(blob)
    assert '<c:dispBlanksAs val="gap"/>' in xml
    _, _, charts = _charts(blob)
    values = list(charts[0].series[0].values)
    assert values[0] is None
    assert values[1] == 7.0
    assert 0 not in [v for v in values if v is not None]


# ---------- 纯 bar / 折线走 add_chart ----------

def test_bar_uses_native_chart():
    req = {
        "chart_type": "bar",
        "config": {"dimension": "平台"},
        "data": {
            "categories": ["a", "b"],
            "series": [{"name": "v", "kind": "bar", "unit": "yi", "data": [1.0, 2.0]}],
        },
    }
    blob = build_pptx(req)
    xml = _chart_xml(blob)
    assert "<c:barChart>" in xml
    assert "<c:lineChart>" not in xml
    assert _external_link_targets(blob) == []


# ---------- 校验 ----------

def test_rejects_unknown_chart_type():
    # v1.6 起 radar 已是合法类型，未知类型用 funnel 代表
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "funnel", "data": COMBO_REQUEST["data"]})


def test_rejects_combo_without_secondary():
    bad = {
        "chart_type": "combo",
        "data": {"categories": ["a"], "series": [{"name": "v", "kind": "bar", "data": [1.0]}]},
    }
    with pytest.raises(PptxValidationError):
        build_pptx(bad)


# ---------- HTTP 端点冒烟：返回 .pptx 文件流 ----------

def test_generate_pptx_endpoint_returns_file():
    client = TestClient(app)
    resp = client.post("/api/generate-pptx", json=COMBO_REQUEST)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert ".pptx" in resp.headers.get("content-disposition", "")
    # 魔数 PK\x03\x04
    assert resp.content[:2] == b"PK"
    # 产物可被 python-pptx 正常打开
    prs = Presentation(io.BytesIO(resp.content))
    assert sum(1 for sh in prs.slides[0].shapes if sh.has_chart) == 1


def test_generate_pptx_endpoint_bad_request():
    client = TestClient(app)
    # 完全未知的图型 → VALIDATION_FAILED/400
    resp2 = client.post("/api/generate-pptx", json={"chart_type": "funnel", "data": {}})
    assert resp2.status_code == 400
    assert resp2.json()["code"] == "VALIDATION_FAILED"
    # 结构非法（缺 data）→ VALIDATION_FAILED/400
    resp3 = client.post("/api/generate-pptx", json={"chart_type": "scatter"})
    assert resp3.status_code == 400
    assert resp3.json()["code"] == "VALIDATION_FAILED"


# ---------- v1.5 六图型覆盖（slope / scatter / pie） ----------

def test_slope_builds_line_markers_with_gap():
    req = {
        "chart_type": "slope",
        "data": {
            "categories": ["微信", "抖音", "快手"],
            "series": [
                {"name": "2024 MAU", "unit": "yi", "data": [13.9, 10.5, 7.2]},
                {"name": "2025 MAU", "unit": "yi", "data": [14.2, 11.7, None]},
            ],
        },
    }
    blob = build_pptx(req)
    xml = _chart_xml(blob)
    assert "<c:lineChart>" in xml
    assert '<c:dispBlanksAs val="gap"/>' in xml
    assert _external_link_targets(blob) == []
    prs = Presentation(io.BytesIO(blob))
    assert sum(1 for sh in prs.slides[0].shapes if sh.has_chart) == 1


def test_scatter_builds_and_drops_invalid_points():
    req = {
        "chart_type": "scatter",
        "data": {
            "categories": ["微信", "抖音", "快手", "微博"],
            "series": [
                {"name": "2025 MAU", "unit": "yi", "data": [14.2, 11.7, 7.0, 5.7]},
                {"name": "2025 DAU", "unit": "yi", "data": [None, 7.6, 4.0, 2.5]},
            ],
        },
    }
    blob = build_pptx(req)
    xml = _chart_xml(blob)
    assert "<c:scatterChart>" in xml
    # 微信 DAU=None 的点被整体剔除：xVal/yVal 各剩 3 个点
    assert xml.count('<c:ptCount val="3"') == 2
    assert _external_link_targets(blob) == []


def test_pie_builds_and_drops_null_slices():
    req = {
        "chart_type": "pie",
        "data": {
            "categories": ["微信", "抖音", "快手"],
            "series": [{"name": "2025 MAU", "unit": "yi", "data": [14.2, None, 7.0]}],
        },
    }
    blob = build_pptx(req)
    xml = _chart_xml(blob)
    assert "<c:pieChart>" in xml
    # 抖音扇区被剔除：缓存只剩 2 个分类
    assert xml.count("<c:pt idx=") >= 2 and "抖音" not in xml
    assert _external_link_targets(blob) == []


def test_rejects_new_type_shape_violations():
    # scatter 系列数 ≠ 2
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "scatter", "data": {
            "categories": ["a"], "series": [{"name": "x", "data": [1.0]}]}})
    # pie 系列数 ≠ 1
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "pie", "data": {
            "categories": ["a"], "series": [{"name": "x", "data": [1.0]}, {"name": "y", "data": [2.0]}]}})
    # slope 含 percent
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "slope", "data": {
            "categories": ["a", "b"],
            "series": [{"name": "p", "unit": "percent", "data": [0.1, 0.2]}]}})


# ---------- v1.6 新增七图型（hbar / area / stacked / waterfall / radar / donut / sunburst） ----------

def _series(name: str, data: list, unit: str = "yi") -> dict:
    return {"name": name, "unit": unit, "data": data}


def test_hbar_builds_bar_dir_bar():
    blob = build_pptx({"chart_type": "hbar", "data": {
        "categories": ["微信", "抖音"],
        "series": [_series("2025 MAU", [14.2, 11.7])],
    }})
    xml = _chart_xml(blob)
    assert "<c:barChart>" in xml
    assert '<c:barDir val="bar"/>' in xml  # 横向条形
    assert _external_link_targets(blob) == []


def test_area_builds_area_chart():
    blob = build_pptx({"chart_type": "area", "data": {
        "categories": ["Q1", "Q2", "Q3"],
        "series": [_series("营收", [1.0, None, 3.0])],  # null 空点保留（C-3）
    }})
    xml = _chart_xml(blob)
    assert "<c:areaChart>" in xml
    _, _, charts = _charts(blob)
    values = list(charts[0].series[0].values)
    assert values[1] is None  # 未转 0
    assert _external_link_targets(blob) == []


def test_stacked_builds_stacked_grouping():
    blob = build_pptx({"chart_type": "stacked", "data": {
        "categories": ["Q1", "Q2"],
        "series": [_series("移动", [3.0, 4.0]), _series("PC", [1.5, 2.0])],
    }})
    xml = _chart_xml(blob)
    assert "<c:barChart>" in xml
    assert '<c:grouping val="stacked"/>' in xml
    _, _, charts = _charts(blob)
    assert len(charts[0].series) == 2
    assert _external_link_targets(blob) == []


def test_waterfall_builds_transparent_base():
    blob = build_pptx({"chart_type": "waterfall", "data": {
        "categories": ["期初", "迁移", "流失", "期末调整"],
        "series": [_series("规模变化", [10.0, None, -3.0, 1.0])],
    }})
    xml = _chart_xml(blob)
    assert "<c:barChart>" in xml
    assert '<c:grouping val="stacked"/>' in xml  # R-5：COLUMN_STACKED 等价
    assert "<a:noFill/>" in xml  # 底座系列透明
    _, _, charts = _charts(blob)
    chart = charts[0]
    assert len(chart.series) == 2  # 底座 + 增量
    # 底座 = min(前值累计, 后值累计)（§6 M4 映射表口径）：[0, 0(None占位), min(10,7), min(7,8)]
    assert list(chart.series[0].values) == [0.0, 0.0, 7.0, 7.0]
    # 增量取绝对值（负值翻转防回落零轴）；None 空点保留不转 0（C-3）
    assert list(chart.series[1].values) == [10.0, None, 3.0, 1.0]
    assert _external_link_targets(blob) == []


def test_radar_builds_radar_markers():
    blob = build_pptx({"chart_type": "radar", "data": {
        "categories": ["增长", "留存", "变现", "传播"],
        "series": [
            _series("产品A", [8.0, 6.5, 7.0, 5.0], unit="count"),
            _series("产品B", [6.0, 7.5, 5.5, 8.0], unit="count"),
            _series("产品C", [7.0, 7.0, 6.0, 6.5], unit="count"),
        ],
    }})
    xml = _chart_xml(blob)
    assert "<c:radarChart>" in xml
    _, _, charts = _charts(blob)
    assert len(charts[0].series) == 3
    assert _external_link_targets(blob) == []


def test_donut_builds_doughnut_chart():
    blob = build_pptx({"chart_type": "donut", "data": {
        "categories": ["微信", "抖音", "快手"],
        "series": [_series("时长占比", [5.0, 4.0, 1.0])],
    }})
    xml = _chart_xml(blob)
    assert "<c:doughnutChart>" in xml
    assert _external_link_targets(blob) == []


def test_sunburst_degrades_to_doughnut_and_drops_null():
    # R-5：python-pptx 无 sunburst 类型，导出降级为 DOUGHNUT 近似；null 扇区剔除（C-3）
    blob = build_pptx({"chart_type": "sunburst", "data": {
        "categories": ["微信", "抖音", "快手"],
        "series": [_series("份额", [5.0, None, 3.0])],
    }})
    xml = _chart_xml(blob)
    assert "<c:doughnutChart>" in xml
    assert "抖音" not in xml
    assert _external_link_targets(blob) == []


def test_rejects_v16_shape_and_percent_violations():
    # donut/sunburst/waterfall 系列数 ≠ 1
    for t in ("donut", "sunburst", "waterfall"):
        with pytest.raises(PptxValidationError):
            build_pptx({"chart_type": t, "data": {
                "categories": ["a", "b"],
                "series": [_series("x", [1.0, 2.0]), _series("y", [3.0, 4.0])]}})
    # stacked 系列数 < 2 / 单位不一致
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "stacked", "data": {
            "categories": ["a"], "series": [_series("x", [1.0])]}})
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "stacked", "data": {
            "categories": ["a"],
            "series": [_series("x", [1.0]), _series("y", [2.0], unit="wan")]}})
    # radar 系列数 < 3 / 单位不一致
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "radar", "data": {
            "categories": ["a"],
            "series": [_series("x", [1.0]), _series("y", [2.0])]}})
    with pytest.raises(PptxValidationError):
        build_pptx({"chart_type": "radar", "data": {
            "categories": ["a"],
            "series": [_series("x", [1.0]), _series("y", [2.0]), _series("z", [3.0], unit="wan")]}})
    # 新类型（除 hbar/area 外）禁 percent：radar / stacked / waterfall 各验一例
    for t, series in (
        ("radar", [_series("a", [0.1], "percent"), _series("b", [0.2], "percent"), _series("c", [0.3], "percent")]),
        ("stacked", [_series("a", [0.1], "percent"), _series("b", [0.2], "percent")]),
        ("waterfall", [_series("a", [0.1], "percent")]),
    ):
        with pytest.raises(PptxValidationError):
            build_pptx({"chart_type": t, "data": {"categories": ["x"], "series": series}})


# ---------- v1.7 放映动效版（SPEC §6 M4 规则 8 / R-6，验收 A-4.10） ----------

def _slide_xml(blob: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        return zf.read("ppt/slides/slide1.xml").decode("utf-8")


# chart_type -> (最小合法请求, 期望 animEffect filter, 期望 bldChart bld)（§6 M4 规则 8 映射）
_ANIM_CASES = {
    "bar": ({"chart_type": "bar", "data": {"categories": ["a", "b"],
            "series": [_series("x", [1.0, 2.0])]}}, "wipe(up)", "ptInCategory"),
    "hbar": ({"chart_type": "hbar", "data": {"categories": ["a", "b"],
             "series": [_series("x", [1.0, 2.0])]}}, "wipe(r)", "ptInCategory"),
    "line": ({"chart_type": "line", "data": {"categories": ["a", "b"],
             "series": [_series("x", [1.0, None])]}}, "wipe(r)", "ptInSeries"),
    "area": ({"chart_type": "area", "data": {"categories": ["a", "b"],
             "series": [_series("x", [1.0, 2.0])]}}, "wipe(up)", "ptInCategory"),
    "combo": (COMBO_REQUEST, "wipe(up)", "ptInCategory"),
    "stacked": ({"chart_type": "stacked", "data": {"categories": ["a", "b"],
                "series": [_series("x", [1.0, 2.0]), _series("y", [3.0, 4.0])]}}, "wipe(up)", "ptInCategory"),
    "slope": ({"chart_type": "slope", "data": {"categories": ["a", "b"],
              "series": [_series("x", [1.0, 2.0]), _series("y", [2.0, 3.0])]}}, "wipe(r)", "ptInSeries"),
    "scatter": ({"chart_type": "scatter", "data": {"categories": ["a", "b"],
                "series": [_series("x", [1.0, 2.0]), _series("y", [3.0, 4.0])]}}, "fade", "ptInSeries"),
    "waterfall": ({"chart_type": "waterfall", "data": {"categories": ["a", "b", "c"],
                  "series": [_series("x", [10.0, -3.0, 1.0])]}}, "wipe(up)", "ptInCategory"),
    "radar": ({"chart_type": "radar", "data": {"categories": ["a", "b", "c"],
              "series": [_series("x", [1.0, 2.0, 3.0], "count"), _series("y", [2.0, 3.0, 1.0], "count"),
                         _series("z", [3.0, 1.0, 2.0], "count")]}}, "fade", "ptInSeries"),
    "pie": ({"chart_type": "pie", "data": {"categories": ["a", "b"],
            "series": [_series("x", [1.0, 2.0])]}}, "wheel(1)", "ptInSeries"),
    "donut": ({"chart_type": "donut", "data": {"categories": ["a", "b"],
              "series": [_series("x", [1.0, 2.0])]}}, "wheel(1)", "ptInSeries"),
    "sunburst": ({"chart_type": "sunburst", "data": {"categories": ["a", "b"],
                 "series": [_series("x", [1.0, 2.0])]}}, "wheel(1)", "ptInSeries"),
}


@pytest.mark.parametrize("chart_type", sorted(_ANIM_CASES))
def test_animate_injects_timing_per_type(chart_type: str):
    req, effect, build = _ANIM_CASES[chart_type]
    blob = build_pptx({**req, "animate": True})
    xml = _slide_xml(blob)
    # timing 骨架 + 进入动画效果 + 分段构建维度
    assert "<p:timing" in xml
    assert f'<p:animEffect transition="in" filter="{effect}">' in xml
    assert f'<a:bldChart bld="{build}"' in xml
    # target 是图表 graphicFrame 的 spid
    prs = Presentation(io.BytesIO(blob))
    frames = [sh for sh in prs.slides[0].shapes if sh.has_chart]
    assert len(frames) == 1
    assert f'<p:bldGraphic spid="{frames[0].shape_id}" grpId="0">' in xml
    # 动画不破坏 C-1/C-2：图表仍是原生可编辑对象且无外部链接
    assert _external_link_targets(blob) == []


def test_default_export_has_no_timing():
    # animate 缺省 / false：slide 不得出现 <p:timing>（行为与 v1.6 完全一致）
    for req in (COMBO_REQUEST, {**COMBO_REQUEST, "animate": False}):
        xml = _slide_xml(build_pptx(req))
        assert "<p:timing" not in xml
        assert "<p:bldLst>" not in xml


def test_generate_pptx_endpoint_animated_filename():
    client = TestClient(app)
    resp = client.post("/api/generate-pptx", json={**COMBO_REQUEST, "animate": True})
    assert resp.status_code == 200
    disposition = resp.headers.get("content-disposition", "")
    assert "chart-animated" in disposition and disposition.endswith('.pptx"')
    assert "<p:timing" in _slide_xml(resp.content)
    # 标准版文件名不变
    resp2 = client.post("/api/generate-pptx", json=COMBO_REQUEST)
    disposition2 = resp2.headers.get("content-disposition", "")
    assert "chart-2" in disposition2 and "animated" not in disposition2
