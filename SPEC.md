# SPEC.md — 智能数据图表 PPT 生成器

> 版本：v1.18 ｜ 状态：M1/M2 已实现，M3 已实现（推荐产出随界面语言五语言原生 zh/en/fr/de/es），M4 单图 PPT 导出已实现（十三图型全覆盖、可选原生数据标签 show_labels），动效产物支持直出 GIF（实底跟随主题 / 可选二元透明）与嵌入 pptx 两种形态
> 读者：AI 编程工具 / 实现工程师。实现过程中任何与本文档冲突的决策，必须先回写本文档再编码。

**修订记录**
- v1.18：**推荐产出扩为五语言原生**（替代 v1.17 的「非 zh 一律英文」回退）。①`lang` 归一化改为：zh/en/fr/de/es **直通**，仅非法/缺省值回退 `"en"`。②**LLM 路径**：fr/de/es 复用英文 system prompt + 追加一条目标语言指令（"EXCEPTION to rule 8: write BOTH title and reasoning in French/German/Spanish"，并重申列名/维度值保持原文不翻译）——主流 LLM 多语言输出质量可靠，无需维护三套完整 prompt；user prompt 骨架非 zh 一律英文。③**降级路径**：启发式降级标题模板（combo/line/area/stacked/slope/radar/bar/donut/scatter/pie 十组）、缺失系列提示语、降级说明、无数值列错误信息全部扩为 fr/de/es 三套（模板常量 `FALLBACK_TITLES` 五语言字典）；分隔符口径 zh 用全角「；：」，其余一律半角 "; " / ": "。④前端「数据不完整」徽标尾缀匹配同步扩为五语言（大小写不敏感）。⑤列名/categories/series.name 保持用户原文的约束（v1.14）不变。
- v1.17：**出海多语言**。①前端界面语言由 zh/en 扩为**六语言** zh/en/fr/de/es（DESIGN.md 多语言节同步）；初始语言改为**检测浏览器语言**（`navigator.language` 前缀匹配 zh/fr/de/es，其余一律英文兜底——面向海外默认英文而非中文），用户手动切换后存 `localStorage dc-lang` 优先；顶栏语言二态切换按钮改为六语言下拉。②`/api/recommend` 的 `lang` 归一化规则修订：v1.14「缺省/非法值回退 zh」改为**仅 `"zh"` 走中文，其余一切取值（含 fr/de/es 及非法值）统一回退 `"en"`**（出海产品默认回退应为英文；欧洲语言用户的推荐文本以英文输出，远比中文可读）。LLM prompt、降级模板、缺失提示语仍维护 zh/en 两套，欧洲语言经回退复用英文套。③列名/维度值等数据原文不翻译的约束（v1.14）不变。
- v1.16：①标准 PPTX 导出支持**数据标签开关**。GeneratePptxRequest 顶层新增可选 `show_labels`（默认 false）；为 true 时给原生可编辑 Chart 写入 `<c:dLbls>`：柱/条/线/面积/堆叠/斜率显值，饼/圆环/旭日显「类别名+值」，瀑布仅「增量」系列显值（透明底座不加），散点/雷达因 python-pptx 原生 dLbls 支持差而安全跳过（不报错）；数字格式沿用各序列 unit 轴口径（percent=`0.0%`、yi/wan 带单位、count=`General`）。标签是原生图表元素、在 PPT/WPS 可继续编辑，C-1 不违反。「显示数据标签」开关自此同时作用于预览、GIF 与标准 PPTX。②修复降级标题泄漏内部单位码：line/area/stacked/slope/radar 启发式标题不再拼接裸 unit（曾出现「产品线各期yi指标趋势」），单位只保留在坐标轴与数据标签上。
- v1.15：「显示数据标签」开关经 App→PreviewPanel→ChartCard 透传，预览卡片与 GIF 采帧共用 `applyDataLabels`，勾选即显、取消即隐（所见即所得）；标准 pptx 当时仍不带标签（v1.16 补齐）。
- v1.14：**推荐产出跟随界面语言**。`/api/recommend` 入参在裸 SemanticTable 基础上新增可选 `lang`（`"zh"`（默认）/`"en"`；兼容旧调用，缺省/非法值回退 zh）。`lang="en"` 时：LLM system prompt 指示 **title 与 reasoning 一律用英文输出**；LLM 不可用时的启发式降级标题/说明、缺失系列固定提示语均切换为英文模板（中文：「该系列数据不完整，建议不纳入」；英文：`"Incomplete data for this series; exclude with caution"`；降级说明英文：`"Heuristic recommendation (LLM unavailable or incomplete)"`）。**列名、categories（维度取值）、series.name 等数据驱动内容始终保持用户原文不翻译**（C-5 投影依据，翻译会破坏列引用匹配）；翻译范围仅限 title/reasoning 等模型/模板生成的说明性文本。前端按当前 i18n 语言在推荐请求中携带 `lang`。
- v1.13：GIF 采帧体验两处修订。①**浅色主题实底由浅蓝 `#f4f8fc` 改为纯白 `#ffffff`**（用户反馈：贴 PPT 白底场景不应带颜色）。②采帧新增可选**数据标签**（GIF 为位图、导出后不可编辑，数值显示与否须在导出期决定）：前端导出区加「显示数据标签」开关，仅作用于动效 GIF 采帧（预览与标准 pptx 不变）；实现为 `specToOption` 的导出后处理器 `applyDataLabels(option, spec, theme)`——按 series 名匹配单位（`valueFormatter` 口径：percent 0.112→11.2%、亿/万追加单位），waterfall 显示**带正负的真实增量**而非 abs 堆叠值并跳过透明底座（`__base__`），pie/donut/sunburst 为「名称: 值」，柱/条/线/面积/堆叠/组合/散点/雷达按图型选 label 位置（hbar→right、stacked→inside、其余→top）。
- v1.12：动效产物**主形态从「嵌入 pptx」改为「直出 .gif 文件」**，并新增透明背景选项。新增端点 `POST /api/generate-gif`：入参与 §5.6a 相同（`{title?（忽略，GIF 无标题）, frames, frame_ms?, transparent?}`），直接返回 `image/gif`（`Content-Disposition: attachment; filename="chart-{ts}.gif"`，GIF89a、loop=0）。前端动效按钮从「导出动效版 pptx」改为「导出动效 GIF」，逐图下载 .gif；不再默认套一层 pptx。`transparent`（默认 false）：①false=**跟随当前 UI 主题的实底色**（前端采帧时铺深色/浅色实底，GIF 不支持半透明、透明区域会被填黑）；②true=**二元透明**——GIF 仅支持每像素全透/不透（无 alpha 半透明），线条与文字抗锯齿边缘、面积图半透明填充、深色主题发光阴影会被硬切（可能出现毛边），且图表内文字/坐标色随主题（深色主题浅字贴到白底上不可见），**透明底仅适用于贴到与主题同色的背景**，作为可选项提供，默认实底。实现上透明模式保留 RGBA 合成（`disposal=2` 防帧残影、`transparency` 索引）。嵌入 pptx 的 `POST /api/generate-animated-pptx`（§5.6a）保留但前端不再主推；两端点共享同一 GIF 合成核心。标准静态导出 `/api/generate-pptx`（原生可编辑 Chart，C-1）不变。
- v1.11：放映动效**路线切换——放弃 OOXML 原生图表动画，改走 GIF 动图路线**（R-6 改判）。v1.7~v1.10 四个版本基于 `<p:timing>`/oleChartEl 的原生图表分段动画在 WPS 实测全部失败（整图进入或完全无动画），且沙箱无法运行 WPS 验证、只能盲改，定论：**WPS 对图表子元素动画支持不可靠，此路不通**。新方案：前端用离屏 ECharts 实例播放绘制动画并定时采帧（canvas.toDataURL），将帧序列 POST 到新端点 `POST /api/generate-animated-pptx`；后端用 PIL 把多帧合成为动态 GIF（`save_all` + `duration` + `loop=0`），再以 `add_picture` 嵌入 pptx 全幅呈现。PPT/WPS 放映对 GIF 动图支持稳定，所见即所得。动效版是**独立产物**（文件名 `chart-animated-{ts}.pptx`），与标准导出互不影响；GIF 为位图不可编辑，但这**不违反 C-1**——C-1 约束的是标准导出端点 `/api/generate-pptx`（仍输出原生可编辑 Chart），动效版属用户显式选择的另一产物。标准导出端点移除 `animate` 入参，恢复为纯静态原生图表（不再有 p:timing 注入路径）。
- v1.10：放映动效**第三版修正**——修复 v1.9 引入的致命 XML 合法性错误：v1.9 给 afterEffect 段的起始条件用了**不存在的元素 `<p:beginCondLst>`**（OOXML 时间节点只有 `<p:stCondLst>`/`<p:endCondLst>`），WPS 解析到非法节点将整段 `<p:timing>` 丢弃 → 放映**完全没有动画**。v1.10 改为合法形式：首段 `clickEffect`（`<p:stCondLst><p:cond delay="indefinite"/>` 等待点击），其余段 `afterEffect` + `<p:stCondLst><p:cond delay="0"/></p:stCondLst>`（afterEffect 语义即「上一动画之后」自动接续，无需逐段点击）。oleChartEl 多段结构（v1.9）保留不变。
- v1.9：放映动效**第二版修正**——v1.7/v1.8 注入的 `<a:bldChart bld>` 只解决「动画窗格里的构建声明」，但真正决定播放分段的是 mainSeq 中**每个动画 effect 目标里的 `<p:oleChartEl type="..." lvl="N"/>`**（`spTgt` 的子元素，指定该段作用到第 N 个类别/系列）。此前所有 effect 目标都是整图 spid、无 oleChartEl，WPS 实测只能整图进入。v1.9 改为**为每个类别（或系列）生成一个独立 par/clickEffect 段**，每段 target 为 `spTgt[spid] > oleChartEl`（笛卡尔柱/条/堆叠/面积/瀑布/组合/雷达=`type="category" lvl=类别下标`，折线/斜率/散点=`type="series" lvl=系列下标`，饼/圆环/旭日=`type="series" lvl=0` 配合 wheel 逐扇区由 bldChart 表达），首段点击触发、其余段「上一动画之后」自动接续（WPS 无需逐次点击）；`<a:bldChart bld>` 同步用 `category`/`series` 粗粒度（`ptIn*` 逐点粒度对多系列柱图的 oleChartEl 段结构要求更高、WPS 兼容更差，弃用）。人工 WPS 验证（A-4.11）确认后关闭。
- v1.8：两处修正——①修复降级（heuristic fallback）路径面积图序列 `kind` 误置 `bar` 导致前端预览把面积图渲染为柱状图的问题，面积图序列 `kind` 恒为 `line`（降级路径与 LLM 投影路径一致）；②动效注入的 `<a:bldChart bld>` 枚举值修正：v1.7 使用的 `bySeries`/`byCategory`/`byPtInSeries` 非 ECMA-376 合法值（`ST_ChartBuildStep` 实际枚举为 `category`/`ptInCategory`/`series`/`ptInSeries`/`allPts`/`gridLegend`），非法值会被播放器忽略分段构建、退化为整图进入；同时按产品诉求将构建粒度从按系列改为**按数据点**（柱/条/堆叠/面积/瀑布/组合=`ptInCategory` 逐类各点，折线/斜率/雷达/散点/饼/圆环/旭日=`ptInSeries` 逐点），单步时长 750ms→500ms，实现「图表本身逐点变化」的放映效果。
- v1.7：新增**放映动效版导出**（独立功能，标准导出行为不变）：GeneratePptxRequest 新增可选 `animate`（默认 false）；为 true 时在 slide XML 注入 `<p:timing>` 进入动画 + `<p:bldLst>` 的 `<a:bldChart>` 分段构建定义，放映时图表按图型映射逐系列/逐类别/逐扇区出现（wipe / wheel / fade，R-6）。动画只是附加的 timing 层，不改写 chart part，图表仍为原生可编辑 Chart（C-1 不违反）；动效版文件名 `chart-animated-{ts}.pptx` 与标准版区分；前端导出区新增「导出动效版」独立按钮（不混入标准导出）。python-pptx 无动画 API，采用 ECMA-376 标准 XML 模板注入（R-6），WPS/Office 双端人工验证列入 A-4.11。
- v1.6：图表类型从六种扩展为**十三种**——新增 `hbar`（水平条形）、`stacked`（堆叠柱）、`donut`（圆环）、`area`（面积）、`waterfall`（瀑布）、`radar`（雷达）、`sunburst`（旭日）；C-5 枚举、§5.4 Schema、V-2、§5.5 LLM 契约、§6 M4 映射表同步扩展，并新增不变式 V-9~V-12。导出等价说明：**瀑布图无 python-pptx 原生枚举，以 `COLUMN_STACKED`（透明底座系列 + 增量系列）等价实现**，仍为原生可编辑 Chart（C-1 不违反）；**旭日图 python-pptx 无对应类型，导出降级为 `DOUGHNUT`**（近似表达，R-5）；圆环=`DOUGHNUT`、面积=`AREA`、雷达=`RADAR_MARKERS`、水平条形=`BAR_CLUSTERED`、堆叠=`COLUMN_STACKED`（均原生）。新不变式：V-9（stacked ≥2 个同单位 measure 序列）、V-10（waterfall 恰好 1 个 measure 序列）、V-11（radar ≥3 个同单位 measure 序列、禁 percent）、V-12（donut/sunburst 同 V-8 pie 口径）。新类型 percent 口径：`stacked`/`waterfall`/`radar`/`donut`/`sunburst` 禁 percent；percent 仅允许 `bar`/`hbar`/`line`/`area`/`combo`。
- v1.5：M4 导出能力从「bar / line / combo」扩展为**六种图型全覆盖**——`slope` 按两期 `LINE_MARKERS`（含 gap 断线）实现，`scatter` 用 `XyChartData`（无效点剔除），`pie` 用 `PIE`（null 扇区剔除）（R-4 落定）；`UNSUPPORTED_CHART` 错误码随之移除（未知类型仍走 `VALIDATION_FAILED`）；新增入参校验：scatter 恰好 2 系列、pie 恰好 1 系列、slope/scatter/pie 禁止 percent 系列（V-9/V-10 与 M3 口径一致）。产品行为变更：前端「解析数据」与「生成候选图表」合并为一次点击（解析成功后自动调用推荐），导出不再跳过任何已选图型。
- v1.4：M4 落地为**单图导出端点 `POST /api/generate-pptx`**（入参 `{chart_type, config, data}`，出参 `.pptx` 文件流，见 §5.6）；原多图 deck 端点 `/api/generate`（GenerateRequest，含 table/charts/options）降级为后续里程碑（MVP 之后），契约保留在 §5.6b 暂不实现。M0 门禁已通过（`backend/spikes/ablechart_spike.py`）：ablechart 0.2.0 `create_combo_chart(slide, df, categories_col, series_config=[{key,name,type,axis}], polish=False)` 产出原生 barChart+lineChart+双 valAx，内嵌 workbook 为内部 `package` 关系（`TargetMode` 非 External），**无外部数据链接**；python-pptx 1.0.2 无公共 BreakLink API（R-2），C-2 以「遍历 chart part relationships，删除所有 is_external 关系 + 移除 `<c:externalData>` 空引用」等价实现；python-pptx 生成的 line 图 `dispBlanksAs` 默认即 `gap`（空点断线，C-3），builder 仍显式置 `gap` 兜底；次轴数字格式 `0.0%`、主轴 tick label 格式 `0.0"亿"`（yi）通过 chart XML 设置；combo 的 `chart.chart_type` 读回为 COLUMN_CLUSTERED（多 plot 混合图无独立枚举），验收以 chart XML 同时含 `barChart`+`lineChart` 且 valAx=2 为准。
- v1.3：图表类型恢复为六种（bar / line / combo / slope / scatter / pie，v1.1 的 MVP 三类型收窄撤销）；LLM 原始输出契约改为**裸 JSON 数组**，每项字段为 `chart_type` / `title` / `config` / `reasoning`（§5.5）；ChartSpec 的推荐理由字段 `rationale` 统一改名 `reasoning`，新增 `semantic_layer` 字段；M3 新增「趋势 / 体量对比 / 变化率」三语义层覆盖要求（含降级补齐）；明确缺失系列由后端确定性追加「该系列数据不完整，建议不纳入」；LLM 容错重试措辞明确为「最多调用 2 次（失败后重试 1 次）」；恢复 V-5~V-8（scatter/slope/pie）不变式与 §8 对应前端映射。
- v1.2：percent 数值形态统一为小数（解析阶段 `+11.2% → 0.112`，M2/M3/ECharts/pptx 全链路一致，M4 不再换算）；缺失标记词表新增「无」；percent 判定新增「列名含 %」规则；M1 parser / M2 semantic 与 `/api/parse` 落地；勘误 §5.3 期望输出 distinct_count（以 §12 夹具实际值为准：梯队=4、平台态势=6，v1.3 再次校正）。
- v1.1：MVP 范围收窄（chart_type 仅保留 bar / line / combo，删除 slope / scatter / pie）；新增 §5.1 百分比数值转换表；同列混合单位改为不自动折算（MVP 已知限制）；测试夹具扩为 6 行（含负同比 / DAU 全缺失 / DAU 完整 / MAU 下降）；实施顺序新增 M0 ablechart 可行性验证。
- v1.0：初版。

