"""M4 放映动效注入（SPEC §6 M4 规则 8，v1.7 引入 / v1.8 修正枚举与粒度 / R-6）。

python-pptx 无动画 API，采用 ECMA-376 标准 ``<p:timing>`` + ``<a:bldChart>`` XML 模板注入：

- 单个 clickEffect 进入动画（``<p:set>`` 置可见 + ``<p:animEffect transition="in">``，dur=500ms）；
- ``<p:bldLst>/<p:bldGraphic>/<p:bldSub>/<a:bldChart bld="...">`` 定义分段构建维度，由播放器展开为
  逐数据点出现；``bld`` 必须是 ST_ChartBuildStep 合法枚举（category/ptInCategory/series/ptInSeries/
  allPts/gridLegend）——v1.7 误用的 bySeries 等非法值会被播放器忽略而整图进入（v1.8 修正）；
- v1.8 起一律按数据点构建（柱族 ptInCategory、线/饼族 ptInSeries），放映时「图表本身」逐点变化；
- 动画只是附加的 timing 层，不改写 chart part，C-1/C-2/C-3/C-4 全部不受影响；
- 仅在请求 ``animate=true`` 时注入；缺省/false 时 slide 不出现 ``<p:timing>``（行为同 v1.6）。
"""
from __future__ import annotations

from lxml import etree
from pptx.slide import Slide

# chart_type -> (animEffect filter, bldChart bld, presetID)
# bld 为 ECMA-376 ST_ChartBuildStep 合法枚举；presetID 仅影响动画窗格显示名（R-6）。
# v1.8：一律按数据点构建（ptInCategory=逐类各点 / ptInSeries=逐系列逐点），单步 500ms。
_ANIM_MAP: dict[str, tuple[str, str, int]] = {
    "bar": ("wipe(up)", "ptInCategory", 22),
    "stacked": ("wipe(up)", "ptInCategory", 22),
    "area": ("wipe(up)", "ptInCategory", 22),
    "combo": ("wipe(up)", "ptInCategory", 22),
    "waterfall": ("wipe(up)", "ptInCategory", 22),
    "hbar": ("wipe(r)", "ptInCategory", 22),
    "line": ("wipe(r)", "ptInSeries", 22),
    "slope": ("wipe(r)", "ptInSeries", 22),
    "radar": ("fade", "ptInSeries", 10),
    "scatter": ("fade", "ptInSeries", 10),
    "pie": ("wheel(1)", "ptInSeries", 21),
    "donut": ("wheel(1)", "ptInSeries", 21),
    "sunburst": ("wheel(1)", "ptInSeries", 21),
}

_DURATION_MS = 500

_TEMPLATE = """\
<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:tnLst>
    <p:par>
      <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
        <p:childTnLst>
          <p:seq concurrent="1" nextAc="seek">
            <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
              <p:childTnLst>
                <p:par>
                  <p:cTn id="3" fill="hold">
                    <p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>
                    <p:childTnLst>
                      <p:par>
                        <p:cTn id="4" fill="hold">
                          <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                          <p:childTnLst>
                            <p:par>
                              <p:cTn id="5" presetID="{preset}" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="clickEffect">
                                <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                                <p:childTnLst>
                                  <p:set>
                                    <p:cBhvr>
                                      <p:cTn id="6" dur="1" fill="hold">
                                        <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                                      </p:cTn>
                                      <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>
                                      <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                                    </p:cBhvr>
                                    <p:to><p:strVal val="visible"/></p:to>
                                  </p:set>
                                  <p:animEffect transition="in" filter="{filter}">
                                    <p:cBhvr>
                                      <p:cTn id="7" dur="{dur}"/>
                                      <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>
                                    </p:cBhvr>
                                  </p:animEffect>
                                </p:childTnLst>
                              </p:cTn>
                            </p:par>
                          </p:childTnLst>
                        </p:cTn>
                      </p:par>
                    </p:childTnLst>
                  </p:cTn>
                </p:par>
              </p:childTnLst>
            </p:cTn>
            <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
            <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
          </p:seq>
        </p:childTnLst>
      </p:cTn>
    </p:par>
  </p:tnLst>
  <p:bldLst>
    <p:bldGraphic spid="{spid}" grpId="0">
      <p:bldSub>
        <a:bldChart bld="{bld}" animBg="1"/>
      </p:bldSub>
    </p:bldGraphic>
  </p:bldLst>
</p:timing>"""


def inject_chart_animation(slide: Slide, spid: int, chart_type: str) -> None:
    """向 slide 注入图表进入动画（SPEC §6 M4 规则 8）。

    - ``spid``：图表 graphicFrame 的 shape_id；
    - ``chart_type``：决定效果（wipe/fade/wheel）与分段维度（ptInCategory/ptInSeries）；
    - 未知类型退化为 fade + series（防御性，正常入参已经 §5.6 校验）。
    """
    effect, build, preset = _ANIM_MAP.get(chart_type, ("fade", "series", 10))
    xml = _TEMPLATE.format(spid=spid, filter=effect, bld=build, dur=_DURATION_MS, preset=preset)
    timing = etree.fromstring(xml.encode("utf-8"))
    # <p:sld> 子元素顺序为 cSld, clrMapOvr, transition?, timing?, extLst?：python-pptx 新建
    # 页面只有 cSld + clrMapOvr，直接 append 即满足 schema 顺序（R-6）。
    slide._element.append(timing)  # noqa: SLF001 — python-pptx 无动画 API，按 R-6 注入
