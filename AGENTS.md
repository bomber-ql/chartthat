# AGENTS.md

## 项目概览
智能数据图表 PPT 生成器：用户输入文本/CSV/Excel，后端解析数据语义，LLM 推荐图表（line/bar/combo/slope/scatter/pie），前端 ECharts 预览，最终由 python-pptx + ablechart 生成含**原生可编辑 Chart 对象**的 .pptx。

**唯一规格来源：`SPEC.md`（v1.0，待评审）。任何代码实现必须先与 SPEC 对齐，冲突时先回写 SPEC。**

## 架构
- `backend/`：FastAPI（Python 3.12），模块 M1 parser / M2 semantic / M3 recommender / M4 pptx_builder，契约见 SPEC §5/§6。
- `frontend/`：React 18 + TypeScript + Vite 5 + ECharts 5；`ChartSpec` 是前后端共享的唯一图表事实源，映射层为 `src/utils/specToOption.ts`。
  - 已实现三步流程：`InputStep`（文本/文件→/api/parse）→ `PreviewStep`（/api/recommend → `ChartCard` 卡片网格，ECharts 缩略图 + reasoning，点击选中全局 state）→ `ExportStep`（已能展示选中图表；下载按钮尚未接 /api/generate-pptx）。
  - `ChartSpec` → ECharts option 的唯一映射层为 `src/utils/specToOption.ts`（line/bar/combo/slope/scatter/pie；combo 柱主轴 + percent 折线副轴，tooltip/label 层 ×100 显示百分比；`connectNulls:false` 断线）。
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
- C-5 LLM 仅输出列引用（六种 chart_type 枚举、严格 JSON），数据由后端投影填充。

## 测试说明
- 后端测试位于 `backend/tests/`，夹具 `sample.md` 内容见 SPEC §12（csv/xlsx 变体由测试动态生成，.gitignore 忽略不落盘）；LLM 测试一律 mock。
- 运行后端测试需先装 dev 依赖：`python3 -m pip install -r backend/requirements-dev.txt`（`scripts/setup.sh` 已包含），然后 `cd backend && python3 -m pytest`。
- M1/M2 已实现：`backend/app/modules/parser.py`（文本/CSV/Excel → RawTable）、`semantic.py`（→ SemanticTable），入口 `parse_input`；percent 为小数形态（11.2% → 0.112，SPEC §5.1 v1.2）。
- M3 已实现：`backend/app/modules/recommender.py`（OpenAI 兼容调用、裸 JSON 数组容错解析+失败重试 1 次、列引用投影填充、三语义层 trend/comparison/rate 覆盖、缺失系列追加固定提示语、LLM 不可用/产出为空时启发式降级 `degraded=true`）；校验在 `backend/app/validators.py`（V-1~V-8）。LLM 测试全部注入 `llm_call` mock，禁止真实网络调用。
- M4 已实现（`backend/app/modules/pptx_builder.py`，SPEC v1.4 §5.6/§6）：端点 `POST /api/generate-pptx`，入参自描述 `{chart_type, config?, data:{categories, series:[{name,kind,axis,unit,data}]}}`，返回 `attachment; filename=chart-<ts>.pptx`（PK 魔数、正确 MIME）。
  - line/bar 走 python-pptx `add_chart + CategoryChartData`；combo 走 `ablechart.create_combo_chart`（bar 主轴 + line 副轴）；None 原样传入（CategoryChartData 空点 / DataFrame NaN），禁 0。
  - 格式：折线显式写 `<c:dispBlanksAs val="gap"/>`；副轴 `numFmt=0.0%`（percent 数据恒为小数，不换算），主轴 `0.0"亿"` / `0.0"万"`（数值是换算后的绝对值）。
  - C-2 等价实现（M0 spike 结论，见 SPEC §11 R-2）：python-pptx/ablechart 无 `BreakLink()` API，且内嵌 `c:externalData r:id` 指向**内部** `embeddings/*.xlsx` 是 WPS 可双击编辑的依据（IsLinked=False），不得删除；builder 仅移除 `TargetMode="External"` 的关系（外部 .xlsx 才是 IsLinked=True）。
  - slope/scatter/pie 返回 400 `UNSUPPORTED_CHART`；契约错误 400 `VALIDATION_FAILED`；构建异常 500 `PPTX_BUILD_FAILED`。
  - M0 spike 已通过：`backend/spikes/ablechart_spike.py`（pip 安装、双轴 combo、副轴 percent 生效、内部嵌入、line gap 默认、combo `replace_data` 可更新）。
- M4 测试在 `backend/tests/test_pptx_builder.py`（10 例，TestClient 直接打 ASGI，无网络）：断言无 External rel、combo 含 barChart+lineChart+双 valAx+0.0%、`replace_data` 后重存读回值更新、null→gap 且无伪 0、400 分支、端点 .pptx 冒烟。
- 交付前用 test_run 跑静态检查 + 接口冒烟（已实现 `/api/health`、`/api/parse`、`/api/recommend`、`/api/generate-pptx`；多图 deck 端点 `/api/generate` 为后续里程碑）。recommend/generate-pptx 冒烟注意 pipeline 会给 curl 追加 `-w` 尾巴，落盘文件再 `json.load` 会 Extra data，需用 Python urllib 串联或提取纯 JSON。