---

## 1. 产品目标与范围

### 1.1 目标
用户输入一份不规整的数据（文本粘贴或 CSV/Excel 上传），系统自动完成：

1. 解析并规整数据；
2. 分析列语义（维度 / 数值 / 百分比 / 备注）；
3. 调用 LLM 推荐多种图表方案，前端以 ECharts 渲染候选预览；
4. 用户选定后导出 `.pptx`，其中所有图表为 **原生 Chart 对象**，可在 WPS / PowerPoint 中**双击编辑数据**。

### 1.2 范围说明（MVP）
- **支持十三种图表类型（v1.6）：`bar`、`hbar`、`line`、`area`、`combo`、`stacked`、`slope`、`scatter`、`waterfall`、`radar`、`pie`、`donut`、`sunburst`。** 全部参与推荐、预览与 M4 PPT 导出；瀑布/旭日的导出等价与降级规则见 §6（M4 映射表）与 R-5，任何进一步降级必须先回写 SPEC。另提供独立的**动效产物**（GIF 路线，v1.11 引入 / v1.12 直出 .gif 为主、可选嵌入 pptx；支持跟随主题实底或二元透明背景，见 §5.6a/§6a；位图产物，不影响 C-1）。
- M3 每次推荐**至少覆盖三个语义层**：趋势（trend）、体量对比（comparison）、变化率（rate），见 §6 M3 规则 4。

### 1.3 非目标（Out of Scope）
- 六种类型之外的图表（面积图、雷达图、箱线图、热力图等）
- 用户系统 / 多租户 / 历史记录持久化
- PPT 模板市场、在线协同编辑
- 图表以 PNG/SVG 图片形式导出（与核心约束 C-1 冲突，明确禁止）
- 国际化（界面仅中文）

---

## 2. 技术栈（锁定，禁止更换）

| 层 | 技术 | 用途 |
|---|---|---|
| 前端 | React + TypeScript + ECharts | 数据输入、候选图表预览、选择与导出 |
| 后端 | FastAPI + Python | API 编排、模块承载 |
| 数据解析 | pandas | CSV/Excel/文本解析与规整 |
| 图表推荐 | LLM API（OpenAI 兼容协议） | 语义到图表类型的推荐，输出严格 JSON |
| PPT 生成 | python-pptx + ablechart | 原生图表写入；组合图用 `ablechart.create_combo_chart` |

---

## 3. 核心约束（C-1 ~ C-5，不可违反）

> 每条约束附**实现要求**与**验证方式**。验收测试必须覆盖验证方式。

### C-1 原生图表，禁止图片嵌入
- **要求**：最终写入 pptx 的所有图表，必须通过 python-pptx 的 `add_chart` 或 ablechart 的 `create_*_chart` 创建。**禁止**将 ECharts 截图、matplotlib 图片等以图片形式嵌入。
- **验证**：解压产物 `.pptx`，每张图表存在对应的 `ppt/charts/chartN.xml`；`ppt/media/` 中不存在任何作为图表主体的图片文件。

### C-2 断开外部数据链接
- **要求**：保存前遍历所有 slide 中 `has_chart` 为 True 的 shape，若其 chart_data 的 `IsLinked` 为 True，调用 `BreakLink()`。目标：WPS 中双击图表不出现「链接文件不可用」。若 python-pptx 当前版本无公共 BreakLink API，则以操作 chart XML / relationship 的等价方式实现（见 §13 风险项 R-2）。
- **验证**：解压产物，所有 `chartN.xml` 中的 `c:externalData` 要么不存在，要么其 relationship 指向包内嵌入的工作簿（internal part），**不得**存在指向外部文件路径的 relationship。人工验收：WPS 双击图表直接打开内嵌数据表。

### C-3 缺失值语义保留
- **要求**：缺失值（如「未披露」「无」「—」「N/A」、空串，以及 §5.0 混合单位规则下未折算的单元格）在解析阶段（M2）映射为 Python `None`，API 序列化为 JSON `null`，写入图表时留空（空数据点：line 断线、bar 缺柱）。**全链路任何环节不得将其转为 0。**
- **验证**：单元测试断言样例数据中微信 / 小红书 DAU 为 `null`；解压产物检查对应图表 XML 中该数据点的 `c:v` 为空/缺失，而非 `0`。

### C-4 百分比列独立识别
- **要求**：百分比列（同比、增速等带 `%` 的列，或列名含 `%` 的数值列）单独识别，`role=percent`、`unit=percent`，**不得**与亿级数值（`unit=yi`）混用同一主轴。组合图中 percent 序列必须挂副轴（`axis=secondary`）。各层数值形态严格遵循 §5.1 百分比数值转换表。
- **验证**：M2 输出中「同比」列 `unit=percent` 且解析值为 `0.112`（非 `"11.2%"` 字符串、非 `11.2`）；M3 输出的所有 ChartSpec 通过不变式校验 V-3（见 §5.4）；M4 产物中该序列写入值与 JSON 一致（`0.112`）且轴格式含 `%`。

