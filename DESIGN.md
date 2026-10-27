# DESIGN.md

## 品牌
- 产品名：**ChartThat**（chartthat.com）；顶栏品牌字为驼峰 `ChartThat`（品牌渐变字，字距收紧 0.02em，不再全大写拉开）。
- 口号：互动交换式——中「数据给我，图表给你」（人称互动、最好懂）、英 `Data in, charts out.`（in/out 押韵极简）；法/德/西走口语+押韵+有趣，不强求同构：法 «Des données ? Hop, des graphiques !»（Hop=变戏法语气词"变！"）、德 „Daten her, Diagramme hin.“（her/hin 方向对子，her 隐含"交给我"）、西 «Pásame datos, te paso gráficos.»（pásame/te paso 押韵，"传给我/传给你"）；置于顶栏副标题位（brandSub）与空态 hero，浏览器 title 跟随英文版。
- 产品介绍：右列空态（首次到访第一眼）承载品牌 hero——大号产品名 + 口号 + 一句话介绍（粘贴数据→十三种图表→PPTX/GIF）+ 三枚特性胶囊（图型数 / 原生可编辑 PPTX / 动效 GIF），下方保留原空态引导。
- 分享组件：导出区底部 `.share-row`——等宽字体大写小标签 + 文字徽章按钮（X / in / f / r/ / 复制链接），幽灵边框 hover 变青上浮；链接带 `?ref=share-<平台>` 归因参数；OG 预览图 `/og.jpg`（1200×630 深空控制台品牌图），全平台（X/Facebook/LinkedIn/WhatsApp/Telegram 等）链接预览经 OG/Twitter Card meta 一次接入。
- Logo：对话气泡 + 上升折线 SVG（`Logo.tsx`，方向 B——「数据给我，图表给你」的对话感 + 数据变图表的上升线）；气泡描边/底色走主题变量深浅自适应，折线固定青蓝品牌渐变；实例化多处时渐变 id 用 `useId` 防冲突。出现位：顶栏品牌位（32px）、空态 hero（58px 带青色投影）、favicon.svg（深色圆角方块底 + 标记）。

## 气质与意象
深空控制台：像太空任务指挥中心的操作台——深色空间中悬浮着半透明玻璃面板，数据流以青色光带穿行。克制、精密、冷冽，发光只用于指引视线，不做炫技。

## 布局与信息架构
- **左右分布单工作区**（本版核心变更）：左列固定 400px 控制台（数据输入 → 解析摘要 → 已选清单 → 导出），右列弹性画布（候选图表卡片网格）；顶部一条通栏品牌栏。三步流程收拢为同屏流水线，无页签跳转。
- 右侧候选卡片网格：`repeat(auto-fill, minmax(320px, 1fr))`，按语义层（趋势 / 体量对比 / 变化率）分组，组标题为青色侧光条 + 大写英文标签。

