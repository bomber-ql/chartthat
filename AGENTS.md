# AGENTS.md

## 项目概览
智能数据图表 PPT 生成器：用户输入文本/CSV/Excel，后端解析数据语义，LLM 推荐图表（十三种：bar/hbar/line/area/combo/stacked/slope/scatter/waterfall/radar/pie/donut/sunburst），前端 ECharts 预览，最终由 python-pptx + ablechart 生成含**原生可编辑 Chart 对象**的 .pptx。

**唯一规格来源：`SPEC.md`（v1.11）。任何代码实现必须先与 SPEC 对齐，冲突时先回写 SPEC。**

## 架构
- `backend/`：FastAPI（Python 3.12），模块 M1 parser / M2 semantic / M3 recommender / M4 pptx_builder，契约见 SPEC §5/§6。
- `frontend/`：React 18 + TypeScript + Vite 5 + ECharts 5；`ChartSpec` 是前后端共享的唯一图表事实源，映射层为 `src/utils/specToOption.ts`。
  - 已实现**左右分布单工作区**（深色科技感，DESIGN.md）：左 `ControlPanel`（输入→/api/parse **成功后自动调 /api/recommend**、解析摘要、已选清单、导出）+ 右 `PreviewPanel`（`ChartCard` 卡片网格，ECharts 缩略图 + reasoning，点击选中全局 state）；导出已接 /api/generate-pptx（十三种图型逐张下载 .pptx，v1.6 起全覆盖）。无页签三步流已废弃；「解析」与「生成图表」已合并为一次点击。响应式：≤1080px 上下单列 + **自然文档流**（`.workspace` overflow 必须 visible，整页随 body 滚动，内部滚动会导致移动端候选区显示不完整）、≤640px 手机端卡片单列全宽 + 顶栏压缩 + 隐藏四角装饰 + 预览面板头部折行（文字占满整行，提示文案不被按钮挤压成竖长条）（`styles.css` 媒体查询）。
  - **双主题 + 中英双语**：`src/theme.tsx`（`data-theme` 写根节点，深色默认，localStorage `dc-theme`）+ `src/i18n.tsx`（zh 默认，localStorage `dc-lang`；界面框架文案全入 STRINGS 字典，组件一律 `useI18n()` 取词；图表标题/reasoning/列名等数据内容保持后端原文）。样式全部走 CSS 变量（`styles.css` `:root` 深色 / `[data-theme='light']` 浅色），ECharts 色板由 `specToOption(spec, theme)` 双套 token 切换；顶栏右侧有主题/语言切换按钮。
  - `ChartSpec` → ECharts option 的唯一映射层为 `src/utils/specToOption.ts`（十三型；combo 柱主轴 + percent 折线副轴，tooltip/label 层 ×100 显示百分比；`connectNulls:false` 断线；hbar 轴互换 inverse、stacked 同 stack、area 半透明填充、waterfall 透明底座+增量同 stack、radar indicator 上限=最大值×1.2、donut 空心半径、sunburst 单层嵌套）。
- dev：Vite 监听对外端口 `${DEPLOY_RUN_PORT}`（主仓 5000），`/api` 代理到 FastAPI 127.0.0.1:8000。
- prod：`pnpm build` 产出 `frontend/dist`，FastAPI 监听 `${DEPLOY_RUN_PORT}` 并托管 dist（SPA fallback 已在 `main.py` 实现）。