### C-5 LLM 推荐输出强约束
- **要求**：LLM 推荐的图表类型限定在十三种（v1.6）：`bar`、`hbar`、`line`、`area`、`combo`、`stacked`、`slope`、`scatter`、`waterfall`、`radar`、`pie`、`donut`、`sunburst`。输出必须是**严格 JSON 数组**（裸数组文本，无 Markdown 代码围栏、无解释性前后缀；元素结构见 §5.5：`chart_type` / `title` / `config` / `reasoning`）。LLM **只输出列引用与图表配置，不输出数据值**——数据由后端从 SemanticTable 投影填充，防止 LLM 编造数字。
- **验证**：LLM 原始响应先做容错 JSON parse（先直接 parse；失败则剥离 Markdown 代码围栏后再 parse），再过 §5.5 Schema 校验与引用完整性校验（列名必须存在）；parse 或校验失败时携带错误反馈**重试 1 次**（即最多调用 2 次），仍失败走降级策略（见 §6 M3）。

---

## 4. 总体架构与数据流

```
┌─────────────┐   text/csv/xlsx   ┌──────────────────────────────────────────┐
│   前端 React │ ───────────────▶ │ M1 数据解析 parser                        │
│  (ECharts   │                   │   原始输入 → RawTable                     │
│   预览)      │                   │ M2 语义分析 semantic                      │
│             │ ◀─────────────── │   RawTable → SemanticTable（含 null 保留） │
│             │  SemanticTable    └──────────────────────────────────────────┘
│             │
│             │  SemanticTable    ┌──────────────────────────────────────────┐
│             │ ───────────────▶ │ M3 图表推荐 recommender                   │
│             │                   │   LLM(严格JSON) + Schema校验 + 降级       │
│             │ ◀─────────────── │   SemanticTable → ChartSpec[]（含数据投影）│
│             │  ChartSpec[]      └──────────────────────────────────────────┘
│             │  （ECharts 按 ChartSpec 渲染候选预览，用户勾选）
│             │
│             │  GenerateRequest  ┌──────────────────────────────────────────┐
│             │ ───────────────▶ │ M4 PPT 生成 pptx_builder                  │
│             │ ◀─────────────── │   python-pptx + ablechart → .pptx         │
└─────────────┘   .pptx 下载      └──────────────────────────────────────────┘
```

**模块边界与部署约束：**
- M1–M4 全部位于后端。前端不解析 Excel（避免前后端两套解析逻辑分叉），仅做输入采集、ChartSpec → ECharts option 映射、文件下载。
- LLM API Key 仅存于后端环境变量，严禁下发前端。
- **ChartSpec（§5.4）是前后端共享的唯一图表事实源**：前端用它渲染预览，后端用它生成 pptx，两端各自实现渲染映射，不允许再引入第二种图表描述格式。

---

## 5. 数据契约（JSON Schema，draft 2020-12）

### 5.0 值规范化规则总表（M2 的统一依据）

| 原始输入示例 | 规范化值 | unit | 说明 |
|---|---|---|---|
| `13.9亿` | `13.9` | `yi` | 保留显示量级，不展开为 1390000000 |
| `7000万` | `7000` | `wan` | 整列单位统一为 `万` 时直接保留数值 |
| `+11.2%` | `0.112` | `percent` | 去 `%`、去前导 `+` 后除以 100（小数形态）；负数保留符号（`-3.9%` → `-0.039`） |
| `7` / `7.0` | `7.0` | `count` | 无单位纯数值 |
| `未披露`/`无`/`—`/`-`/`N/A`/`n/a`/`NA`/空串 | `null` | 继承列 unit | 仅在数值类列（measure/percent）中识别为缺失；维度列保留原字符串 |
| `微信` | `"微信"` | `text` | 维度/备注原样保留 |

**默认缺失标记词表**（须在 M2 配置中显式列出，允许扩展）：
`["未披露", "未公布", "暂无", "无", "—", "--", "-", "N/A", "n/a", "NA", "null", ""]`

**NaN/Inf 处理**：pandas 产生的 `NaN`/`inf` 在 M2 出口必须全部转为 `None`（JSON 无法表达 NaN），不允许泄漏到后续模块。

**混合单位（MVP 已知限制，不自动折算）**：
同一数值列出现混合量级（如多数单元格为 `亿`、个别为 `万`）时：
1. 按非空单元格中占比最高的量级确定**列主单位**（unit）；裸数值（无后缀）单元格视为与列主单位一致；
2. 与列主单位不一致的带后缀单元格，**MVP 不做自动折算**，其值置为 `null`，并在该列的 `warnings` 中记录原始值与原因，例如：`列 "2024 MAU" 主单位为 yi，单元格 "7000万" 未自动折算，已置空`；
3. 这是 **MVP 已知限制**（避免量级误算导致数据失真）；后续版本再引入自动折算或交互式单位确认。

### 5.1 百分比数值转换表（percent 值在各层的唯一权威形态）

以「同比 = 11.2%」（负例：微博同比 `-3.9%`）为准：

| 层 / 载体 | 数值 | 呈现或写入方式 | 禁止事项 |
|---|---|---|---|
| **M2 SemanticTable**（JSON） | `0.112`（number） | `role="percent"`、`unit="percent"`；负数为 `-0.039`；解析阶段（÷100）是全链路唯一的数值转换点 | 禁止存 `11.2`、禁止存 `"11.2%"` 字符串 |
| **M3 LLM 契约 / ChartSpec**（JSON） | `0.112`（number） | LLM 只引用列；投影填充的 `series.data` 为 `0.112`，`axis="secondary"` | 禁止 LLM 给数；禁止任何倍率换算 |
| **前端 ECharts 预览** | 数据仍是 `0.112` | tooltip / label / 副轴通过 formatter（`(v*100).toFixed(1) + "%"`）呈现，用户看到 `11.2%`、`-3.9%` | 禁止在前端修改数据值本身 |
| **M4 写入 pptx** | `0.112`（与 JSON 值一致，直接写入；负例 `-0.039`） | 副轴 / 数据标签数字格式设为 `0.0%`；轴标题如「同比」 | 写入前不得再除 100（M2 已完成转换）；`null` 仍写 `None` |

**边界规则**：`null` 在任何层都保持 `null/None`，不做转换；M2 之外的任何模块对 percent 做乘除 100 均视为缺陷。

### 5.2 RawTable（M1 输出）

M1 只做「切分」，不做数值规范化，单元格保持原始字符串。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "raw_table.schema.json",
  "title": "RawTable",
  "type": "object",
  "required": ["source", "columns", "rows"],
  "properties": {
    "source": { "type": "string", "enum": ["text", "csv", "xlsx"] },
    "sheet_name": { "type": ["string", "null"], "default": null, "description": "仅 xlsx：所选工作表名（默认第一个）" },
    "columns": { "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 1 } },
    "rows": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "array",
        "items": { "type": ["string", "null"] }
      }
    },
    "meta": {
      "type": "object",
      "default": {},
      "properties": {
        "delimiter_detected": { "type": ["string", "null"], "default": null },
        "encoding": { "type": ["string", "null"], "default": null },
        "dropped_rows": { "type": "integer", "minimum": 0, "default": 0, "description": "因列数不符等原因丢弃的行数" },
        "warnings": { "type": "array", "items": { "type": "string" }, "default": [] }
      }
    }
  }
}
```

**不变式**：`rows[i].length === columns.length`（不足补 `null`，超长截断并记 warning）。

### 5.3 SemanticTable（M2 输出，模块间核心契约）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "semantic_table.schema.json",
  "title": "SemanticTable",
  "type": "object",
  "required": ["columns", "rows"],
  "properties": {
    "columns": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "role", "unit", "nullable", "stats"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "role": {
            "type": "string",
            "enum": ["dimension", "measure", "percent", "meta"],
            "description": "dimension=可作分类轴的短文本；measure=数值；percent=百分比数值；meta=备注性文本，不参与绘图"
          },
          "unit": { "type": "string", "enum": ["none", "text", "count", "yi", "wan", "percent"] },
          "nullable": { "type": "boolean" },
          "missing_tokens_hit": {
            "type": "array",
            "items": { "type": "string" },
            "default": [],
            "description": "本列实际命中的缺失标记，如 [\"未披露\"]"
          },
          "warnings": {
            "type": "array",
            "items": { "type": "string" },
            "default": [],
            "description": "列级告警，如混合单位单元格被置空（§5.0）"
          },
          "stats": {
            "type": "object",
            "required": ["null_count", "distinct_count"],
            "properties": {
              "min": { "type": ["number", "null"], "default": null },
              "max": { "type": ["number", "null"], "default": null },
              "null_count": { "type": "integer", "minimum": 0 },
              "distinct_count": { "type": "integer", "minimum": 0 }
            }
          }
        }
      }
    },
    "rows": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "array",
        "items": { "type": ["number", "string", "null"] }
      }
    }
  }
}
```

**不变式**：
- `rows[i].length === columns.length`；
- measure/percent 列的单元格只能是 `number | null`；dimension/meta 列只能是 `string | null`；
- percent 列值域为小数形态（`0.112` 表示 11.2%，允许负数），不含 `%` 字符（§5.1）。

**§12 测试夹具（6 行）经 M2 后的期望输出（验收基准，须逐字段一致）：**

```json
{
  "columns": [
    { "name": "平台",      "role": "dimension", "unit": "text",    "nullable": false, "missing_tokens_hit": [], "warnings": [], "stats": { "min": null, "max": null, "null_count": 0, "distinct_count": 6 } },
    { "name": "2024 MAU",  "role": "measure",   "unit": "yi",      "nullable": false, "missing_tokens_hit": [], "warnings": [], "stats": { "min": 3.2,  "max": 13.9, "null_count": 0, "distinct_count": 6 } },
    { "name": "2025 MAU",  "role": "measure",   "unit": "yi",      "nullable": false, "missing_tokens_hit": [], "warnings": [], "stats": { "min": 3.5,  "max": 14.2, "null_count": 0, "distinct_count": 6 } },
    { "name": "同比",       "role": "percent",   "unit": "percent", "nullable": false, "missing_tokens_hit": [], "warnings": [], "stats": { "min": -0.039, "max": 0.112, "null_count": 0, "distinct_count": 6 } },
    { "name": "2024 DAU",  "role": "measure",   "unit": "yi",      "nullable": true,  "missing_tokens_hit": ["未披露"], "warnings": [], "stats": { "min": 1.0, "max": 7.0, "null_count": 2, "distinct_count": 4 } },
    { "name": "2025 DAU",  "role": "measure",   "unit": "yi",      "nullable": true,  "missing_tokens_hit": ["未披露"], "warnings": [], "stats": { "min": 1.1, "max": 7.6, "null_count": 2, "distinct_count": 4 } },
    { "name": "梯队",       "role": "dimension", "unit": "text",    "nullable": false, "missing_tokens_hit": [], "warnings": [], "stats": { "min": null, "max": null, "null_count": 0, "distinct_count": 4 } },
    { "name": "平台态势",   "role": "meta",      "unit": "text",    "nullable": false, "missing_tokens_hit": [], "warnings": [], "stats": { "min": null, "max": null, "null_count": 0, "distinct_count": 6 } }
  ],
  "rows": [
    ["微信",   13.9, 14.2,  0.024, null, null, "第二梯队", "稳健"],
    ["抖音",   10.5, 11.7,  0.112, 7.0,  7.6,  "第一梯队", "高增长"],
    ["快手",    7.2,  7.0, -0.028, 4.1,  4.0,  "第三梯队", "存量承压"],
    ["微博",    5.9,  5.7, -0.039, 2.6,  2.5,  "第三梯队", "收缩"],
    ["B站",     3.4,  3.7,  0.088, 1.0,  1.1,  "第四梯队", "社区增长"],
    ["小红书",  3.2,  3.5,  0.094, null, null, "第四梯队", "种草扩张"]
  ]
}
```

