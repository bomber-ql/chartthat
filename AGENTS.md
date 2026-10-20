# AGENTS.md

## 项目概览
智能数据图表 PPT 生成器：用户输入文本/CSV/Excel，后端解析数据语义，LLM 推荐图表（line/bar/combo/slope/scatter/pie），前端 ECharts 预览，最终由 python-pptx + ablechart 生成含**原生可编辑 Chart 对象**的 .pptx。

**唯一规格来源：`SPEC.md`（v1.0，待评审）。任何代码实现必须先与 SPEC 对齐，冲突时先回写 SPEC。**

## 架构
- `backend/`：FastAPI（Python 3.12），模块 M1 parser / M2 semantic / M3 recommender / M4 pptx_builder，契约见 SPEC §5/§6。
- `frontend/`：React 18 + TypeScript + Vite 5 + ECharts 5；`ChartSpec` 是前后端共享的唯一图表事实源，映射层为 `src/utils/specToOption.ts`。
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
- M4 验收需解压 pptx 断言 `ppt/charts/chartN.xml` 存在且无外部数据链接（SPEC A-4.x）；M4 开工前必须先跑通 M0 ablechart spike（`backend/spikes/`，SPEC §14）。
- 交付前用 test_run 跑静态检查 + 接口冒烟（已实现 `/api/health`、`/api/parse`、`/api/recommend`；`/api/generate` 随 M4 补齐）。recommend 冒烟注意 pipeline 会给 curl 追加 `-w` 尾巴，落盘文件再 `json.load` 会 Extra data，需用 Python urllib 串联或提取纯 JSON。