## 内容区与静态页（SEO / AdSense 审核，v1.21 起）
- **页面滚动模型变更**：桌面端从「100vh 禁滚动应用壳」改为「首屏 100vh 应用壳（`.stage` = topbar + workspace，内部滚动行为不变）+ 下方内容区随 body 滚动」。背景光晕（`.shell::before`）与网格（`.bg-grid`）改 `position: fixed`，不随滚动。
- **内容区多语言双轨制（v1.22）**：`index.html` 的 `#root` 之外、`<div id="site-content">` 内嵌**静态英文版**（爬虫零渲染可见，SEO 基底）；React 启动时 `main.tsx` 清空容器，`App.tsx` 用 `createPortal` 把 `<SiteContent/>` 渲染回同一容器（同树共享 I18nProvider），按界面语言呈现**五语言版**。View Source 恒为英文，用户所见随界面语言。文案单一事实源是 `SiteContent.tsx` 的 `SITE_COPY` 五语言字典；静态英文版必须与其 `en` 分支逐字一致。
- **内容区布局（v1.23 加宽）**：容器与页脚 `max-width: 1400px`（与工作区同边距贯通，消除「全宽顶栏+居中孤岛」断层）；文字栏仍限宽保可读（`.c-prose` 740px、`.faq` 860px）；人群场景 4 列一排。
- **内容区五大区块**：开发故事（3 段，**强调** 转 strong）→ How it works（**左三步纵向编号 01/02/03 渐变字 + 右侧 `.perks` 优势宣传栏**（玻璃卡、checkmark 列表、桌面端 sticky），≤1080 收单列）→ 十三图型速查 → 人群场景（`.case-card` 4 卡：咨询/营销广告/运营产品/分析学生，**卡头 3:2 人物插画**（AI 生成扁平风 `/case-*.jpg`，与故事区同色系））→ FAQ 9 条。
- **独立静态页多语言（v1.23）**：`/about.html` 正文五语言块 `data-lang-block="en|zh|fr|de|es"`——head 内联脚本首帧前写 `<html data-lang>`（dc-lang 优先、浏览器前缀其次、en 兜底，与 i18n.tsx 同规则），CSS 按属性显隐（无 JS 默认英文，爬虫基底）；body 尾脚本仅更新 back 链接/title/meta description。privacy.html 保持英文（法律文本不机翻）。
- **故事区插画（v1.23）**：`.story-grid` 左文右图（7fr/5fr），右栏单张 AI 生成扁平商务插画 `/story-pain.jpg`（痛点：深夜被 PPT 图表包围）——深蓝底 + 青色点缀贴合深空控制台，2048×1365 JPEG（原 2048² 中心裁 3:2，quality 82），`width/height` 防 CLS + `loading="lazy"`，alt 五语言入 `SITE_COPY.storyArtAlt`（单条）；静态英文版同结构同图片。解法图 `/story-flow.jpg` 与收工图 `/story-relief.jpg`（周五傍晚合上电脑）在 `/about.html`——完整故事页五语言块各嵌 3 张（痛点段后/解法段后/落款前，`.sp-art` 整宽圆角卡），叙事节奏：痛点 → 解法 → 圆满收尾。
- 组件语言：区块标题 `.c-title`（青色大写 + 左侧 3px 渐变侧光条）；图型速查 `.cg-card` 玻璃卡片（hover 上浮 2px + 边框提亮）——**卡头为真实 ECharts 迷你演示（v1.23）**：React 版 `ChartMini`（demo spec 与迷你化覆写在 `utils/chartMiniData.ts`：隐藏坐标轴/图例/标签/交互、网格贴边、silent，纯形态展示；`specToOption` 同管线双主题联动；入场播一次绘制动画 + hover 重播，`prefers-reduced-motion` 停播；内置固定 demo 数据不走生成管线）；**静态英文版保留 `.cg-head` = `.cg-icon`（24px 线性 SVG）+ `.cg-name`**（爬虫基底零渲染可见）；卡尾 `.cg-meta`（虚线分隔，`.cg-needs` 数据要求带青色小标签 `.cg-tag` + `.cg-eg` 斜体示例）；FAQ 用原生 `<details>` 手风琴（无 JS、SEO 友好），`+` 号旋转 45°。
- **页头内容链接**：topbar 右侧「About」锚点（`.tb-link`，指向 `#site-content`，`html{scroll-behavior:smooth}`）+ GitHub 图标（`.tb-icon`）。
- **页脚 `.site-footer`**：玻璃顶边条——品牌渐变字 + 口号 / About·Privacy·GitHub 导航 / 版权行。
- **独立静态页** `/about.html`（完整开发故事 + `.sp-table` 对比表 vs AI 聊天机器人/插件/BI 工具——末列 ChartThat 青色高亮）、`/privacy.html`（隐私政策，诚实对应实际数据行为；含 Contact 段指向 GitHub Issues）：Vite 多页构建（rollupOptions.input），复用 styles.css；`<head>` 内嵌 localStorage `dc-theme` 主题检测脚本防闪烁；`.sp-*` 文章版式（760px 中栏、h2 侧光条、`.sp-back` 幽灵返回按钮）。
- `index.html`：`lang="en"`（出海定位）；JSON-LD `WebApplication` 结构化数据（免费、十三图型、PPTX/GIF 卖点）；`public/robots.txt` + `public/sitemap.xml`（3 URL，Vite 原样入 dist）。