**role 判定规则（启发式，M2 内部实现）：**
- **列名含 `%`**，或含 `%` 单元格占非空单元格比例 ≥ 60% 的数值列 → `percent`（解析值 = 数值部分 ÷ 100）；
- 其余纯数值列 → `measure`（再按单位后缀占比确定 `yi`/`wan`/`count`）；
- 文本列：`distinct_count / row_count ≤ 0.8` 且最大单元格长度 ≤ 20 字符 → `dimension`，否则 → `meta`；
- 首列若为文本，强制为 `dimension` 并作为 `primary_dimension` 候选。

### 5.4 ChartSpec（M3 输出；前端预览与 M4 生成的统一图表规格）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "chart_spec.schema.json",
  "title": "ChartSpec",
  "type": "object",
  "required": ["id", "chart_type", "title", "categories", "series"],
  "properties": {
    "id": { "type": "string", "minLength": 1 },
    "chart_type": { "type": "string", "enum": ["bar", "hbar", "line", "area", "combo", "stacked", "slope", "scatter", "waterfall", "radar", "pie", "donut", "sunburst"] },
    "title": { "type": "string", "minLength": 1 },
    "subtitle": { "type": ["string", "null"], "default": null },
    "reasoning": { "type": "string", "default": "", "description": "推荐理由，UI 展示用；系列不完整时必须追加规定提示语（见 §6 M3 规则 5）" },
    "semantic_layer": { "type": "string", "enum": ["trend", "comparison", "rate"], "description": "趋势 / 体量对比 / 变化率，三语义层覆盖依据" },
    "dimension_column": { "type": "string" },
    "categories": {
      "type": "array", "minItems": 1,
      "items": { "type": "string" },
      "description": "分类轴标签（dimension 列投影值）；slope 为实体（如平台），scatter 存放行标签用于 tooltip，pie/donut/sunburst 为扇区名，waterfall 为阶段名；radar 为指标名（其 series 为各实体，M3 投影时维度/序列互换）"
    },
    "series": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "source_column", "unit", "axis", "data"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "source_column": { "type": "string", "description": "来源列名，可追溯" },
          "kind": {
            "type": "string", "enum": ["line", "bar", "scatter"], "default": "bar",
            "description": "combo 必填（各序列的绘制形态）；scatter 图序列 kind=scatter；其余类型省略时取与 chart_type 一致的默认形态"
          },
          "unit": { "type": "string", "enum": ["count", "yi", "wan", "percent"] },
          "axis": { "type": "string", "enum": ["primary", "secondary"] },
          "data": {
            "type": "array", "minItems": 1,
            "items": { "type": ["number", "null"], "description": "null=缺失留空（C-3），禁止填 0；percent 为小数形态 0.112（§5.1）" }
          }
        }
      }
    },
    "axes": {
      "type": "object",
      "required": ["primary"],
      "properties": {
        "primary":   { "$ref": "#/$defs/axis" },
        "secondary": { "$ref": "#/$defs/axis" }
      }
    }
  },
  "$defs": {
    "axis": {
      "type": "object",
      "required": ["unit"],
      "properties": {
        "unit": { "type": "string", "enum": ["count", "yi", "wan", "percent"] },
        "title": { "type": ["string", "null"], "default": null, "description": "轴标题，如 'MAU（亿）'" }
      }
    }
  }
}
```

**不变式（validators 必须实现，M3/M4 入口均执行）：**
- **V-1** 非 scatter 图：所有 `series[i].data.length === categories.length`。
- **V-2** `chart_type ∈ {bar, hbar, line, area, combo, stacked, slope, scatter, waterfall, radar, pie, donut, sunburst}`（C-5，v1.6）。
- **V-3** `unit=percent` 的序列：当同图存在非 percent 序列时，必须 `axis=secondary`；主副轴 unit 不得相同。（C-4）
- **V-4** `combo`：序列数 ≥ 2 且至少包含两种不同 `kind`；percent 序列 `kind` 必须为 `line` 并挂副轴。
- **V-5** 所有 `series[i].source_column` 必须存在于 SemanticTable.columns，且其 role 与 `unit` 必须和源列一致（禁止前端/LLM 篡改单位）。
- **V-6** `slope`：序列 ≥ 2 且全部同 unit（measure）；`categories` 为实体集合（series 为各期快照，每条序列画为一条两点连线；line 图的特例约定）。
- **V-7** `scatter`：恰好 2 个 measure 序列（`kind=scatter`，分别为 X/Y）；任一坐标为 null 的点整点剔除。
- **V-8** `pie`：恰好 1 个 measure 序列；null 数据点对应扇区剔除（不按 0 绘制）。
- **V-9** `stacked`：≥ 2 个同单位 measure 序列（非 percent），堆叠才有意义。
- **V-10** `waterfall`：恰好 1 个 measure 序列（非 percent）；数值为各阶段增量（首项为基数）。
- **V-11** `radar`：≥ 3 个同单位 measure 序列（非 percent）；`categories` 为指标名，`series` 为各实体（M3 投影时维度/系列互换）。
- **V-12** `donut` / `sunburst`：同 V-8 pie 口径——恰好 1 个 measure 序列（非 percent），null 扇区剔除。
- **新类型 percent 口径**：`stacked`、`waterfall`、`radar`、`donut`、`sunburst` 一律禁止 percent 序列（同 slope/scatter/pie）；percent 仅允许出现在 `bar`、`hbar`、`line`、`area`、`combo`。

### 5.5 LLM 内部输出契约（M3 与 LLM 之间）

LLM 只引用列、不给数据（C-5）。**LLM 必须输出裸 JSON 数组**（顶层即 `[ ... ]`，不得包对象、不得带 Markdown 围栏与解释文本），后端按以下元素 Schema 校验：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "llm_recommendation_item.schema.json",
  "title": "LlmRecommendationItem（LLM 输出数组的单个元素）",
  "type": "object",
  "required": ["chart_type", "title", "config", "reasoning"],
  "additionalProperties": false,
  "properties": {
    "chart_type": { "type": "string", "enum": ["bar", "hbar", "line", "area", "combo", "stacked", "slope", "scatter", "waterfall", "radar", "pie", "donut", "sunburst"] },
    "title": { "type": "string", "minLength": 1, "maxLength": 60 },
    "reasoning": { "type": "string", "maxLength": 200, "description": "推荐理由（不得编造数据值）" },
    "config": {
      "type": "object",
      "required": ["dimension", "series"],
      "additionalProperties": false,
      "properties": {
        "dimension": { "type": "string", "description": "必须是 role=dimension 的列名" },
        "semantic_layer": { "type": "string", "enum": ["trend", "comparison", "rate"], "description": "可省略，省略时由后端推断" },
        "series": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["column"],
            "additionalProperties": false,
            "properties": {
              "column": { "type": "string", "description": "必须是 role=measure 或 percent 的列名" },
              "kind": { "type": "string", "enum": ["line", "bar", "scatter"], "default": "bar" },
              "axis": {
                "type": "string", "enum": ["primary", "secondary"],
                "description": "可省略：percent 列后端强制 secondary（V-3）；其余默认 primary"
              }
            }
          }
        }
      }
    }
  }
}
```

**裸数组示例（LLM 的原始响应文本）：**

```json
[
  {
    "chart_type": "combo",
    "title": "各平台 MAU 规模与同比增速",
    "reasoning": "MAU 为亿级体量、同比为百分比，双轴组合图避免量纲混淆",
    "config": { "dimension": "平台", "semantic_layer": "rate", "series": [
      { "column": "2024 MAU", "kind": "bar" },
      { "column": "2025 MAU", "kind": "bar" },
      { "column": "同比", "kind": "line" }
    ]}
  }
]
```

**LLM 调用参数**：`temperature ≤ 0.3`；system prompt 内嵌本节元素 Schema、「输出裸 JSON 数组」要求、C-4/C-5 约束（六种 chart_type 枚举、percent 必须挂副轴、禁止输出数据值）与三语义层覆盖要求（趋势 / 体量对比 / 变化率，至少各 1 条）；user prompt 仅提供 SemanticTable 的列摘要（name/role/unit/stats/null_count）与 ≤10 行抽样数据。为兼容不支持 strict 数组模式的模型，不依赖 `response_format`；解析层负责容错（直接 parse → 剥围栏 parse → 识别为 `{"recommendations":[...]}` 旧形态时取数组）。

### 5.6 GeneratePptxRequest（M4 单图导出端点，v1.4 现行契约）