## 常用命令
- 安装全部依赖：`bash scripts/setup.sh`
- 本地开发：`bash scripts/dev.sh`
- 生产构建：`bash scripts/build.sh`
- 生产运行：`bash scripts/start.sh`
- 后端单独运行：`cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 前端单独运行：`cd frontend && pnpm run dev`（需 DEPLOY_RUN_PORT 环境变量）
- 后端测试：`cd backend && python3 -m pytest`

## 代码风格
- Python：类型标注齐全（`from __future__ import annotations`），pydantic v2 模型；不硬编码任何密钥/端口，端口读 `DEPLOY_RUN_PORT`/`BACKEND_PORT`。
- TypeScript：strict 模式；React 17+ JSX runtime，不写 `import React`（除非显式使用 React API）。
- 标点符号代码内一律半角；提交信息遵循 Conventional Commits。

## 核心约束（实现时不可违反，详见 SPEC §3）
- C-1 pptx 图表只能走 `add_chart` / ablechart `create_*_chart`，禁止图片嵌入。
- C-2 保存前遍历 has_chart shapes，IsLinked 则断链（WPS 双击不弹"链接文件不可用"）。
- C-3 缺失值全程 None/null/空点，禁止转 0。
- C-4 percent 列独立识别，组合图挂副轴，不与亿级数值同轴。
- C-5 LLM 仅输出列引用（十三种 chart_type 枚举、严格 JSON），数据由后端投影填充。

## 测试说明
- 后端测试位于 `backend/tests/`，夹具 `sample.md` 内容见 SPEC §12（csv/xlsx 变体由测试动态生成，.gitignore 忽略不落盘）；LLM 测试一律 mock。
- 运行后端测试需先装 dev 依赖：`python3 -m pip install -r backend/requirements-dev.txt`（`scripts/setup.sh` 已包含），然后 `cd backend && python3 -m pytest`。
- M1/M2 已实现：`backend/app/modules/parser.py`（文本/CSV/Excel → RawTable）、`semantic.py`（→ SemanticTable），入口 `parse_input`；percent 为小数形态（11.2% → 0.112，SPEC §5.1 v1.2）。
- M3 已实现：`backend/app/modules/recommender.py`（OpenAI 兼容调用、裸 JSON 数组容错解析+失败重试 1 次、列引用投影填充、三语义层 trend/comparison/rate 覆盖、缺失系列追加固定提示语、LLM 不可用/产出为空时启发式降级 `degraded=true`）；校验在 `backend/app/validators.py`（V-1~V-12：V-9 stacked ≥2 同单位、V-10 waterfall 恰好 1 系列、V-11 radar ≥3 同单位、V-12 donut/sunburst 同 pie 口径；percent 仅允许 bar/hbar/line/area/combo）。MAX_RECOMMENDATIONS=8，降级变体含 area/stacked/radar/donut。LLM 测试全部注入 `llm_call` mock，禁止真实网络调用。
- M4 已实现（`backend/app/modules/pptx_builder.py`，SPEC v1.4 §5.6/§6）：端点 `POST /api/generate-pptx`，入参自描述 `{chart_type, config?, data:{categories, series:[{name,kind,axis,unit,data}]}}`，返回 `attachment; filename=chart-<ts>.pptx`（PK 魔数、正确 MIME）。
  - **v1.11 动效版导出（GIF 路线，SPEC §5.6a/§6a，R-6）**：独立端点 `POST /api/generate-animated-pptx`，入参 `{title?, frames: string[]（base64 PNG dataURL，≥2 帧）, frame_ms?（默认 100，20~2000）}`，返回 `chart-animated-<ts>.pptx`。后端 `backend/app/modules/gif_builder.py`：PIL 逐帧解码 → 首帧 `save(format='GIF', save_all=True, append_images, duration=frame_ms, loop=0)` 合成循环动图 → 16:9 空白页可选标题 + `add_picture` 等比缩放居中嵌入。前端 `src/utils/captureFrames.ts`：隐藏容器离屏 `echarts.init`（devicePixelRatio 2）+ `specToOption(spec, theme)` setOption 播绘制动画，每 100ms 采 `canvas.toDataURL('image/png')` 共 ~20 帧（1.9s）后 dispose；App.tsx `exportPptx(animate=true)` 改为采帧上传新端点（标准导出仍走 `/api/generate-pptx`，两个独立按钮互不影响）。**历史教训（v1.7~v1.10，已废弃）**：OOXML `<p:timing>`/oleChartEl 原生图表分段动画在 WPS 实测四版皆败（整图进入或完全无动画），沙箱无法运行 WPS 验证只能盲改 → 定论 WPS 对图表子元素动画支持不可靠，模块 `pptx_animation.py` 已删除，标准端点移除 `animate` 入参。GIF 为位图不可编辑，但不违 C-1（C-1 仅约束标准导出端点）。Pillow 已入 requirements.txt。
  - **v1.8 面积图 kind 修复**：降级路径曾把 area 序列 `kind` 误置 `bar`（前端 `cartesianSeries` 用 `s.kind` 渲染 → 面积图显示成柱状），已修为恒 `line`；前端 `areaOption` 同步强制 `type:'line'` 兜底。
  - line/bar 走 python-pptx `add_chart + CategoryChartData`；combo 走 `ablechart.create_combo_chart`（bar 主轴 + line 副轴）；None 原样传入（CategoryChartData 空点 / DataFrame NaN），禁 0。
  - 格式：折线显式写 `<c:dispBlanksAs val="gap"/>`；副轴 `numFmt=0.0%`（percent 数据恒为小数，不换算），主轴 `0.0"亿"` / `0.0"万"`（数值是换算后的绝对值）。
  - C-2 等价实现（M0 spike 结论，见 SPEC §11 R-2）：python-pptx/ablechart 无 `BreakLink()` API，且内嵌 `c:externalData r:id` 指向**内部** `embeddings/*.xlsx` 是 WPS 可双击编辑的依据（IsLinked=False），不得删除；builder 仅移除 `TargetMode="External"` 的关系（外部 .xlsx 才是 IsLinked=True）。
  - v1.5 起六图型全部支持导出：slope=两期 LINE_MARKERS+gap、scatter=XyChartData（无效点剔除）、pie=PIE（null 扇区剔除）；`UNSUPPORTED_CHART` 错误码已移除，未知类型与契约错误均 400 `VALIDATION_FAILED`；构建异常 500 `PPTX_BUILD_FAILED`。scatter 恰好 2 系列、pie 恰好 1 系列、slope/scatter/pie 禁 percent。
  - v1.6 起扩展为**十三图型**（新增 hbar/stacked/donut/area/waterfall/radar/sunburst，映射表见 SPEC §6）：hbar=BAR_CLUSTERED、area=AREA、stacked=COLUMN_STACKED、radar=RADAR_MARKERS（categories=指标名、系列=各实体）、donut=DOUGHNUT；**waterfall 无原生枚举**→COLUMN_STACKED 等价（R-5）：「底座」系列透明（`format.fill.background()`）+「增量」系列，取值口径 **底座=min(前值累计,后值累计)、增量=|原始增量|**（堆叠负值会回落零轴下方，必须翻转垫高），None 增量保持空点；**sunburst 降级 DOUGHNUT**（R-5，前端预览仍为真旭日）。形态校验：donut/sunburst/waterfall 恰好 1 系列、stacked ≥2 同单位、radar ≥3 同单位，新类型（除 hbar/area）禁 percent。
  - M0 spike 已通过：`backend/spikes/ablechart_spike.py`（pip 安装、双轴 combo、副轴 percent 生效、内部嵌入、line gap 默认、combo `replace_data` 可更新）。
- M4 测试在 `backend/tests/test_pptx_builder.py`（TestClient 直接打 ASGI，无网络）：断言无 External rel、combo 含 barChart+lineChart+双 valAx+0.0%、`replace_data` 后重存读回值更新、null→gap 且无伪 0、v1.6 七新图型 plot 标记（barDir=bar/areaChart/stacked/radarChart/doughnutChart/waterfall 底座透明+累计口径）、形态与 percent 违规 400、端点 .pptx 冒烟、v1.11 标准版无 `<p:timing>`（即便误传 animate 也忽略）。M4b 测试在 `backend/tests/test_gif_builder.py`（GIF89a 魔数/n_frames/loop=0/duration、slide 含图片 shape、非法入参 400、端点 chart-animated 文件名冒烟）。validators 单测在 `backend/tests/test_validators.py`（V-9~V-12 与 percent 口径，最小表直造）。
- 交付前用 test_run 跑静态检查 + 接口冒烟（已实现 `/api/health`、`/api/parse`、`/api/recommend`、`/api/generate-pptx`、`/api/generate-animated-pptx`；多图 deck 端点 `/api/generate` 为后续里程碑）。recommend/generate-pptx 冒烟注意 pipeline 会给 curl 追加 `-w` 尾巴，落盘文件再 `json.load` 会 Extra data，需用 Python urllib 串联或提取纯 JSON；**`/api/recommend` 入参是裸 SemanticTable JSON（不要包 `{"table": ...}`）**。十三图型导出冒烟脚本：`python3 scripts/smoke_pptx_export.py`（逐型断言 PK 魔数/.pptx 文件名/plot 标记/无 External rels）。