## 响应式
- **≤1080px（平板/小桌面）**：左右工作区改为上下单列，**自然文档流**——`.shell` 高度自适应、`.workspace` 禁内部滚动（overflow 必须 visible），整页随 body 滚动；**flex 链同步解除拉伸**：`.workspace` / `.main .scroll` / `.empty` 必须 `flex: none`（column flex 链上 `flex:1` basis 0% + `min-height:0` 会把工作区压成「100vh − 顶栏」固定高，grid 内容溢出盒外与下方内容区重叠穿透）；底部导出条由 sticky 改为随文档流；How it works 三步骤卡改单列；故事区 `.story-grid` 改单列（插画落文字下）；人群场景 4 列降 2 列。
- **≤640px（手机）**：候选卡片单列全宽（弃用 320px minmax，杜绝横向溢出）；顶栏压缩——状态只留圆点、品牌副标题省略号截断；隐藏四角括号装饰（小屏噪点）；各区块 padding/gap 收紧；预览面板头部允许折行——标题/提示文字占满整行、操作按钮换到下一行，避免提示文案被挤压成竖长条；人群场景卡改单列。

## 色彩（深色科技感）
- 底色：深空 `#060a13`，面板玻璃 `rgba(13,20,36,.72)` + 12px 背景模糊。
- 主光：青 `#22d3ee`，辅光：蓝 `#3b82f6`；强调渐变 `linear-gradient(135deg,#22d3ee,#3b82f6)` 仅用于主按钮、选中描边、进度光带。
- 文字：主 `#e2e8f0`，次 `--dim #a8b6cf`（11-12px 小字对比度 ~8:1，历经 #7c8aa5 → #93a1bd → #a8b6cf 两轮提亮），强调级次级 `--dim-hi #c3cde0`（hero 介绍、特性胶囊）；边框 `rgba(56,189,248,.14)`。
- 语义色：缺失徽标告警 `#fb7185`（底 `rgba(251,113,133,.12)`）；降级提示琥珀 `#fbbf24`。
- 发光：选中卡 `0 0 24px rgba(34,211,238,.22)` + 1px 青色描边；主按钮 hover 光晕扩散。

## 字体排版
- 展示字（拉丁/数字/标题）：Chakra Petch；中文正文回退 PingFang SC / system-ui。数据输入区与表格用 JetBrains Mono 等宽。
- 品牌标题 17px 加粗字距拉开；面板标题 14px；reasoning 12px 次级；组标题 12px 全大写字距 .18em。

## 背景与装饰
- 页面底层：径向青光晕（左上 25% 透明）+ 1px 深色网格线纹理 + 四角细括号装饰（`.corner`），营造控制台面感；不叠加高饱和紫蓝大渐变。
- 面板 1px 青边 + 顶部 2px 渐变光条；输入框聚焦时青色内发光。

## 交互与状态
- 卡片选中：青色描边 + 外发光 + 右上 ✓ 亮青；hover 卡片上浮 2px、边框提亮。
- 缩略图底：深色网格纹；ECharts 配色换为青蓝系发光色板，坐标轴/文字改浅色适配深底。
- 按钮：主按钮渐变底 + 深色文字 + hover 光晕；幽灵按钮透明青边。加载态用脉冲光点。
- 页面动效统一 `cubic-bezier(.22,.61,.36,1)`，时长 180–260ms，不做弹性过冲。