`POST /api/generate-pptx` 一次生成一张图表、单页 `.pptx`。入参为 ChartSpec 的**自描述扁平形态**（不依赖上游 SemanticTable，可独立调用，数据自带于 `data`）。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "generate_pptx_request.schema.json",
  "title": "GeneratePptxRequest",
  "type": "object",
  "required": ["chart_type", "data"],
  "additionalProperties": false,
  "properties": {
    "chart_type": {
      "type": "string",
      "enum": ["bar", "hbar", "line", "area", "combo", "stacked", "slope", "scatter", "waterfall", "radar", "pie", "donut", "sunburst"],
      "description": "六种图型全部支持导出（v1.5 起）；未知类型返回 400 VALIDATION_FAILED"
    },
    "config": {
      "type": "object",
      "default": {},
      "properties": {
        "title": { "type": ["string", "null"], "default": null },
        "dimension_column": { "type": ["string", "null"], "default": null, "description": "分类轴列名，仅用于缺省标题，不参与取数" }
      }
    },
    "data": {
      "type": "object",
      "required": ["categories", "series"],
      "properties": {
        "categories": { "type": "array", "minItems": 1, "items": { "type": "string" } },
        "series": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["name", "data"],
            "properties": {
              "name": { "type": "string", "minLength": 1 },
              "kind": { "type": "string", "enum": ["line", "bar", "scatter"], "description": "combo 必填，决定 bar/line；纯 line/bar 图可省略" },
              "axis": { "type": "string", "enum": ["primary", "secondary"], "default": "primary" },
              "unit": { "type": "string", "enum": ["count", "yi", "wan", "percent"], "default": "count" },
              "data": { "type": "array", "items": { "type": ["number", "null"] }, "description": "null=缺失（C-3），禁止填 0；percent 为小数形态 0.112（§5.1）" }
            }
          }
        }
      }
    }
  }
}
```

**入参校验规则（M4 入口，不信任前端）：**
- 非 scatter/pie 图：每个 `series[i].data.length === data.categories.length`。
- `combo`：≥2 个系列且至少一个 `kind=bar`、一个 `kind=line`；`unit=percent` 系列必须 `kind=line` 且 `axis=secondary`；主、副轴 unit 不得相同（V-3/V-4，C-4）。
- percent 值必须是小数形态（绝对值 ≤ 1.5 的宽松容忍，仅用于拦截 `11.2` 这类未转换值；不修改数据）。
- `scatter`：恰好 2 个系列（x、y），且均不得为 percent；`pie`：恰好 1 个系列，且不得为 percent；`slope`：不得含 percent 系列（与 M3 投影口径一致）。
- 非法入参返回 §5.7 ApiError：`VALIDATION_FAILED`（结构/长度/类型约束问题），HTTP 400。

**GenerateResult**：HTTP 层直接返回 `.pptx` 文件流（见 §7）：
`Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation`
`Content-Disposition: attachment; filename="chart-{yyyyMMdd-HHmmss}.pptx"`（标准端点自 v1.11 起不再有 `animate`，动效产物见 §5.6a）。

**数据标签（v1.16）**：请求体顶层可选 `show_labels: boolean`（默认 false）。为 true 时在原生 Chart 的序列上写 `<c:dLbls>` 显值（口径见修订记录 v1.16）；标签为原生元素、可在 PPT/WPS 继续编辑。
错误时返回 §5.7 ApiError（构建失败 `PPTX_BUILD_FAILED`，HTTP 500）。

### 5.6a 动效产物契约（GIF，v1.11 引入 / v1.12 扩展为直出 + 嵌入两形态，R-6）

两个端点共享同一帧契约与 GIF 合成核心，前端离屏 ECharts 采帧 → 后端 PIL 合成 GIF。位图产物、不可编辑，属独立动效产物，不影响 C-1（C-1 仅约束 §5.6 标准端点）。

- **`POST /api/generate-gif`（v1.12 起为主形态）**：直接返回 `image/gif` 文件，`Content-Disposition: attachment; filename="chart-{yyyyMMdd-HHmmss}.gif"`。
- `POST /api/generate-animated-pptx`（v1.11，保留）：把同一 GIF 以 `add_picture` 等比居中嵌入 16:9 空白页（可选 `title` 页标题），返回 `chart-animated-{ts}.pptx`。

```json
{
  "title": "AnimatedFramesRequest",
  "type": "object",
  "required": ["frames"],
  "properties": {
    "title":       { "type": ["string", "null"], "default": null, "description": "仅嵌入 pptx 形态使用，直出 GIF 忽略" },
    "frames":      { "type": "array", "minItems": 2, "items": { "type": "string", "description": "base64 PNG dataURL（data:image/png;base64,...）" } },
    "frame_ms":    { "type": "integer", "minimum": 20, "maximum": 2000, "default": 100, "description": "每帧时长（GIF duration）" },
    "transparent": { "type": "boolean", "default": false, "description": "true=二元透明底（保留 alpha=0）；false=跟随主题实底（推荐）" }
  }
}
```

**背景模式（v1.12）**：
- `transparent=false`（默认）：帧由前端按当前 UI 主题铺实底色（深色/浅色）。GIF 不支持半透明，透明像素若不铺底会被填黑。
- `transparent=true`：GIF 仅有二元透明（每像素全透/不透，无 alpha 半透明）——后端保留 RGBA 合成（P 模式 + `transparency` 索引、`disposal=2` 防帧残影）。代价：抗锯齿边缘/面积图半透明填充/发光阴影被硬切可能毛边，且文字坐标色随主题，透明底仅适合贴到与主题同色的背景。

入参校验规则（不信任前端）：frames 至少 2 帧；每帧必须是 `data:image/png;base64,` 前缀的合法 base64 PNG（PIL 可解码）；`transparent` 必须为布尔；非法返回 `VALIDATION_FAILED`（400）；合成/构建异常返回 `PPTX_BUILD_FAILED`（500）。

直出 GIF 输出：`Response`，`Content-Type: image/gif`，魔数 `GIF89a`，循环 `loop=0`。

### 5.6b GenerateRequest（多图 deck 契约，后续里程碑，MVP 不实现）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "generate_request.schema.json",
  "title": "GenerateRequest",
  "type": "object",
  "required": ["table", "charts"],
  "properties": {
    "table": { "$ref": "semantic_table.schema.json" },
    "charts": {
      "type": "array", "minItems": 1, "maxItems": 20,
      "items": {
        "type": "object",
        "required": ["spec"],
        "properties": {
          "spec": { "$ref": "chart_spec.schema.json" },
          "slide_title": { "type": ["string", "null"], "default": null, "description": "覆盖 spec.title 作为页标题" },
          "show_data_table": { "type": "boolean", "default": false, "description": "图表页下方附数据表" }
        }
      }
    },
    "options": {
      "type": "object",
      "default": {},
      "properties": {
        "title_slide": { "type": "boolean", "default": true },
        "deck_title": { "type": "string", "default": "数据图表报告" },
        "append_raw_table_slide": { "type": "boolean", "default": false, "description": "末尾附完整数据表页" },
        "slide_size": { "type": "string", "enum": ["16:9", "4:3"], "default": "16:9" }
      }
    }
  }
}
```

多图 deck 端点路径预留为 `POST /api/generate`（携带 SemanticTable + ChartSpec 列表 + 分页选项），在单图端点稳定后于后续里程碑实现。

### 5.7 ApiError（统一错误格式）

```json
{
  "title": "ApiError",
  "type": "object",
  "required": ["code", "message"],
  "properties": {
    "code": { "type": "string", "description": "机器可读错误码，如 PARSE_EMPTY / LLM_INVALID_JSON / VALIDATION_FAILED / PPTX_BUILD_FAILED" },
    "message": { "type": "string", "description": "面向用户的中文描述" },
    "details": { "type": ["object", "null"], "default": null }
  }
}
```

---

## 6. 模块详述与验收标准

### M0 ablechart 可行性验证（Spike，进入 M1 的前置门禁）

**职责**：在业务编码前，用一次性脚本验证锁定依赖能真正生成符合 C-1/C-2/C-4 的双轴组合图。脚本位置：`backend/spikes/ablechart_spike.py`。

**必须达成的目标（全部满足才算通过）：**
1. **能装**：`pip install "ablechart==0.2.0" "python-pptx>=1.0.2,<2.0"` 成功，二者可同进程导入（numpy 版本兼容、无导入冲突）。
2. **能生成双轴 combo**：用 §12 夹具数据调 `ablechart.create_combo_chart` 在 `Presentation` 上生成一张组合图——主轴为 `2024 MAU`/`2025 MAU` 的 **bar**（unit=yi），副轴为「同比」的 **line**（unit=percent）。
3. **副轴 percent 生效**：解压产出的 pptx，检查对应 `ppt/charts/chart1.xml`：
   - 存在两个数值轴（primary / secondary），percent 序列引用副轴；
   - 副轴或该序列数字格式包含 `%`；
   - percent 数据点写入值与 JSON 一致（`0.024`、`0.112`、`-0.039`，§5.1 小数形态，写入前不再换算）。
4. **原生图表与断链**：产物中存在 `ppt/charts/chart1.xml`（C-1），且不存在指向外部文件的数据 relationship（C-2 的断链处理在真实 ablechart 产物上验证可行）。
5. 产物可被 python-pptx 重新打开，WPS 双击可编辑（至少完成自动化断言；人工双击可延后到 M4 验收）。

**失败预案**：若 `create_combo_chart` 不支持双轴或 percent 格式，先回写本 SPEC（§6 M4 映射表与 R-1），改用 python-pptx 原生 XML 扩展实现副轴，仍以 C-1/C-2/C-4 的验证方式为准；**M0 未通过不得进入 M1 编码。**

### M1 数据解析模块（`parser`）

**职责**：把三种来源的输入规整为 RawTable。不做数值规范化。

**处理规则：**
- **text**：支持 Markdown 表格（`| a | b |`，自动跳过 `|---|` 分隔行）、制表符、逗号、分号分隔；分隔符自动嗅探；首行为表头。
- **csv**：编码按 `utf-8-sig → gbk` 顺序回退探测；分隔符嗅探。
- **xlsx**：默认读取第一个工作表（`sheet_name` 可指定）；首行为表头；空表返回 `PARSE_EMPTY`。
- 行单元格数与表头不一致：不足补 null，超长截断，计入 `meta.dropped_rows` / `warnings`。
- 限制：文件 ≤ 10MB，数据行 ≤ 10000（超限返回 `PARSE_TOO_LARGE`）。

**输入**：`UploadFile` 或 `{"text": string}`（HTTP 契约见 §7）。
**输出**：RawTable（§5.2）。

**验收标准：**
- A-1.1：§12 样例 Markdown 文本解析出 8 列 × 6 行，`未披露`、`+11.2%`、`-3.9%`、`13.9亿` 保持原始字符串进入 RawTable。
- A-1.2：同内容 CSV（utf-8-sig 与 gbk 两种编码）与 xlsx 三种输入，RawTable 完全一致。
- A-1.3：列数不齐的行不抛异常，正确补 null 并记录 warning；全空输入返回 `PARSE_EMPTY` 错误。

### M2 语义分析模块（`semantic`）

**职责**：RawTable → SemanticTable。执行 §5.0 全部规范化规则、role/unit 判定、stats 统计。对外门面入口：`parse_input(raw_text: str) -> dict`（M1+M2 串联，返回 SemanticTable）。

**处理规则：**
- 按 §5.0 词表将缺失标记映射为 `None`（C-3）；记录 `missing_tokens_hit`（空串命中不计入）。
- 数值正则：`^[+-]?\d+(\.\d+)?\s*(亿|万|%)?$`；带单位的列要求 ≥60% 非空单元格命中同一模式，否则整列降级为 `meta` 并记 warning。
- **percent 判定与转换**：列名含 `%`，或 ≥60% 非空单元格带 `%` 后缀 → `role=percent`；解析值 = 数值部分 ÷ 100（`+11.2% → 0.112`，负号保留），保留至 10 位小数内；percent 是全链路唯一的数值转换点（§5.1）。
- pandas `NaN`/`inf` → `None`（出口强制清洗）。
- 同列混合 `亿`/`万`：**不自动折算**——按占比高者定列 unit，裸数值视为同单位，其余异类单元格置 `null` 并写入列级 `warnings`（§5.0，MVP 已知限制）。
- 数值类列中无法按数值解析的非缺失单元格：置 `null` 并记 warning。

**输入**：RawTable。 **输出**：SemanticTable（§5.3）。

**验收标准：**
- A-2.1：样例数据输出与 §5.3「期望输出」完全一致（8 列 × 6 行；同比为 `[0.024, 0.112, -0.028, -0.039, 0.088, 0.094]`；微信与小红书 4 个 DAU 单元格为 `null`；抖音 DAU 完整为 `7.0`/`7.6`）。
- A-2.2：序列化后的 JSON 中不存在 `NaN`/`Infinity` 字面量；缺失单元格为 `null`。
- A-2.3：`同比` 列 role=percent；`平台态势` 列 role=meta；`平台`/`梯队` 列 role=dimension。
- A-2.4：构造一列含 `13.9亿` 与 `7000万` 混合单位的数据：列 unit 为 `yi`，`7000万` 单元格输出 `null`，且列 `warnings` 含未折算说明；不得输出 `0.7`。
- A-2.5：缺失标记「无」「—」在数值列中映射为 `null`（C-3）；列名含 `%` 而单元格为裸数字（如 `11.2`）时，列仍识别为 percent 且值解析为 `0.112`。

### M3 图表推荐模块（`recommender`）

**职责**：SemanticTable → ChartSpec[]。内部步骤：构造 prompt → 调 LLM → 严格校验 → 数据投影 → 不变式校验。

**处理规则：**
1. prompt 只含列摘要（含 null_count）+ ≤10 行抽样，明确六种 chart_type、三语义层至少各 1 条、禁止输出数据值。
2. LLM 响应校验链：容错 JSON parse（先直接 parse；失败剥离 Markdown 围栏再 parse；兼容 `{"recommendations":[...]}` 包装形态）→ §5.5 元素 Schema 逐条校验 → 引用完整性（列名存在、role 合法）。parse 或整体校验失败时，携带错误信息**重试 1 次（最多调用 2 次）**；单条推荐非法仅丢弃该条并记 warning，不整体重试。
3. **轴与形态归一**：LLM 可省略 `axis`——percent 列后端强制 `axis=secondary` 且（combo 内）`kind=line`，其余默认 `primary`；与 LLM 显式指定冲突且违反 V-3/V-4 时，以后端强制规则为准。
4. **数据投影**：后端按 `config.dimension` + `config.series[].column` 从 SemanticTable 取真实数据填充 `categories` 与 `data`（null 原样保留，C-3），生成完整 ChartSpec（§5.4），过 V-1~V-8；不过则丢弃该条。
5. **缺失系列提示（确定性，不依赖 LLM 是否写出）**：投影后任一 `series.data` 含 null，则在该 ChartSpec 的 `reasoning` 末尾**原样追加**规定提示语（v1.14/v1.18：按归一化后 lang 取 `INCOMPLETE_NOTE[lang]`，五语言各一条；LLM 的 reasoning 已包含对应语言的该短语时不重复追加；多系列缺失时逐系列加列名前缀，分隔符 zh 用全角「：；」、其余用半角 ": " / "; "）。**禁止**为缺失值编造任何数值（A-3.6）。
6. **语义层覆盖**：每条 ChartSpec 的 `semantic_layer` 取 LLM 值（非法/缺失时由后端推断：含 percent 副轴→`rate`；line/slope 且≥2 期同单位→`trend`；否则→`comparison`）。LLM 结果若未同时覆盖 trend / comparison / rate 三层（且数据支持），用降级策略补齐缺失层。
7. **降级策略**（LLM 失败或覆盖不全时的启发式兜底，按数据条件产出）：
   - 有 measure + percent → `combo`（measure bar 主轴 + percent line 副轴，`rate`）；
   - ≥2 个同单位 measure（如两期 MAU）→ `line`（`trend`）；恰为 2 期时同时产出 `slope`（`trend`，series 为两期、categories 为实体）；
   - 任意 measure → `bar`（`comparison`）；
   - 恰好 1 个 measure + 1 个 dimension → 追加 `pie`（`comparison`）；≥2 个 measure → 追加 `scatter`（前两列，`comparison`）。
   降级结果同样过 V-1~V-8。表中无任何 measure/percent 列时，`/api/recommend` 返回 `VALIDATION_FAILED`（message：数据中没有可绘图的数值列）。
8. 输出数量 1~6 条，去重（同 chart_type + 同列组合视为重复）；LLM 未配置 `LLM_API_KEY` 时直接走降级，不报错。

**输入**：SemanticTable。 **输出**：`{ "recommendations": ChartSpec[], "degraded": boolean }`。

**验收标准：**
- A-3.1：mock LLM 返回合法裸数组 JSON 时，输出 ChartSpec 通过 §5.4 Schema 与 V-1~V-8；含 Markdown 围栏 / 旧版 `{"recommendations":[...]}` 包装的响应经容错后同样通过。
- A-3.2：mock LLM 首次返回非 JSON、二次返回合法 JSON → 断言恰好调用 2 次且最终成功；返回引用不存在列 / chart_type 越界（如 `radar`）的条目被丢弃，最终不产出非法 ChartSpec。
- A-3.3：mock LLM 持续失败时，`degraded=true`；对 §12 夹具必须覆盖三层语义（trend=line/slope、comparison=bar、rate=combo 含同比副轴），且每条通过 V-1~V-8。
- A-3.4：所有输出中 percent 序列均为 secondary、combo 内 `kind=line`（C-4）；data 中 null 未被改写（C-3），percent 值保持 `0.112` 小数形态（§5.1）。
- A-3.5：即使 LLM 在 config 外伪造 data/数值字段，最终 data 全部来自 SemanticTable 投影（抽查断言伪造值不出现）。
- A-3.6：含 DAU 系列的推荐，其 `reasoning` 必须包含短语「该系列数据不完整，建议不纳入」；对应 data 中微信/小红书位置为 `null` 而非 0；LLM 已写该短语时不重复追加。

### M4 PPT 生成模块（`pptx_builder`）

**职责**：GeneratePptxRequest（§5.6，单图自描述）→ 单页 `.pptx` 文件流。C-1/C-2/C-3/C-4 的最终落点。多图 deck（§5.6b）为后续里程碑。

**处理规则：**
1. 入口按 §5.6「入参校验规则」校验（不信任前端）：长度一致、combo 的 kind/axis/unit 约束、percent 形态、scatter/pie 系列数约束、slope/scatter/pie 禁 percent；非法返回 `VALIDATION_FAILED`。
2. 图表类型映射（v1.6 起十三型全覆盖）：
   | chart_type | 实现方式 |
   |---|---|
   | `bar` | python-pptx `add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, ...)` + `CategoryChartData` |
   | `hbar` | python-pptx `add_chart(XL_CHART_TYPE.BAR_CLUSTERED, ...)` + `CategoryChartData`（水平条形） |
   | `line` | python-pptx `add_chart(XL_CHART_TYPE.LINE_MARKERS, ...)` + `CategoryChartData`，显式置 `c:dispBlanksAs val="gap"`（空点断线，不把空值当 0 连接，C-3） |
   | `area` | python-pptx `add_chart(XL_CHART_TYPE.AREA, ...)` + `CategoryChartData` |
   | `combo` | **`ablechart.create_combo_chart`**（M0 已验证）：构造 `DataFrame`（分类列 + 各系列列，None 保留为 NaN），`series_config=[{key,name,type,axis}]`，bar 主轴 + percent line 副轴，`polish=False`；之后对两个 `c:valAx` 设置数字格式 |
   | `stacked` | python-pptx `add_chart(XL_CHART_TYPE.COLUMN_STACKED, ...)` + `CategoryChartData`（V-9：≥2 同单位序列） |
   | `slope` | 同 line 的 `LINE_MARKERS` + `CategoryChartData` + `dispBlanksAs=gap`（系列为两期快照，R-4） |
   | `scatter` | python-pptx `add_chart(XL_CHART_TYPE.XY_SCATTER, ...)` + `XyChartData`，任一坐标为 None 的点整体剔除（C-3）；x/y 轴按对应系列 unit 设数字格式 |
   | `waterfall` | **等价实现（无原生枚举，R-5）**：python-pptx `COLUMN_STACKED` + 两个系列——「底座」系列（`format.fill.background()` 置透明）+「增量」系列；取值口径：**底座 = min（前值累计， 后值累计），增量 = |原始增量|**——堆叠图中负值会回落零轴下方独立渲染，负增量必须翻转为正值段并以下界垫高，否则瀑布形态断裂；None 增量保持空点（C-3，底座对应位补 0 高度即不可见）；原生可编辑 Chart，C-1 不违反 |
   | `radar` | python-pptx `add_chart(XL_CHART_TYPE.RADAR_MARKERS, ...)` + `CategoryChartData`（categories=指标名，系列=各实体，V-11） |
   | `pie` | python-pptx `add_chart(XL_CHART_TYPE.PIE, ...)` + `CategoryChartData`，值为 None 的扇区整体剔除（C-3） |
   | `donut` | python-pptx `add_chart(XL_CHART_TYPE.DOUGHNUT, ...)` + `CategoryChartData`，None 扇区剔除（V-12） |
   | `sunburst` | **降级近似（R-5）**：python-pptx 无旭日类型，导出为 `DOUGHNUT`（环图近似，None 扇区剔除）；前端预览仍为真旭日效果，PPT 侧以圆环表达占比 |
3. 数据写入：缺失值以 `None` 写入（line 断线、bar 缺柱，C-3），任何环节禁止转 0；combo 经 pandas 时 None→NaN，ablechart 同样写为空点。
4. 数字格式（严格按 §5.1）：percent 序列**按 JSON 值直接写入**（已为 `0.112` 小数形态，不再换算），**副轴 tick label 数字格式 `0.0%`**；`yi` 序列原值写入，**主轴 tick label 数字格式 `0.0"亿"`**（`wan` 类推 `0.0"万"`，`count` 用 `General`）。格式作用于对应 `c:valAx/c:numFmt`。
5. **BreakLink 收尾（C-2，等价 XML 实现，R-2）**：save 之前遍历 `prs.slides[*].shapes` 中 `has_chart=True` 的 shape，对 `chart.part.rels.values()` 中 `is_external=True` 的关系删除；随后移除 `c:chartSpace/c:chart` 下已无有效引用的 `<c:externalData r:id=.../>` 元素（仅删空引用，内部嵌入 workbook 的 `package` 关系保留，以保证双击可编辑）。语义等价于「`IsLinked` 为 True 则 `BreakLink()`」：python-pptx 1.0.2 无公共 IsLinked/BreakLink API，外部关系是否存在即 IsLinked 的判据。
6. 页面结构：单页 16:9 空白版式，图表铺满大部分版面；若给 `config.title`，加文本框页标题。
7. 输出：`Response`，`Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation`，`Content-Disposition: attachment; filename="chart-{yyyyMMdd-HHmmss}.pptx"`。
8. **v1.11 起移除 `animate` 入参与 p:timing 注入路径**：标准导出端点恒为纯静态原生可编辑 Chart（C-1）。动效版改由独立端点 `/api/generate-animated-pptx`（§5.6a，GIF 路线，R-6）提供。历史：v1.7~v1.10 的 OOXML `<p:timing>`/oleChartEl 图表分段动画因 WPS 支持不可靠且无法在本环境验证而废弃（见修订记录 v1.11）。

**§6a M4b 动效产物 GIF（v1.11 引入 / v1.12 直出为主，R-6）**