## 内容系列：Charts That Sell（提案老兵的图表手记）
- **人设**：营销行业多年、靠 B2B 提案赢单的老手。图表观：图表不是证据陈列，是销售道具——客户为「无法反驳的结论」买单，数据永远服务于要卖的那个结论，结论指向需求，需求由解决方案接住。核心信条：先写结论句（slide 标题即主张），再倒推选图与摆数。
- **文风**：第一人称、战场感（周五深夜/周一早会/客户会议室）；断言式短句、敢下狠判断、反学院派（不写「数据可视化最佳实践」式正确的废话）；每条技巧落到「提案现场怎么帮你赢/怎么让你死」。
- **内容三层架构**：The Story（叙事：金字塔/SCQA/结论先行）→ The Charts（选型/一图一主张/改样式/配色）→ The Data（清洗/缺失值）。
- **版式**（`.g-*`，sp-* 之上的增量）：`.g-kicker` 系列标签（mono 大写青色）→ h1 → `.sp-sub` 期号与时长 → 正文 → `.g-fig` 示意图卡（极简 SVG，CSS 变量双主题）→ `.g-pull` 金句左光条 → `.g-cta` 文末回工具卡 → `.g-sign` 斜体署名。
- **语言策略**：英文单语先行（AdSense 审查看英文内容厚度），审查过后再补多语言；页头主题预检测脚本保留，无 data-lang-block。
- **页面机制**：`frontend/guides/*.html` 独立静态页（Vite 多页 input 逐篇注册），Article JSON-LD + canonical + OG；sitemap 与首页页脚 Guides 链接（指向索引页 `/guides/`）同步。
- **索引页 `/guides/index.html`**：系列封面 + 全 8 篇按三层架构分组（页面顺序 The Charts #1-4 → The Data #5-6 → The Story #7-8，期号即发布序）；卡片复用 `.g-grid`（2 列，移动 1 列）+ `.g-card`（玻璃卡 hover 上浮）。早期「未发布 `.g-soon` 占位」方案已废弃——2/8 可点让页面像半成品（v1.27 起改为发布一篇加一张卡，8 篇已全部上线）。
- **首页导引区（fn\*，cases 与 faq 之间）**：`.fn-intro` 一句话定位 + 已发布篇 `.g-card` 列表 + `.fn-more` 指向索引页；文案入 SITE_COPY 五语言字典（fnTitle/fnIntro/fnCta/fnNotes，文章标题保持英文、desc 本地化、num 手记期号本地化），静态英文版逐字同步 en 分支。
- **生产托管**：`/guides/` 目录形式依赖 main.py `spa_fallback` 的目录 index.html 支持（candidate 为目录时补查其下 index.html），勿回退。

## 图型落地页：/make/（v1.27）
- **定位**：十三个图型各一页英文单语落地页（`frontend/make/*.html`），吃「xxx chart maker」类工具词搜索流量；与 guides（方法论长文）分工——make 页答「这个图怎么做/何时用」，文末互链回 guides。
- **页面骨架**（复用 sp-* 版式 + `.g-*` 组件）：g-kicker（Chart maker · 图型名）→ h1「Xxx chart maker」→ sp-sub 一句话定位 → `.mk-demo` 内联 SVG 演示（640×320，玻璃卡包裹，fill/stroke 全走 `var(--accent)`/`var(--accent-2)`/`var(--dim)` 等 CSS 变量实现双主题；legend 色块透明度用 fill-opacity，rect 无 stroke）→ Paste/pick/download 三步 → `.mk-cols` 双栏（When it wins / When it lets you down，含页间互链）→ `.sp-table` 示例数据（可直接复制进工具）→ mk-tips 四条 Field notes → g-cta 跳首页 → 12 个 `.mk-chip` 互链 → guides 互链 → g-sign。
- **`.mk-*` 样式**（styles.css，插于 `.g-soon` 后 `.fn-*` 前）：mk-demo / mk-cols（≤900px 收单列）/ mk-h3（mono 青色小节题）/ mk-tips（li::before 渐变短横 marker）/ mk-chips + mk-chip（胶囊链接，--chip-bg 双主题已有）。
- **head 全要素**：主题预检测（仅 dc-theme，无语言块）+ AdSense 脚本 + HowTo & BreadcrumbList JSON-LD + canonical + OG；英文单语 lang="en"。
- **诚实声明**：sunburst 页明说 PPTX 导出降级为环形（预览/ GIF 为真旭日，R-5）。
- **文件命名**：scatter-plot.html（搜索量大于 scatter chart）、horizontal-bar-chart.html（非 hbar）。
- **索引页 `/make/index.html`**：13 卡按四语义分组 Compare（bar/hbar/stacked/waterfall）→ Track change（line/area/slope/combo）→ Show composition（pie/donut/sunburst）→ Reveal relationships（scatter/radar），复用 g-grid/g-card，ItemList + BreadcrumbList JSON-LD。
- **注册链**：vite.config input +14（makeIndex/makeBar/…）、sitemap +14 URL（make/ 索引 weekly 0.8，页 monthly 0.7）、首页静态页脚 `.sf-nav` 加「Chart makers」（Guides 与 Privacy 之间）；顶栏不加入口（保持 About/Guides 两链，落地页靠搜索+页脚+互链导流）。