1. **前端采帧**：离屏创建隐藏容器，`echarts.init`（devicePixelRatio 2）+ `specToOption(spec, theme)` setOption 播放绘制动画；以固定帧间隔 `frame_ms`（默认 100ms）采样 `chart.renderToCanvas().toDataURL('image/png')`，总时长覆盖动画周期（默认 ≈1.9s），得到 PNG dataURL 帧序列。背景：`transparent=false` 时给 option 注入主题实底色（深色 `#0d1424` / 浅色 `#f4f8fc`，GIF 不支持半透明，透明区会被填黑）；`transparent=true` 时不铺底、保留 alpha。
2. **上传**：主端点 `POST /api/generate-gif`（v1.12）直出 GIF；嵌入端点 `POST /api/generate-animated-pptx`（v1.11，保留）。入参 `{title?, frames: string[], frame_ms?, transparent?}`（§5.6a）。
3. **后端合成**：PIL 逐帧 base64 解码 → `Image.open`；实底模式转 RGB，透明模式保留 RGBA；首帧 `save(format='GIF', save_all=True, append_images=rest, duration=frame_ms, loop=0, disposal=2)` 合成循环动态 GIF（透明模式 GIF 为二元透明，`transparency` 索引；`disposal=2` 防帧间残影）。
4. **形态**：直出端点返回 `image/gif`（`chart-{ts}.gif`）；嵌入端点把同一 GIF 以 `add_picture` 等比居中嵌入 16:9 空白页（可选 `title`），返回 `chart-animated-{ts}.pptx`。
5. **输出**：直出 `Content-Type: image/gif`、魔数 `GIF89a`；嵌入 `Content-Type: ...presentationml.presentation`。PPT/WPS 放映对 GIF 动图支持稳定。
6. **约束**：动效产物为位图、不可编辑，属用户显式选择的独立产物，**不影响 C-1**（C-1 仅约束标准导出端点）；后端不合成图表、不处理 ChartSpec 数据，仅做帧→GIF（→嵌入）。透明模式为可选，仅适合贴同色背景（§5.6a）。

**输入**：GeneratePptxRequest（§5.6）。 **输出**：`.pptx` 二进制流 / ApiError。

**验收标准（test_pptx_builder.py）：**
- A-4.1：产物可被 python-pptx 重新打开，含 1 个 has_chart shape（combo 请求亦然）。
- A-4.2：解压产物——存在 `ppt/charts/chart1.xml`；`ppt/media/` 无图表图片（C-1）。
- A-4.3：遍历所有 has_chart shape，其 `chart.part.rels` 中不存在任何 `is_external=True` 关系；解压产物 `ppt/charts/_rels/*.rels` 无 `TargetMode="External"`（C-2）。
- A-4.4（combo 必测）：chart XML 同时含 `c:barChart` 与 `c:lineChart`、且有两个 `c:valAx`；副轴 `numFmt` 含 `0.0%`；缓存的 percent 值点（`c:v`）与 JSON 一致（`0.024`/`0.112`/`-0.039`，§5.1 / C-4）；主轴 `numFmt` 含 `亿`。
- A-4.5：line 图含 null 系列——chart XML 中 `<c:dispBlanksAs val="gap"/>`，且空点缓存不出现 `0`（C-3）。
- A-4.6（可更新性）：读回产物中的 chart，调用 `chart.replace_data(CategoryChartData)` 改写内嵌数据后重新读回，`series.values` 等于新值（验证是真内嵌、可编辑的原生 Chart，而非图片/死链）。
- A-4.7：非法入参（percent 挂主轴 / data 长度不齐 / chart_type=radar / scatter 系列数≠2 / pie 系列数≠1 / slope、scatter、pie 含 percent）→ HTTP 400 `VALIDATION_FAILED`，不产出文件。
- A-4.9（v1.5 六型覆盖）：slope 产物含 `dispBlanksAs=gap` 且可重开；scatter 产物 plot 为 `scatterChart` 且无效（含 null）点已剔除；pie 产物 plot 为 `pieChart` 且 null 扇区已剔除；三者均无外部关系（C-2 同其他类型）。
- A-4.8（人工，延后）：WPS 与 PowerPoint 打开产物，双击图表可编辑数据，无「链接文件不可用」提示。
- A-4.10（v1.7 动效版）：`animate=true` 时十三型逐一构建——slide XML 含 `<p:timing>` 与 `<p:bldLst>`，`<a:bldChart>` 的 `bld` 值与 `<p:animEffect>` 的 `filter` 符合规则 8 映射；产物可重开、图表仍 `has_chart` 且无 External rels（动画不破坏 C-1/C-2）；`animate` 缺省/false 时 slide XML 不含 `<p:timing>`。
- A-4.11（人工，延后）：WPS 与 PowerPoint 打开放映动效版，放映时图表按映射逐点出现（v1.8 按数据点构建），双击图表仍可编辑数据。

---

## 7. HTTP API 契约（FastAPI）

| 方法 | 路径 | 请求 | 响应 | 说明 |
|---|---|---|---|---|
| GET | `/api/health` | - | `{"status":"ok"}` | 健康检查 |
| POST | `/api/parse` | `multipart/form-data`（`file`）**或** JSON `{"text": string, "sheet_name"?: string}` | SemanticTable（§5.3） | M1+M2 串联，一次调用（已实现） |
| POST | `/api/recommend` | SemanticTable，可选顶层 `lang`（v1.18：`"zh"/"en"/"fr"/"de"/"es"` 直通，非法/缺省回退 `"en"`；可与 `columns/rows` 同级，兼容裸表） | `{"recommendations": ChartSpec[], "degraded": boolean}` | M3；`lang` 决定 title/reasoning 与降级模板语言（v1.14/v1.18），列名等数据保持原文 |
| POST | `/api/generate-pptx` | GeneratePptxRequest（§5.6，单图 `{chart_type, config, data}`） | `.pptx` 文件流 | M4（已实现）；错误返回 ApiError + 4xx/5xx |
| POST | `/api/generate-gif` | AnimatedFramesRequest（§5.6a，GIF 帧序列 + transparent?） | `.gif` 文件流 | M4b 动效直出（v1.12 主形态，R-6） |
| POST | `/api/generate-animated-pptx` | AnimatedFramesRequest（§5.6a，GIF 帧序列） | `.pptx` 文件流 | M4b 嵌入版（v1.11，保留，R-6） |
| POST | `/api/generate` | GenerateRequest（§5.6b，多图 deck） | `.pptx` 文件流 | 后续里程碑，MVP 未实现 |

**通用约定：**
- 所有错误响应统一为 ApiError（§5.7），HTTP 状态码语义化（400 参数/校验错误，413 超限，502 LLM 失败且降级亦失败，500 其他）。
- 后端配置 CORS，允许前端开发源。
- 请求体大小限制 10MB。

**`/api/recommend` 响应示例（基于 §12 夹具的 combo 推荐）：**

```json
{
  "degraded": false,
  "recommendations": [
    {
      "id": "rec-01",
      "chart_type": "combo",
      "title": "各平台 MAU 规模与同比增速",
      "reasoning": "MAU 为亿级数值、同比为百分比，组合图双轴可避免量纲混淆；含负增长平台，副轴可体现正负区间",
      "semantic_layer": "rate",
      "dimension_column": "平台",
      "categories": ["微信", "抖音", "快手", "微博", "B站", "小红书"],
      "series": [
        { "name": "2024 MAU", "source_column": "2024 MAU", "kind": "bar",  "unit": "yi",      "axis": "primary",   "data": [13.9, 10.5, 7.2, 5.9, 3.4, 3.2] },
        { "name": "2025 MAU", "source_column": "2025 MAU", "kind": "bar",  "unit": "yi",      "axis": "primary",   "data": [14.2, 11.7, 7.0, 5.7, 3.7, 3.5] },
        { "name": "同比",      "source_column": "同比",      "kind": "line", "unit": "percent", "axis": "secondary", "data": [0.024, 0.112, -0.028, -0.039, 0.088, 0.094] }
      ],
      "axes": {
        "primary":   { "unit": "yi",      "title": "MAU（亿）" },
        "secondary": { "unit": "percent", "title": "同比" }
      }
    }
  ]
}
```

> ChartSpec JSON 中 percent 值为小数形态（`0.112` / `-0.039`，§5.1），M4 写入 pptx 时直接使用该值、不再换算。

---

## 8. 前端契约（React + ECharts）

**页面流（单页三步）：**
1. **输入页**：文本粘贴区 + 文件拖拽上传（.csv/.xlsx）→ 调 `/api/parse` → 展示规整后的数据表（含 role/unit 徽标、null 高亮为「缺失」、列 warning 提示混合单位置空）。
2. **预览页**：调 `/api/recommend` → 卡片网格展示候选图表（ECharts 渲染 + 标题 + reasoning，含「数据不完整」提示徽标），按 semantic_layer 分组，支持勾选、调整顺序、编辑标题。
3. **导出页**：调 `/api/generate`（携带 SemanticTable + 选中 ChartSpec）→ fetch 转 blob 下载 pptx。

**ChartSpec → ECharts option 映射规则（前端唯一映射层 `specToOption.ts`）：**
- `line`：类目轴折线图，`connectNulls: false`（null 断线，C-3 的可视化表达）。
- `bar`：类目轴分组柱；null 位置缺柱，不渲染为 0。
- `combo`：bar 系列 `yAxisIndex:0`，percent line 系列 `yAxisIndex:1`；双 y 轴。
- `slope`：以两期为 x 轴两个类目点、每个实体（平台）一条线，端点显示数值标签；空点断线。
- `scatter`：两序列配对为 `[x, y]` 点（type=scatter），任一坐标为 null 的点整点剔除（V-7）。
- `pie`：单序列饼图，null 扇区剔除不绘制（V-8）。
- tooltip/label 按 `unit` 追加后缀：`yi→" 亿"`、`wan→" 万"`；percent 用 formatter 呈现（数据为小数形态 `0.112`，显示 `(v*100).toFixed(1) + "%"`；副轴 `axisLabel.formatter` 同规则）。前端使用的数据值恒为 `0.112` 形态，**不改数据值**（§5.1）。

**下载约束**：跨域/同源一律 `fetch → blob → a[download]`，不直接用 `<a href>` 触发下载。

---

## 9. 项目文件结构建议