## 顶栏导航与首屏滚动提示（v1.26）
- **顶栏全页 sticky**：topbar 移出 `.stage` 成为 `.shell` 首子元素（`position: sticky; top: 0; z-index: 60`，毛玻璃背景现成），内容区滚动时导航仍可达。
- **顶栏控件统一胶囊体系 + 排序**（左→右）：文字导航胶囊 About / Guides（`.tb-link` 复用 `.tgl`/语言框形态：34px 高、999px 圆角、1px 边框、mono 12px、hover 青色+边框提亮+光晕，文案入 i18n navAbout/navGuides）→ 状态胶囊 → 圆按钮图标组 GitHub / 主题（`.tb-icon` 34px 圆形描边，与 `.tgl` 同 hover 语言）→ 语言下拉收尾；≤640px 控件收到 30px、隐藏状态胶囊与品牌副标题为导航腾位。
- **首屏滚动提示条 `.scroll-cue`**：stage 之后、内容区之前的文档流内 40px 细条（`--cue-h`），mono 大写小字「Stories & guides」（navCue 五语言）+ chevron 上下浮动动画（reduced-motion 停）；点击锚跳 #site-content；零遮挡（不占 workspace 高度），滚动后随文档流自然离开，无需 JS 隐藏。
- **首屏高度配平**：`.stage` 高度 = `calc(100vh − var(--tb-h) − var(--cue-h))`（--tb-h 桌面 65px / ≤640px 53px），三者合计恰好一屏，提示条在首屏可见；≤1080px 媒体查询 stage `min-height` 同步扣除两者。
- **锚点留位**：`#site-content { scroll-margin-top: calc(var(--tb-h) + 14px) }`，跳转不被 sticky 顶栏遮标题。

## 启动加载占位（boot）
- React bundle 下载/执行期间 `#root` 为空、静态内容区文字先渲染，易误以为页面未加载——故在 `index.html` 的 `#root` 内放**静态启动占位**：`createRoot().render()` 挂载时自动整体替换，无需 JS 手动移除。
- 结构：居中玻璃面板 = Logo 56px + ChartThat 渐变字（26px）+ 220px 伪进度光带（0→92%，1.6s `cubic-bezier(.22,.61,.36,1)` forwards + 流光扫过，与生成等待期同语言）+ 11px 大写加载文案（五语言 `data-lang-block`，显隐规则与 about.html 同构）。
- 高度 `min-height: 100vh/100svh`：把静态内容区推到一屏下方，首屏只见加载面板；**不用 fixed 遮盖**——JS 加载失败时滚动仍可阅读内容区。
- 样式与预检测脚本（dc-theme/dc-lang 优先、浏览器前缀、en 兜底，同 theme.tsx/i18n.tsx 规则）全部内联 head——dev 模式 styles.css 由 JS 注入时序太晚，必须自包含防主题/语言闪烁；`prefers-reduced-motion` 时光带直置 92% 停动画。

## 生成动效（管线构建）
- 生成等待期：扫描光束自上而下扫过画布 + 伪进度光带缓升至 92%，进度数字用等宽字体 + 青色文字辉光。
- 候选到达后逐张「接通」：卡片按 150ms 间隔依次进场（上浮 16px + 微缩放 + 模糊褪去），顶部进度条显示「管线构建 n/N」；进度条为 3px 渐变光带 + 流光扫过。
- 卡片内部 ECharts 同步播放绘制动画：折线/柱体逐段拉出（1500ms cubicOut，数据点 70ms 渐进延迟），营造「线管逐段铺设」感；鼠标移入卡片时重播当前图表的绘制动画。
- 提供「重播动画」幽灵按钮，便于单独测试前端动效；`prefers-reduced-motion` 时全部动效关闭直接呈现。
- 动效产物导出跟随当前主题：色板随 `specToOption(spec, theme)` 切换。默认直出实底循环 `.gif`（采帧底色深色 `#0d1424` / 浅色**纯白 `#ffffff`**——贴 PPT 白底不带颜色，GIF 不支持半透明，透明底会被填黑）；提供「透明背景」勾选，输出二元透明 GIF（P 模式 + transparency、disposal=2），因抗锯齿毛边且文字随主题配色，仅适合贴到与主题同色的背景。导出区双按钮：主按钮「导出 PPTX」（原生可编辑）、幽灵按钮「导出动效 GIF」（直出 .gif）；GIF 专属选项：「显示数据标签」（位图导出后不可编辑，数值在导出期决定）、「透明背景」。

## 浅色主题（日间控制台）
同一「深空控制台」基因的日间形态：指挥中心开了天窗——冰蓝白空间里，青色沉入湖蓝以保证白底对比度；玻璃面板变为磨砂白，发光收敛为柔和投影。
- 触发：顶栏主题切换按钮（日/夜图标），`localStorage` 持久化，默认深色；实现为 `:root`（深色）+ `[data-theme='light']` 全套 CSS 变量覆盖。
- 底色：冰蓝白 `#f2f6fb`（不用纯白，保留蓝调基因）；面板：磨砂白 `rgba(255,255,255,.78)`。
- 主色下沉：青 `#22d3ee` → `#0891b2`，蓝 `#3b82f6` → `#2563eb`；渐变同族加深（`#06b6d4 → #3b82f6`），主按钮文字改纯白。
- 文字：墨 `#0f1c2e` / 次 `#5b6b82`；边框 `rgba(8,145,178,.16)`。
- 发光收敛：外发光强度减半以上，卡片悬浮改用柔和投影 `0 10px 28px rgba(15,28,46,.12)`；数字辉光取消。
- ECharts 同步换浅色色板（同色相降明度：`#0891b2/#2563eb/#059669/#d97706/#e11d48/#7c3aed`），坐标轴/文字转墨色，tooltip 白底。

## 多语言（i18n）
- 六语言界面：中文 / English / Français / Deutsch / Español（SPEC v1.17 出海多语言）；顶栏语言下拉（母语名标签，复用 `.tgl` 胶囊 + 自绘小三角），`localStorage` 持久化。
- 初始语言：**检测浏览器语言**（`navigator.language` 前缀匹配 zh/fr/de/es，其余一律英文兜底——面向海外默认英文而非中文）；用户手动选择优先于检测结果。
- 范围：仅界面框架文案（按钮/标题/状态/提示/图型与语义层标签/示例数据表头）；列名、维度值等用户数据内容始终保持原文不翻译。
- 推荐产出（v1.18）：图表标题/reasoning 按界面语言**五语言原生**——LLM 路径 fr/de/es 经 prompt 语言指令产出目标语言；降级模板/缺失提示同样五语言。语言与内容语言一致，不混搭。
- 文案集中于 `frontend/src/i18n.tsx` 字典（六语言全量），组件一律经 `useI18n()` 取词，禁止散落硬编码。

## 设计禁忌
- 不大面积铺高饱和紫蓝「AI 渐变」背景（旧版禁忌保留精神：发光克制，只做点缀）。
- 深色主题不使用纯黑 #000 底；浅色主题不使用纯白 #fff 底（保蓝调呼吸感）。
- 发光效果不叠加超过两层，避免"光污染"；浅色主题以投影替代光晕。