```
project-root/
├── SPEC.md                          # 本文档（唯一规格来源）
├── backend/
│   ├── requirements.txt             # 精确版本锁定
│   ├── requirements-dev.txt         # dev 依赖（pytest 等）
│   ├── pytest.ini                   # pythonpath=.，testpaths=tests
│   ├── .env.example                 # LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / CORS_ORIGINS
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口、CORS、路由注册
│   │   ├── config.py                # 环境变量读取（禁止硬编码密钥）
│   │   ├── api/
│   │   │   └── routes.py            # /api/parse /api/recommend /api/generate /api/health
│   │   ├── modules/
│   │   │   ├── parser.py            # M1（已实现）
│   │   │   ├── semantic.py          # M2（已实现）
│   │   │   ├── recommender.py       # M3：LLM client + 校验链 + 数据投影 + 降级
│   │   │   └── pptx_builder.py      # M4：python-pptx + ablechart + BreakLink 收尾
│   │   ├── schemas/                 # §5 全部 JSON Schema 文件（唯一事实源）
│   │   │   ├── raw_table.schema.json
│   │   │   ├── semantic_table.schema.json
│   │   │   ├── chart_spec.schema.json
│   │   │   ├── llm_recommendations.schema.json
│   │   │   └── generate_request.schema.json
│   │   └── validators.py            # V-1 ~ V-5 不变式校验（M3/M4 共用）
│   ├── spikes/
│   │   └── ablechart_spike.py       # M0 可行性验证脚本（门禁，通过后保留作回归）
│   └── tests/
│       ├── fixtures/
│       │   ├── sample.md            # §12 样例 Markdown 表格（6 行）
│       │   ├── sample.csv           # 测试时由 fixture 动态生成（避免二进制/编码文件入库）
│       │   └── sample.xlsx          # 同上
│       ├── test_parser.py           # A-1.x
│       ├── test_semantic.py         # A-2.x
│       ├── test_recommender.py      # A-3.x（LLM 全部 mock）
│       └── test_pptx_builder.py     # A-4.x（含解压产物断言）
└── frontend/
    ├── package.json
    └── src/
        ├── App.tsx                  # 三步页面流
        ├── api/client.ts            # fetch 封装、ApiError 处理、blob 下载
        ├── types/                   # TS 类型（镜像 backend/schemas，注释注明来源版本）
        ├── utils/specToOption.ts    # ChartSpec → ECharts option（唯一映射层）
        └── components/
            ├── DataInput.tsx        # 粘贴 + 拖拽上传
            ├── DataPreviewTable.tsx # 规整数据表（role/unit 徽标、null 高亮、列 warning）
            ├── ChartCard.tsx        # 单个候选图表卡片（ECharts）
            └── ChartPicker.tsx      # 勾选、排序、标题编辑
```

---

## 10. 关键依赖与版本

### 后端（`requirements.txt`，精确锁定）

| 依赖 | 版本约束 | 用途 |
|---|---|---|
| python | 3.11+ | 运行时 |
| fastapi | `>=0.115,<1.0` | Web 框架 |
| uvicorn[standard] | `>=0.30,<1.0` | ASGI 服务 |
| pydantic | `>=2.7,<3.0` | 请求/响应模型 |
| pandas | `>=2.2,<3.0` | 数据解析（Excel 路径） |
| openpyxl | `>=3.1,<4.0` | xlsx 读写 |
| python-pptx | `>=1.0.2,<2.0` | 原生图表 PPT 生成（C-1） |
| ablechart | `==0.2.0` | 组合图 `create_combo_chart`（M0 已初步确认可安装、函数存在；双轴/percent 能力待 M0 门禁验证） |
| jsonschema | `>=4.22,<5.0` | LLM 输出与契约校验 |
| httpx | `>=0.27,<1.0` | LLM API 异步调用 |
| python-multipart | `>=0.0.9` | 文件上传 |
| pytest | `>=8.2,<9.0` | 测试（dev 依赖，`requirements-dev.txt`） |

### 前端（`package.json`）

| 依赖 | 版本约束 | 用途 |
|---|---|---|
| react / react-dom | `^18.3` | UI |
| typescript | `^5.5` | 类型 |
| vite | `^5` | 构建（建议，非锁定项） |
| echarts | `^5.5` | 候选图表预览 |

### LLM 接入配置（环境变量，禁止硬编码）

| 变量 | 说明 |
|---|---|
| `LLM_API_KEY` | 密钥，仅后端持有 |
| `LLM_BASE_URL` | OpenAI 兼容接口地址 |
| `LLM_MODEL` | 模型名；要求支持 JSON object 输出模式 |

---

## 11. 错误码总表

| code | 触发场景 | HTTP |
|---|---|---|
| `PARSE_EMPTY` | 输入为空/无法识别表格 | 400 |
| `PARSE_TOO_LARGE` | 超 10MB / 超 10000 行 | 413 |
| `PARSE_UNSUPPORTED` | 不支持的文件类型/编码 | 400 |
| `LLM_INVALID_JSON` | LLM 输出非严格 JSON（重试耗尽） | 502（伴随降级结果时不报错） |
| `LLM_UNAVAILABLE` | LLM 服务不可达且降级失败 | 502 |
| `VALIDATION_FAILED` | ChartSpec/GenerateRequest 违反 Schema 或 V-1~V-8；或表中无可绘图数值列 | 400 |
| `PPTX_BUILD_FAILED` | pptx 构建异常 | 500 |

---

## 12. 测试夹具（样例数据，6 行）

以下 Markdown 表格为 `tests/fixtures/sample.md` 的标准内容（同内容的 csv/xlsx 版本由测试 fixture 动态生成）。覆盖：负同比（微博 -3.9%）、DAU 全缺失平台（微信、小红书）、DAU 完整平台（抖音等）、MAU 下降平台（快手、微博）。

```markdown
| 平台 | 2024 MAU | 2025 MAU | 同比 | 2024 DAU | 2025 DAU | 梯队 | 平台态势 |
|---|---|---|---|---|---|---|---|
| 微信 | 13.9亿 | 14.2亿 | +2.4% | 未披露 | 未披露 | 第二梯队 | 稳健 |
| 抖音 | 10.5亿 | 11.7亿 | +11.2% | 7.0亿 | 7.6亿 | 第一梯队 | 高增长 |
| 快手 | 7.2亿 | 7.0亿 | -2.8% | 4.1亿 | 4.0亿 | 第三梯队 | 存量承压 |
| 微博 | 5.9亿 | 5.7亿 | -3.9% | 2.6亿 | 2.5亿 | 第三梯队 | 收缩 |
| B站 | 3.4亿 | 3.7亿 | +8.8% | 1.0亿 | 1.1亿 | 第四梯队 | 社区增长 |
| 小红书 | 3.2亿 | 3.5亿 | +9.4% | 未披露 | 未披露 | 第四梯队 | 种草扩张 |
```

**端到端验收 checklist：**
- [ ] 粘贴样例文本 → 8 列 × 6 行正确展示，微信 / 小红书 DAU 高亮「缺失」
- [ ] 推荐列表同时覆盖趋势（line/slope）、体量对比（bar）、变化率（combo）三层；percent 走副轴、显示 `%`，微博 / 快手同比呈现负值
- [ ] 含 DAU 的推荐 reasoning 出现「该系列数据不完整，建议不纳入」提示，且无编造数值
- [ ] bar / line 图中微信 / 小红书 DAU 位置为空（缺柱 / 断线），不是 0
- [ ] 导出 pptx；解压校验通过（C-1/C-2/C-3/C-4，percent 写入值与 JSON 一致）
- [ ] WPS 打开，双击图表可编辑数据，无「链接文件不可用」
- [ ] 断开 LLM（改错 BASE_URL）→ 降级推荐仍可用（含 combo），导出正常

---

## 13. 风险与待验证事项

| 编号 | 事项 | 说明与预案 |
|---|---|---|
| R-1 | ablechart 的 `create_combo_chart` 双轴与 percent 能力 | **M0 门禁（§6 M0）必须先验证**：双轴 combo、副轴 percent 格式、写入值与 JSON 一致。若不满足，预案为 python-pptx 原生 XML 扩展实现副轴，仍保证 C-1（禁止图片化），并回写本 SPEC |
| R-2 | python-pptx 公共 BreakLink API 可用性 | 锁定版本若无公共 API，则实现等价的 XML/relationship 操作函数 `break_chart_links(prs)`，对外行为以 C-2 的验证方式为准（zip 解压断言外部链接不存在）；M0 顺带在真实 ablechart 产物上验证 |
| R-3 | LLM 的严格 JSON 数组能力差异 | 不依赖 `response_format`（OpenAI 的 json_object 只保证对象、不保证裸数组）：prompt 强约束裸数组 + 解析层容错（直接 parse → 剥围栏 → 兼容 `{"recommendations":[...]}` 包装）+ 失败重试 1 次；行为以 A-3.x 为准 |
| R-4 | slope/scatter/pie 的 pptx 呈现 | slope 按「两期 LINE_MARKERS + 端点标签」实现；scatter 用 XyChartData；pie 用 PIE；M4 实现时若与 ablechart 产物冲突，先回写 SPEC |
| R-5 | 瀑布/旭日无 python-pptx 原生类型 | waterfall 以 `COLUMN_STACKED`（透明底座 + 增量）等价实现，仍为原生可编辑 Chart（C-1 不违反）；sunburst 降级导出为 `DOUGHNUT` 近似，前端预览保留真旭日效果；若后续 python-pptx/ablechart 支持原生类型，先回写 SPEC 再升级 |
| R-6 | 放映动效的实现路线（v1.11 改判） | **v1.11 定论：放弃 OOXML `<p:timing>`/oleChartEl 原生图表分段动画，改走 GIF 动图路线。** 历史：v1.7~v1.10 四版 XML 注入在 WPS 实测全部失败（整图进入或完全无动画），且本环境无法运行 WPS 验证、只能盲改；根因是 WPS 对图表子元素动画（无论 oleChartEl 还是 bldChart 拆分）支持不可靠。**新方案**：前端离屏 ECharts 采帧 → 后端 PIL 合成循环 GIF（`save_all`+`duration`+`loop=0`）→ `add_picture` 嵌入 pptx。PPT/WPS 放映对 GIF 动图支持稳定，所见即所得。GIF 为位图不可编辑，但动效版是用户显式选择的独立产物（`chart-animated-{ts}.pptx`），**不影响 C-1**——C-1 仅约束标准导出端点（仍输出原生可编辑 Chart）。标准导出端点同步移除 `animate` 入参，不再有 p:timing 注入路径。验收 A-4.11 口径重写为「动效版 pptx 在 PPT/WPS 放映时 GIF 正常循环播放」 |

---

## 14. 实施顺序（里程碑，无时间预估）

0. **M0 ablechart 可行性验证**（✅ 已通过，脚本 `backend/spikes/ablechart_spike.py`）：五项目标达成——ablechart 0.2.0 可安装；`create_combo_chart` 生成 barChart+lineChart+双 valAx；副轴 percent 不换算、轴上写 `numFmt=0.0%`；图表原生（`ppt/charts/chart1.xml`），数据为**内部**嵌入 workbook（rel `../embeddings/*.xlsx`，无 `TargetMode=External`）；python-pptx 默认写 `<c:dispBlanksAs val="gap">`；combo 对象的 `replace_data(CategoryChartData)` 可更新内嵌数据。C-2 的工程落点据此定为 §11 R-2。
1. **M1 + M2 + validators**（✅ 已落地）：parser/semantic 与 `/api/parse`；validators V-1~V-8 随 M3 落地。6 行样例夹具、A-1.x/A-2.x 测试通过。
2. **M3**（✅ 已落地）：mock LLM（A-3.x 全绿）+ 真实 LLM 接入（OpenAI 兼容，模型名走环境变量）；`/api/recommend` 已实现。
3. **前端三步页面**（✅ 已落地）：`/api/parse`、`/api/recommend` 联调，ECharts 候选预览 + 选中全局 state 走通；导出按钮尚未接 `/api/generate-pptx`（待端到端联调）。
4. **M4 单图导出**（✅ 已落地 `/api/generate-pptx`，A-4.1~A-4.6 自动化通过）：line/bar/combo 三类；剩 WPS/Office 人工双击验收（§12 checklist）。多图 deck 端点 `/api/generate` 与 slope/scatter/pie 导出为后续里程碑。

每个里程碑完成的标准 = 对应验收标准全部通过，而非「代码写完」。
