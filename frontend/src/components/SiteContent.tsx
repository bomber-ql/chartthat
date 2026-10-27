/**
 * 主页底部内容区（v1.21 SEO/AdSense，v1.22 多语言化）。
 *
 * 双轨制：index.html 的 #site-content 内嵌静态英文版（爬虫零渲染可见），
 * 浏览器端由 main.tsx 清空后经 App 内 createPortal 挂载本组件，
 * 按界面语言渲染五语言版本。图型名称复用 i18n 的 chartLabel。
 */
import type { ReactNode } from 'react';
import { useI18n } from '../i18n';
import type { Lang } from '../i18n';
import type { ChartType } from '../types';
import ChartMini from './ChartMini';

const GUIDE_ORDER: ChartType[] = [
  'bar', 'hbar', 'line', 'area', 'combo', 'stacked', 'slope',
  'scatter', 'waterfall', 'radar', 'pie', 'donut', 'sunburst',
];

// 人群场景卡插画（AI 生成，扁平商务风，与故事区同色系），顺序对应 SITE_COPY.cases
const CASE_ART = ['/case-consultant.jpg', '/case-marketer.jpg', '/case-operator.jpg', '/case-analyst.jpg'];

interface GuideItem {
  use: string;
  needs: string;
  eg: string;
}

interface FaqItem {
  q: string;
  a: string;
  linkText?: string;
  linkHref?: string;
}

interface SiteCopy {
  storyTitle: string;
  story: string[];
  storyMore: string;
  storyArtAlt: string;
  howTitle: string;
  howSteps: { title: string; desc: string }[];
  perks: { title: string; items: string[] };
  guideTitle: string;
  needsLabel: string;
  guide: GuideItem[];
  casesTitle: string;
  cases: { title: string; desc: string }[];
  fnTitle: string;
  fnIntro: string;
  fnCta: string;
  fnNotes: { num: string; title: string; desc: string; href: string }[];
  faqTitle: string;
  faq: FaqItem[];
}

const SITE_COPY: Record<Lang, SiteCopy> = {
  en: {
    storyTitle: 'Built by someone who makes slides for a living',
    story: [
      "I work in advertising. Most of my Fridays end the same way: a spreadsheet full of numbers, a client pitch on Monday, and a deck full of charts that don't exist yet.",
      'I tried everything. AI chatbots wanted a prompt and returned a **picture** of a chart — flat, uneditable, useless the moment a number changed. Plugins wanted installs and accounts. BI tools wanted a data warehouse. What I actually needed was embarrassingly simple: **a table in, a PowerPoint chart out.**',
      'So I built it. Paste your data, get thirteen kinds of genuinely editable charts, exported as native PowerPoint objects or animated GIFs. No sign-up, no chat window, nothing to install — and your numbers are **never stored, never fed into someone else\u2019s conversation.**',
    ],
    storyMore: 'Read the full story →',
    storyArtAlt: 'Late at night, a marketer buried in presentation slides and printed charts',
    howTitle: 'Three steps. Thirty seconds.',
    howSteps: [
      { title: 'Paste your data', desc: 'Plain text, a CSV file, or an Excel sheet — headers on top, numbers below. That\u2019s all the formatting it needs.' },
      { title: 'Pick a chart', desc: 'ChartThat reads your table\u2019s semantics and recommends the types that genuinely fit — trend, comparison, or rate — with a one-line reason for each.' },
      { title: 'Export to your deck', desc: 'Download a native, editable PowerPoint chart or a looping animated GIF. No watermark, no sign-up, no detours.' },
    ],
    perks: {
      title: 'Why it sticks',
      items: [
        'Paste to chart in about ten seconds',
        'Thirteen chart types, matched to your data',
        'Native PPTX — double-click to edit, right in your deck',
        'No sign-up, nothing to install, nothing stored',
        'Free. No watermark, no trial clock',
      ],
    },
    guideTitle: 'Thirteen chart types, and when to use each',
    needsLabel: 'Needs',
    guide: [
      { use: 'Compare values across categories — the default answer to "which is biggest?"', needs: '1 category column + 1–3 numeric columns', eg: 'e.g. quarterly revenue by product line' },
      { use: 'Same comparison, rotated. Better when category names get long.', needs: '1 category column + 1–3 numeric columns', eg: 'e.g. brand awareness by campaign name' },
      { use: 'Show a trend over time — the workhorse for anything with a date axis.', needs: '1 time column + 1–4 numeric columns', eg: 'e.g. monthly active users over a year' },
      { use: 'A trend with a sense of volume — good for cumulative or total trends.', needs: '1 time column + 1–3 numeric columns', eg: 'e.g. cumulative sign-ups by month' },
      { use: 'Two units, one chart: bars for volume, a line for the rate that explains it.', needs: '1 category/time column + numeric columns + 1 % column', eg: 'e.g. revenue bars with a growth-rate line' },
      { use: 'Part-to-whole across categories — totals and their composition at once.', needs: '1 category column + 2+ numeric columns (same unit)', eg: 'e.g. sales by channel, stacked per quarter' },
      { use: 'Before vs after for many items — slopes make winners and losers obvious.', needs: '1 item column + exactly 2 period columns', eg: 'e.g. this year vs last year, per product' },
      { use: 'Relationship between two metrics — correlation, clusters, outliers.', needs: '2 numeric columns (+ optional label)', eg: 'e.g. ad spend vs conversions per campaign' },
      { use: 'How a total is built up or worn down, step by step.', needs: '1 stage column + 1 numeric column (deltas)', eg: 'e.g. budget from plan to actual, item by item' },
      { use: 'A profile across 3+ metrics — compare entities at a glance.', needs: '3+ numeric columns (same unit) + 1 label column', eg: 'e.g. two products scored on five attributes' },
      { use: 'Share of total for a few categories — best kept to 2–5 slices.', needs: '1 category column + 1 numeric column', eg: 'e.g. market share of the top four brands' },
      { use: 'A pie with breathing room — same job, lighter look.', needs: '1 category column + 1 numeric column', eg: 'e.g. traffic share by source' },
      { use: 'Hierarchical share — a whole and its parts, ring by ring.', needs: '2 category columns + 1 numeric column', eg: 'e.g. sales by region, then by country' },
    ],
    casesTitle: 'Made for people who live in decks',
    cases: [
      { title: 'Consultants', desc: 'Turn the client\u2019s spreadsheet into exhibit-ready charts before the Monday steering committee.' },
      { title: 'Marketing & advertising', desc: 'Campaign results, budget breakdowns, media mix — from report table to client slide in one paste.' },
      { title: 'Operations & product', desc: 'Weekly metrics, funnels, and before/after comparisons that keep up with the numbers.' },
      { title: 'Analysts & students', desc: 'See thirteen ways to show the same table, then take the editable file into your report.' },
    ],
    faqTitle: 'Frequently asked questions',
    faq: [
      { q: 'Is ChartThat really free?', a: 'Yes — completely. No account, no watermark, no trial period, no hidden limits. It runs on a small server that costs less than a coffee per month, and that\u2019s fine.' },
      { q: 'Is my data safe here?', a: 'Your table is processed in memory, only to build your charts. We **never store** your data, chart titles, or column names — our own statistics count feature usage only, with no IP addresses and no user content.', linkText: 'Read our privacy policy', linkHref: '/privacy.html' },
      { q: 'What input formats are supported?', a: 'Paste plain text or a markdown table, or upload a **.csv** or **.xlsx** file. Put headers in the first row and numbers below — ChartThat detects types, units, percentages, and missing values on its own.' },
      { q: 'Are the exported PowerPoint charts really editable?', a: 'Yes. The .pptx file contains a **native PowerPoint chart object**, not an image. Double-click it in PowerPoint, WPS, or Keynote to edit the data and restyle it with your own theme.' },
      { q: 'Which chart types can it generate?', a: 'Thirteen: bar, horizontal bar, line, area, combo (bar + line on dual axes), stacked, slope, scatter, waterfall, radar, pie, donut, and sunburst. The guide above shows when to use each.' },
      { q: 'Can I export animated charts?', a: 'Yes — any chart can be downloaded as a **looping animated GIF**, with optional data labels and a solid or transparent background. GIFs play in every slide tool without plugins.' },
      { q: 'Which languages does the interface support?', a: '中文, English, Français, Deutsch, and Español. The interface follows your browser language automatically, and chart titles are written in the language you use.' },
      { q: 'Does it work with WPS and older PowerPoint versions?', a: 'Any tool that opens .pptx works — Microsoft PowerPoint 2013+, WPS Office, Keynote, Google Slides. Charts stay editable everywhere, including WPS, with no broken-link prompts.' },
      { q: 'Can I use the exported files commercially?', a: 'Absolutely. Your data is yours and your charts are yours — client work, reports, publications, no attribution required.' },
    ],
    fnTitle: 'Field notes: Charts That Sell',
    fnIntro:
      'No chart-beauty contests. Notes on making data close deals, written between pitches — in English, because that\u2019s where the pitches happen.',
    fnCta: 'All field notes →',
    fnNotes: [
      {
        num: 'Field note #1',
        title: 'Choose the chart by the conclusion you\u2019re selling',
        desc: 'Urgency wants a line. A gap wants bars. Reallocation wants blocks. Attribution wants a waterfall.',
        href: '/guides/choose-chart-by-conclusion.html',
      },
      {
        num: 'Field note #2',
        title: 'One slide, one claim: the 3-second rule',
        desc: 'The client gives each page three seconds. Three claims on one page is no claim at all.',
        href: '/guides/one-slide-one-claim.html',
      },
    ],
  },
  zh: {
    storyTitle: '一个天天做 PPT 的人做的工具',
    story: [
      '我是做广告营销的，PPT 是吃饭家伙。几乎每个周五，结局都一样：手里一张塞满数字的表，周一要给客户提案，而 PPT 里的图表一张都还没影。',
      '能试的工具我都试了。AI 聊天机器人要先写 prompt，最后给我一张图——一张**图片**，客户改个数字就得全部重做；插件要装、账号要注册；BI 工具恨不得先建个数据仓库。可我的需求真没那么复杂：**表格进去，PPT 图表出来。**',
      '没人做，那就自己做一个。粘贴数据，生成十三种真正可编辑的图表，导出原生 PowerPoint 图表或动效 GIF。不用注册、不用对话、不用安装——你的数据**不存储，也不发给任何人。**',
    ],
    storyMore: '阅读完整故事 →',
    storyArtAlt: '深夜里被 PPT 和图表稿包围的营销人',
    howTitle: '三步，三十秒。',
    howSteps: [
      { title: '粘贴数据', desc: '纯文本、CSV 或 Excel 文件——首行表头、下面数字，格式要求就这么多。' },
      { title: '挑选图表', desc: 'ChartThat 读懂表格语义，推荐真正合适的图型——趋势、对比或比率——每个都附一句推荐理由。' },
      { title: '导出进 PPT', desc: '下载原生可编辑的 PowerPoint 图表，或循环播放的动效 GIF。无水印、不注册、不绕路。' },
    ],
    perks: {
      title: '为什么值得常驻',
      items: [
        '粘贴到出图，十秒左右',
        '十三种图型，按数据语义匹配',
        '原生 PPTX——幻灯片里双击就能改数换色',
        '免注册、免安装、数据不留存',
        '免费，无水印，没有试用期',
      ],
    },
    guideTitle: '十三种图表，以及各自的最佳场景',
    needsLabel: '数据要求',
    guide: [
      { use: '跨分类比较数值——「谁最大」的默认答案', needs: '1 个分类列 + 1–3 个数值列', eg: '例如：各产品线季度营收' },
      { use: '同样的比较横过来——分类名较长时更好看', needs: '1 个分类列 + 1–3 个数值列', eg: '例如：各 campaign 的品牌认知度' },
      { use: '随时间展示趋势——带日期轴数据的万能手', needs: '1 个时间列 + 1–4 个数值列', eg: '例如：全年月活走势' },
      { use: '带体量感的趋势——适合累计或总量变化', needs: '1 个时间列 + 1–3 个数值列', eg: '例如：逐月累计注册量' },
      { use: '两种单位同图：柱看体量，折线看背后的比率', needs: '1 个分类/时间列 + 数值列 + 1 个百分比列', eg: '例如：营收柱 + 增长率折线' },
      { use: '跨分类的部分与整体——总量和构成一次看清', needs: '1 个分类列 + 2 个以上同单位数值列', eg: '例如：各季度分渠道销量堆叠' },
      { use: '多个对象的前后对比——斜率让涨跌一目了然', needs: '1 个对象列 + 恰好 2 个时期列', eg: '例如：各产品今年 vs 去年' },
      { use: '两个指标的关系——相关性、聚类、异常点', needs: '2 个数值列（可带标签列）', eg: '例如：各 campaign 花费 vs 转化' },
      { use: '总量如何被一步步累加或消耗', needs: '1 个阶段列 + 1 个数值列（逐步增减）', eg: '例如：预算从计划到实际逐项拆解' },
      { use: '3 个以上指标的画像——多个对象一眼对比', needs: '3 个以上同单位数值列 + 1 个标签列', eg: '例如：两款产品五个维度评分' },
      { use: '少数分类的占比——控制在 2–5 个扇区', needs: '1 个分类列 + 1 个数值列', eg: '例如：前四品牌市场份额' },
      { use: '更透气的饼图——同样的占比，更轻的观感', needs: '1 个分类列 + 1 个数值列', eg: '例如：各渠道流量占比' },
      { use: '层级占比——整体到局部一环环展开', needs: '2 个分类列 + 1 个数值列', eg: '例如：销售按大区再到国家' },
    ],
    casesTitle: '为活在 PPT 里的人而做',
    cases: [
      { title: '咨询顾问', desc: '周一指导委员会之前，把客户的表格变成拿得出手的图表页。' },
      { title: '营销与广告', desc: '投放复盘、预算拆解、媒介组合——从数据报表到客户提案，一次粘贴搞定。' },
      { title: '运营与产品', desc: '周会指标、漏斗、前后对比，数字变多快，图表跟多快。' },
      { title: '分析师与学生', desc: '同一张表的十三种画法都试一遍，再带着可编辑文件写进报告。' },
    ],
    faqTitle: '常见问题',
    faq: [
      { q: 'ChartThat 真的免费吗？', a: '完全免费。不用注册、没有水印、没有试用期、没有隐藏限制。它跑在一台每月不到一杯咖啡钱的小服务器上，这样就够了。' },
      { q: '我的数据安全吗？', a: '你的表格只在内存中处理、仅用于生成图表。我们**绝不存储**你的数据、图表标题或列名——使用统计只记录功能次数，不含 IP、不含内容。', linkText: '查看隐私政策', linkHref: '/privacy.html' },
      { q: '支持哪些输入格式？', a: '直接粘贴纯文本或 markdown 表格，或上传 **.csv** / **.xlsx** 文件。首行放表头、下面放数字即可——类型、单位、百分比、缺失值都会自动识别。' },
      { q: '导出的 PPT 图表真的可以编辑吗？', a: '真的。.pptx 里是**原生 PowerPoint 图表对象**，不是图片。在 PowerPoint、WPS 或 Keynote 里双击即可改数据、换样式。' },
      { q: '能生成哪些图表？', a: '十三种：柱状、条形、折线、面积、组合（柱+折线双轴）、堆叠、斜率、散点、瀑布、雷达、饼图、圆环、旭日。上方速查表写了每种的适用场景。' },
      { q: '可以导出动效图表吗？', a: '可以——任何图表都能下载为**循环播放的动效 GIF**，可选数据标签和实底/透明背景，在任何幻灯片工具里都能直接播放。' },
      { q: '界面支持哪些语言？', a: '中文、English、Français、Deutsch、Español。界面自动跟随浏览器语言，图表标题也会用你正在使用的语言生成。' },
      { q: '兼容 WPS 和老版本 PowerPoint 吗？', a: '只要能打开 .pptx 就行——PowerPoint 2013+、WPS Office、Keynote、Google Slides。图表在各处都保持可编辑，WPS 里也不会弹「链接文件不可用」。' },
      { q: '导出的文件可以商用吗？', a: '当然。数据是你的，图表也是你的——客户交付、报告、出版物随便用，无需署名。' },
    ],
    fnTitle: '提案手记：Charts That Sell',
    fnIntro: '不聊图表美学。一个以提案为生的人，写数据如何促成成交——手记以英文撰写，因为提案现场在那里。',
    fnCta: '全部手记 →',
    fnNotes: [
      {
        num: '手记 #1',
        title: 'Choose the chart by the conclusion you\u2019re selling',
        desc: '紧迫感用折线，差距用条形，挪预算用构成，归因用瀑布——按你要卖的结论选图。',
        href: '/guides/choose-chart-by-conclusion.html',
      },
      {
        num: '手记 #2',
        title: 'One slide, one claim: the 3-second rule',
        desc: '客户只给每页三秒钟。一页三个主张，等于没有主张。',
        href: '/guides/one-slide-one-claim.html',
      },
    ],
  },
  fr: {
    storyTitle: 'Conçu par quelqu\u2019un qui vit dans ses slides',
    story: [
      'Je travaille dans la publicité. La plupart de mes vendredis se terminent de la même façon : un tableur plein de chiffres, un pitch client lundi, et une présentation remplie de graphiques qui n\u2019existent pas encore.',
      'J\u2019ai tout essayé. Les chatbots IA voulaient un prompt et renvoyaient une **image** de graphique — plate, inmodifiable, inutile dès qu\u2019un chiffre changeait. Les plugins exigeaient installation et compte. Les outils BI voulaient un entrepôt de données. Mon besoin était pourtant d\u2019une simplicité embarrassante : **un tableau entre, un graphique PowerPoint sort.**',
      'Alors je l\u2019ai construit. Collez vos données, obtenez treize types de graphiques vraiment modifiables, exportés en objets PowerPoint natifs ou en GIF animés. Sans inscription, sans fenêtre de chat, sans rien installer — et vos chiffres ne sont **jamais stockés, jamais envoyés dans la conversation de quelqu\u2019un d\u2019autre.**',
    ],
    storyMore: 'Lire toute l\u2019histoire →',
    storyArtAlt: 'Tard le soir, un marketeur submergé par ses slides et ses graphiques imprimés',
    howTitle: 'Trois étapes. Trente secondes.',
    howSteps: [
      { title: 'Collez vos données', desc: 'Texte brut, CSV ou fichier Excel — en-têtes en haut, chiffres en dessous. C\u2019est tout le formatage requis.' },
      { title: 'Choisissez un graphique', desc: 'ChartThat lit la sémantique de votre tableau et recommande les types vraiment adaptés — tendance, comparaison ou taux — avec une raison en une ligne pour chacun.' },
      { title: 'Exportez vers vos slides', desc: 'Téléchargez un graphique PowerPoint natif et modifiable, ou un GIF animé en boucle. Sans filigrane, sans inscription, sans détour.' },
    ],
    perks: {
      title: 'Pourquoi on y revient',
      items: [
        'Du collage au graphique en dix secondes',
        'Treize types de graphiques, adaptés à vos données',
        'PPTX natif — double-clic pour modifier, directement dans vos slides',
        'Aucun compte, rien à installer, rien de stocké',
        'Gratuit. Sans filigrane ni compte à rebours d’essai',
      ],
    },
    guideTitle: 'Treize types de graphiques, et quand les utiliser',
    needsLabel: 'Requiert',
    guide: [
      { use: 'Comparer des valeurs entre catégories — la réponse par défaut à « lequel est le plus gros ? »', needs: '1 colonne de catégories + 1–3 colonnes numériques', eg: 'p. ex. revenus trimestriels par gamme' },
      { use: 'La même comparaison, en horizontal — mieux quand les noms sont longs.', needs: '1 colonne de catégories + 1–3 colonnes numériques', eg: 'p. ex. notoriété par nom de campagne' },
      { use: 'Montrer une tendance dans le temps — l\u2019outil de base de toute donnée datée.', needs: '1 colonne temporelle + 1–4 colonnes numériques', eg: 'p. ex. utilisateurs actifs mensuels sur un an' },
      { use: 'Une tendance avec du volume — idéale pour les cumuls et les totaux.', needs: '1 colonne temporelle + 1–3 colonnes numériques', eg: 'p. ex. inscriptions cumulées par mois' },
      { use: 'Deux unités, un graphique : des barres pour le volume, une ligne pour le taux.', needs: '1 colonne catégorie/temps + colonnes numériques + 1 colonne %', eg: 'p. ex. barres de revenus + ligne de croissance' },
      { use: 'La partie et le tout à la fois — totaux et composition en un coup d\u2019œil.', needs: '1 colonne de catégories + 2+ colonnes numériques (même unité)', eg: 'p. ex. ventes par canal empilées par trimestre' },
      { use: 'Avant/après pour de nombreux éléments — la pente révèle gagnants et perdants.', needs: '1 colonne d\u2019éléments + exactement 2 colonnes de périodes', eg: 'p. ex. cette année vs l\u2019an dernier, par produit' },
      { use: 'Relation entre deux métriques — corrélation, clusters, valeurs atypiques.', needs: '2 colonnes numériques (+ étiquette optionnelle)', eg: 'p. ex. dépenses pubs vs conversions par campagne' },
      { use: 'Comment un total se construit ou s\u2019érode, étape par étape.', needs: '1 colonne d\u2019étapes + 1 colonne numérique (variations)', eg: 'p. ex. budget du prévu au réel, poste par poste' },
      { use: 'Un profil sur 3+ métriques — comparer des entités d\u2019un coup d\u2019œil.', needs: '3+ colonnes numériques (même unité) + 1 colonne d\u2019étiquettes', eg: 'p. ex. deux produits notés sur cinq attributs' },
      { use: 'Part du total pour quelques catégories — 2 à 5 parts maximum.', needs: '1 colonne de catégories + 1 colonne numérique', eg: 'p. ex. part de marché des quatre premières marques' },
      { use: 'Un camembert aéré — même mission, rendu plus léger.', needs: '1 colonne de catégories + 1 colonne numérique', eg: 'p. ex. part du trafic par source' },
      { use: 'Part hiérarchique — du tout aux parties, anneau par anneau.', needs: '2 colonnes de catégories + 1 colonne numérique', eg: 'p. ex. ventes par région puis par pays' },
    ],
    casesTitle: 'Pour ceux qui vivent dans leurs slides',
    cases: [
      { title: 'Consultants', desc: 'Transformez le tableur du client en graphiques prêts pour le comité du lundi.' },
      { title: 'Marketing & publicité', desc: 'Résultats de campagne, budgets, mix média — du tableau au slide client en un seul collage.' },
      { title: 'Opérations & produit', desc: 'Métriques hebdo, funnels, comparaisons avant/après — à la vitesse des chiffres.' },
      { title: 'Analystes & étudiants', desc: 'Essayez treize façons de montrer le même tableau, puis emportez le fichier modifiable dans votre rapport.' },
    ],
    faqTitle: 'Questions fréquentes',
    faq: [
      { q: 'ChartThat est-il vraiment gratuit ?', a: 'Oui, totalement. Pas de compte, pas de filigrane, pas de période d\u2019essai, pas de limite cachée. Il tourne sur un petit serveur qui coûte moins qu\u2019un café par mois, et cela suffit.' },
      { q: 'Mes données sont-elles en sécurité ?', a: 'Votre tableau est traité en mémoire, uniquement pour construire vos graphiques. Nous ne **stockons jamais** vos données, titres ou noms de colonnes — nos statistiques comptent seulement les usages, sans IP ni contenu.', linkText: 'Lire notre politique de confidentialité', linkHref: '/privacy.html' },
      { q: 'Quels formats d\u2019entrée sont acceptés ?', a: 'Collez du texte brut ou un tableau markdown, ou envoyez un fichier **.csv** ou **.xlsx**. En-têtes en première ligne, chiffres en dessous — types, unités, pourcentages et valeurs manquantes sont détectés automatiquement.' },
      { q: 'Les graphiques PowerPoint exportés sont-ils vraiment modifiables ?', a: 'Oui. Le fichier .pptx contient un **objet graphique PowerPoint natif**, pas une image. Double-cliquez dans PowerPoint, WPS ou Keynote pour modifier les données et le style.' },
      { q: 'Quels types de graphiques sont disponibles ?', a: 'Treize : barres, barres horizontales, ligne, aires, combo (barres + ligne en double axe), empilé, pente, nuage de points, cascade, radar, camembert, anneau et sunburst. Le guide ci-dessus indique quand utiliser chacun.' },
      { q: 'Puis-je exporter des graphiques animés ?', a: 'Oui — chaque graphique peut être téléchargé en **GIF animé en boucle**, avec étiquettes optionnelles et fond plein ou transparent. Lisible partout sans plugin.' },
      { q: 'Quelles langues l\u2019interface prend-elle en charge ?', a: '中文, English, Français, Deutsch et Español. L\u2019interface suit automatiquement la langue de votre navigateur, et les titres de graphiques sont rédigés dans votre langue.' },
      { q: 'Compatible avec WPS et les anciens PowerPoint ?', a: 'Tout outil ouvrant le .pptx convient — PowerPoint 2013+, WPS Office, Keynote, Google Slides. Les graphiques restent modifiables partout, y compris WPS, sans message de lien rompu.' },
      { q: 'Puis-je utiliser les fichiers à des fins commerciales ?', a: 'Bien sûr. Vos données sont à vous, vos graphiques aussi — livrables clients, rapports, publications, sans attribution requise.' },
    ],
    fnTitle: 'Notes de terrain : Charts That Sell',
    fnIntro:
      'Pas de concours de beauté pour graphiques. Des notes pour faire signer avec des données, écrites entre deux pitches — en anglais, parce que c\u2019est là que les pitches ont lieu.',
    fnCta: 'Toutes les notes →',
    fnNotes: [
      {
        num: 'Note #1',
        title: 'Choose the chart by the conclusion you\u2019re selling',
        desc: 'L\u2019urgence veut une ligne. L\u2019écart veut des barres. La réallocation veut des blocs. L\u2019attribution veut une cascade.',
        href: '/guides/choose-chart-by-conclusion.html',
      },
      {
        num: 'Note #2',
        title: 'One slide, one claim: the 3-second rule',
        desc: 'Le client accorde trois secondes par page. Trois messages sur une page, c\u2019est aucun message.',
        href: '/guides/one-slide-one-claim.html',
      },
    ],
  },
  de: {
    storyTitle: 'Gebaut von jemandem, der beruflich Slides baut',
    story: [
      'Ich arbeite in der Werbung. Die meisten meiner Freitage enden gleich: eine Tabelle voller Zahlen, ein Kundenpitch am Montag — und ein Deck voller Diagramme, die noch nicht existieren.',
      'Ich habe alles ausprobiert. KI-Chatbots wollten einen Prompt und lieferten ein **Bild** eines Diagramms — flach, uneditierbar, nutzlos, sobald sich eine Zahl änderte. Plugins verlangten Installation und Konto. BI-Tools ein Data Warehouse. Dabei war mein Bedarf fast peinlich einfach: **Tabelle rein, PowerPoint-Diagramm raus.**',
      'Also habe ich es selbst gebaut. Daten einfügen, dreizehn wirklich editierbare Diagrammtypen bekommen, exportiert als native PowerPoint-Objekte oder animierte GIFs. Ohne Anmeldung, ohne Chatfenster, ohne Installation — und Ihre Zahlen werden **nie gespeichert und nie in fremde Konversationen gefüttert.**',
    ],
    storyMore: 'Die ganze Geschichte lesen →',
    storyArtAlt: 'Spät in der Nacht: ein Marketingmensch, begraben unter Folien und ausgedruckten Diagrammen',
    howTitle: 'Drei Schritte. Dreißig Sekunden.',
    howSteps: [
      { title: 'Daten einfügen', desc: 'Reiner Text, CSV oder Excel — Kopfzeile oben, Zahlen darunter. Mehr Formatierung braucht es nicht.' },
      { title: 'Diagramm wählen', desc: 'ChartThat liest die Semantik Ihrer Tabelle und empfiehlt die wirklich passenden Typen — Trend, Vergleich oder Rate — jeweils mit einer einzeiligen Begründung.' },
      { title: 'Ins Deck exportieren', desc: 'Laden Sie ein natives, editierbares PowerPoint-Diagramm oder ein animiertes GIF in Schleife herunter. Ohne Wasserzeichen, ohne Anmeldung, ohne Umwege.' },
    ],
    perks: {
      title: 'Warum es hängen bleibt',
      items: [
        'Vom Einfügen zum Diagramm in etwa zehn Sekunden',
        'Dreizehn Diagrammtypen, passend zu Ihren Daten',
        'Natives PPTX — per Doppelklick direkt im Deck bearbeiten',
        'Keine Anmeldung, nichts zu installieren, nichts gespeichert',
        'Kostenlos. Ohne Wasserzeichen, ohne Testphase',
      ],
    },
    guideTitle: 'Dreizehn Diagrammtypen — und wann man sie einsetzt',
    needsLabel: 'Benötigt',
    guide: [
      { use: 'Werte über Kategorien vergleichen — die Standardantwort auf „was ist am größten?“', needs: '1 Kategoriespalte + 1–3 Zahlenspalten', eg: 'z. B. Quartalsumsatz pro Produktlinie' },
      { use: 'Derselbe Vergleich, gedreht — besser bei langen Kategorienamen.', needs: '1 Kategoriespalte + 1–3 Zahlenspalten', eg: 'z. B. Markenbekanntheit pro Kampagnenname' },
      { use: 'Einen Trend über Zeit zeigen — das Arbeitstier für alles mit Datumsachse.', needs: '1 Zeitspalte + 1–4 Zahlenspalten', eg: 'z. B. monatlich aktive Nutzer über ein Jahr' },
      { use: 'Ein Trend mit Volumen — gut für kumulative oder Gesamtverläufe.', needs: '1 Zeitspalte + 1–3 Zahlenspalten', eg: 'z. B. kumulierte Registrierungen pro Monat' },
      { use: 'Zwei Einheiten, ein Diagramm: Säulen fürs Volumen, Linie für die Rate.', needs: '1 Kategorie-/Zeitspalte + Zahlenspalten + 1 %-Spalte', eg: 'z. B. Umsatzsäulen + Wachstumslinie' },
      { use: 'Teil und Ganzes zugleich — Summen und Zusammensetzung auf einen Blick.', needs: '1 Kategoriespalte + 2+ Zahlenspalten (gleiche Einheit)', eg: 'z. B. Absatz pro Kanal, gestapelt je Quartal' },
      { use: 'Vorher vs. nachher für viele Elemente — Steigungen zeigen Gewinner und Verlierer.', needs: '1 Elementspalte + genau 2 Periodenspalten', eg: 'z. B. dieses Jahr vs. letztes Jahr, pro Produkt' },
      { use: 'Beziehung zweier Metriken — Korrelation, Cluster, Ausreißer.', needs: '2 Zahlenspalten (+ optionale Beschriftung)', eg: 'z. B. Werbeausgaben vs. Conversions pro Kampagne' },
      { use: 'Wie eine Summe Schritt für Schritt entsteht oder schwindet.', needs: '1 Stufenspalte + 1 Zahlenspalte (Deltas)', eg: 'z. B. Budget von Plan zu Ist, Posten für Posten' },
      { use: 'Ein Profil über 3+ Metriken — Einheiten auf einen Blick vergleichen.', needs: '3+ Zahlenspalten (gleiche Einheit) + 1 Beschriftungsspalte', eg: 'z. B. zwei Produkte auf fünf Attributen bewertet' },
      { use: 'Anteil am Ganzen für wenige Kategorien — am besten 2–5 Segmente.', needs: '1 Kategoriespalte + 1 Zahlenspalte', eg: 'z. B. Marktanteil der vier Top-Marken' },
      { use: 'Ein Kreisdiagramm mit Luft — gleiche Aufgabe, leichteres Erscheinungsbild.', needs: '1 Kategoriespalte + 1 Zahlenspalte', eg: 'z. B. Traffic-Anteil nach Quelle' },
      { use: 'Hierarchischer Anteil — vom Ganzen zu den Teilen, Ring für Ring.', needs: '2 Kategoriespalten + 1 Zahlenspalte', eg: 'z. B. Umsatz nach Region, dann Land' },
    ],
    casesTitle: 'Für Menschen, die in Decks leben',
    cases: [
      { title: 'Berater', desc: 'Verwandeln Sie die Kundentabelle in präsentationsreife Diagramme — noch vor dem Montags-Steering.' },
      { title: 'Marketing & Werbung', desc: 'Kampagnenergebnisse, Budgets, Media-Mix — von der Report-Tabelle zur Kunden-Slide in einem Schritt.' },
      { title: 'Operations & Produkt', desc: 'Wochenmetriken, Funnels, Vorher-Nachher-Vergleiche — so schnell wie die Zahlen.' },
      { title: 'Analysten & Studierende', desc: 'Dreizehn Wege, dieselbe Tabelle zu zeigen — dann die editierbare Datei in den Bericht übernehmen.' },
    ],
    faqTitle: 'Häufige Fragen',
    faq: [
      { q: 'Ist ChartThat wirklich kostenlos?', a: 'Ja — vollständig. Kein Konto, kein Wasserzeichen, keine Testphase, keine versteckten Limits. Es läuft auf einem kleinen Server, der weniger kostet als ein Kaffee im Monat, und das reicht.' },
      { q: 'Sind meine Daten hier sicher?', a: 'Ihre Tabelle wird nur im Speicher verarbeitet, ausschließlich zum Erstellen Ihrer Diagramme. Wir **speichern niemals** Daten, Titel oder Spaltennamen — unsere Statistik zählt nur Funktionsnutzung, ohne IPs, ohne Inhalte.', linkText: 'Datenschutzerklärung lesen', linkHref: '/privacy.html' },
      { q: 'Welche Eingabeformate werden unterstützt?', a: 'Fügen Sie reinen Text oder eine Markdown-Tabelle ein, oder laden Sie eine **.csv**- oder **.xlsx**-Datei hoch. Kopfzeile zuerst, Zahlen darunter — Typen, Einheiten, Prozente und fehlende Werte werden automatisch erkannt.' },
      { q: 'Sind die exportierten PowerPoint-Diagramme wirklich editierbar?', a: 'Ja. Die .pptx enthält ein **natives PowerPoint-Diagrammobjekt**, kein Bild. Doppelklick in PowerPoint, WPS oder Keynote genügt, um Daten und Stil zu ändern.' },
      { q: 'Welche Diagrammtypen gibt es?', a: 'Dreizehn: Säulen, Balken, Linie, Fläche, Combo (Säulen + Linie auf zwei Achsen), gestapelt, Slope, Streuung, Wasserfall, Radar, Kreis, Donut und Sunburst. Der Guide oben zeigt, wann welcher passt.' },
      { q: 'Kann ich animierte Diagramme exportieren?', a: 'Ja — jedes Diagramm lässt sich als **animiertes GIF in Endlosschleife** herunterladen, mit optionalen Datenlabels und Vollton- oder Transparenthintergrund.' },
      { q: 'Welche Sprachen unterstützt die Oberfläche?', a: '中文, English, Français, Deutsch und Español. Sie folgt automatisch der Browsersprache, und Diagrammtitel werden in Ihrer Sprache geschrieben.' },
      { q: 'Funktioniert es mit WPS und älteren PowerPoint-Versionen?', a: 'Alles, was .pptx öffnet — PowerPoint 2013+, WPS Office, Keynote, Google Slides. Diagramme bleiben überall editierbar, auch in WPS, ohne Fehlermeldungen zu Verknüpfungen.' },
      { q: 'Darf ich die Dateien kommerziell nutzen?', a: 'Selbstverständlich. Ihre Daten gehören Ihnen, Ihre Diagramme auch — Kundenarbeit, Berichte, Publikationen, ohne Namensnennung.' },
    ],
    fnTitle: 'Praxis-Notizen: Charts That Sell',
    fnIntro:
      'Keine Diagramm-Schönheitswettbewerbe. Notizen darüber, wie Daten Abschlüsse machen — zwischen Pitches geschrieben, auf Englisch, weil dort die Pitches passieren.',
    fnCta: 'Alle Notizen →',
    fnNotes: [
      {
        num: 'Notiz #1',
        title: 'Choose the chart by the conclusion you\u2019re selling',
        desc: 'Dringlichkeit will eine Linie. Eine Lücke will Balken. Umverteilung will Blöcke. Attribution will einen Wasserfall.',
        href: '/guides/choose-chart-by-conclusion.html',
      },
      {
        num: 'Notiz #2',
        title: 'One slide, one claim: the 3-second rule',
        desc: 'Der Kunde gibt jeder Seite drei Sekunden. Drei Botschaften auf einer Seite sind keine Botschaft.',
        href: '/guides/one-slide-one-claim.html',
      },
    ],
  },
  es: {
    storyTitle: 'Creado por alguien que vive haciendo presentaciones',
    story: [
      'Trabajo en publicidad. La mayoría de mis viernes terminan igual: una hoja de cálculo llena de números, una presentación para el cliente el lunes, y un montón de gráficos que todavía no existen.',
      'Lo probé todo. Los chatbots de IA pedían un prompt y devolvían una **imagen** de un gráfico — plana, ineditable, inútil en cuanto cambiaba un número. Los plugins exigían instalación y cuenta. Las herramientas de BI, un almacén de datos. Y lo que necesitaba era casi ridículamente simple: **entra una tabla, sale un gráfico de PowerPoint.**',
      'Así que lo construí. Pega tus datos, obtén trece tipos de gráficos realmente editables, exportados como objetos nativos de PowerPoint o GIF animados. Sin registro, sin ventana de chat, sin instalar nada — y tus números **nunca se almacenan ni acaban en la conversación de otro.**',
    ],
    storyMore: 'Leer la historia completa →',
    storyArtAlt: 'Tarde por la noche, un publicista sepultado entre diapositivas y gráficos impresos',
    howTitle: 'Tres pasos. Treinta segundos.',
    howSteps: [
      { title: 'Pega tus datos', desc: 'Texto plano, un CSV o un Excel — encabezados arriba, números debajo. Es todo el formato que necesita.' },
      { title: 'Elige un gráfico', desc: 'ChartThat lee la semántica de tu tabla y recomienda los tipos que de verdad encajan — tendencia, comparación o tasa — con una razón de una línea para cada uno.' },
      { title: 'Exporta a tu presentación', desc: 'Descarga un gráfico de PowerPoint nativo y editable, o un GIF animado en bucle. Sin marca de agua, sin registro, sin rodeos.' },
    ],
    perks: {
      title: 'Por qué engancha',
      items: [
        'Del pegado al gráfico en unos diez segundos',
        'Trece tipos de gráficos, según tus datos',
        'PPTX nativo: doble clic para editar, directo en tu presentación',
        'Sin registro, sin instalación, sin guardar nada',
        'Gratis. Sin marca de agua ni cuenta atrás de prueba',
      ],
    },
    guideTitle: 'Trece tipos de gráficos y cuándo usar cada uno',
    needsLabel: 'Requiere',
    guide: [
      { use: 'Comparar valores entre categorías — la respuesta por defecto a «¿cuál es mayor?»', needs: '1 columna de categorías + 1–3 columnas numéricas', eg: 'p. ej. ingresos trimestrales por línea de producto' },
      { use: 'La misma comparación, girada — mejor cuando los nombres son largos.', needs: '1 columna de categorías + 1–3 columnas numéricas', eg: 'p. ej. notoriedad de marca por campaña' },
      { use: 'Mostrar una tendencia en el tiempo — el caballo de batalla de cualquier dato con fechas.', needs: '1 columna temporal + 1–4 columnas numéricas', eg: 'p. ej. usuarios activos mensuales en un año' },
      { use: 'Una tendencia con sensación de volumen — ideal para acumulados y totales.', needs: '1 columna temporal + 1–3 columnas numéricas', eg: 'p. ej. registros acumulados por mes' },
      { use: 'Dos unidades, un gráfico: barras para el volumen, línea para la tasa.', needs: '1 columna de categoría/tiempo + numéricas + 1 columna %', eg: 'p. ej. barras de ingresos + línea de crecimiento' },
      { use: 'Parte y todo a la vez — totales y composición de un vistazo.', needs: '1 columna de categorías + 2+ columnas numéricas (misma unidad)', eg: 'p. ej. ventas por canal apiladas por trimestre' },
      { use: 'Antes vs después de muchos elementos — las pendientes revelan ganadores y perdedores.', needs: '1 columna de elementos + exactamente 2 columnas de periodos', eg: 'p. ej. este año vs el pasado, por producto' },
      { use: 'Relación entre dos métricas — correlación, grupos, valores atípicos.', needs: '2 columnas numéricas (+ etiqueta opcional)', eg: 'p. ej. gasto publicitario vs conversiones por campaña' },
      { use: 'Cómo se construye o se desgasta un total, paso a paso.', needs: '1 columna de etapas + 1 columna numérica (deltas)', eg: 'p. ej. presupuesto de lo previsto a lo real, partida a partida' },
      { use: 'Un perfil en 3+ métricas — compara entidades de un vistazo.', needs: '3+ columnas numéricas (misma unidad) + 1 columna de etiquetas', eg: 'p. ej. dos productos puntuados en cinco atributos' },
      { use: 'Cuota del total para pocas categorías — mejor entre 2 y 5 porciones.', needs: '1 columna de categorías + 1 columna numérica', eg: 'p. ej. cuota de mercado de las cuatro principales marcas' },
      { use: 'Un gráfico circular con aire — mismo trabajo, aspecto más ligero.', needs: '1 columna de categorías + 1 columna numérica', eg: 'p. ej. cuota de tráfico por fuente' },
      { use: 'Cuota jerárquica — del todo a las partes, anillo a anillo.', needs: '2 columnas de categorías + 1 columna numérica', eg: 'p. ej. ventas por región y luego por país' },
    ],
    casesTitle: 'Para quienes viven a base de presentaciones',
    cases: [
      { title: 'Consultores', desc: 'Convierte la hoja de cálculo del cliente en gráficos listos para el comité del lunes.' },
      { title: 'Marketing y publicidad', desc: 'Resultados de campaña, presupuestos, mix de medios — de la tabla al slide del cliente en un solo pegado.' },
      { title: 'Operaciones y producto', desc: 'Métricas semanales, funnels, comparaciones antes/después — al ritmo de los números.' },
      { title: 'Analistas y estudiantes', desc: 'Prueba trece formas de mostrar la misma tabla y lleva el archivo editable a tu informe.' },
    ],
    faqTitle: 'Preguntas frecuentes',
    faq: [
      { q: '¿ChartThat es realmente gratis?', a: 'Sí, por completo. Sin cuenta, sin marca de agua, sin periodo de prueba, sin límites ocultos. Funciona en un servidor pequeño que cuesta menos que un café al mes, y es suficiente.' },
      { q: '¿Mis datos están seguros?', a: 'Tu tabla se procesa en memoria, solo para construir tus gráficos. **Nunca almacenamos** tus datos, títulos ni nombres de columnas — nuestras estadísticas solo cuentan usos de funciones, sin IPs ni contenido.', linkText: 'Lee nuestra política de privacidad', linkHref: '/privacy.html' },
      { q: '¿Qué formatos de entrada se aceptan?', a: 'Pega texto plano o una tabla markdown, o sube un archivo **.csv** o **.xlsx**. Encabezados en la primera fila y números debajo — tipos, unidades, porcentajes y valores vacíos se detectan solos.' },
      { q: '¿Los gráficos de PowerPoint exportados son realmente editables?', a: 'Sí. El .pptx contiene un **objeto de gráfico nativo de PowerPoint**, no una imagen. Haz doble clic en PowerPoint, WPS o Keynote para editar datos y estilos.' },
      { q: '¿Qué tipos de gráficos puede generar?', a: 'Trece: barras, barras horizontales, línea, área, combo (barras + línea en doble eje), apiladas, pendiente, dispersión, cascada, radar, circular, donut y sunburst. La guía de arriba explica cuándo usar cada uno.' },
      { q: '¿Puedo exportar gráficos animados?', a: 'Sí — cualquier gráfico puede descargarse como **GIF animado en bucle**, con etiquetas opcionales y fondo sólido o transparente.' },
      { q: '¿Qué idiomas admite la interfaz?', a: '中文, English, Français, Deutsch y Español. La interfaz sigue automáticamente el idioma de tu navegador, y los títulos de los gráficos se escriben en tu idioma.' },
      { q: '¿Funciona con WPS y versiones antiguas de PowerPoint?', a: 'Cualquier herramienta que abra .pptx sirve — PowerPoint 2013+, WPS Office, Keynote, Google Slides. Los gráficos siguen siendo editables en todas, incluido WPS, sin avisos de vínculos rotos.' },
      { q: '¿Puedo usar los archivos con fines comerciales?', a: 'Por supuesto. Tus datos son tuyos y tus gráficos también — trabajo para clientes, informes, publicaciones, sin atribución necesaria.' },
    ],
    fnTitle: 'Notas de campo: Charts That Sell',
    fnIntro:
      'Nada de concursos de belleza de gráficos. Notas sobre cómo cerrar tratos con datos, escritas entre presentaciones — en inglés, porque ahí es donde ocurren las presentaciones.',
    fnCta: 'Todas las notas →',
    fnNotes: [
      {
        num: 'Nota #1',
        title: 'Choose the chart by the conclusion you\u2019re selling',
        desc: 'La urgencia quiere una línea. La brecha quiere barras. La reasignación quiere bloques. La atribución quiere una cascada.',
        href: '/guides/choose-chart-by-conclusion.html',
      },
      {
        num: 'Nota #2',
        title: 'One slide, one claim: the 3-second rule',
        desc: 'El cliente da tres segundos por página. Tres mensajes en una página equivalen a ninguno.',
        href: '/guides/one-slide-one-claim.html',
      },
    ],
  },
};

/** 极简富文本：**强调** → <strong>（内容为本文件常量，无注入面） */
function rich(text: string): ReactNode {
  const parts = text.split('**');
  if (parts.length === 1) return text;
  return parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>));
}

export function SiteContent() {
  const { lang, chartLabel } = useI18n();
  const copy = SITE_COPY[lang];

  return (
    <>
      <section className="c-block">
        <h2 className="c-title">{copy.storyTitle}</h2>
        <div className="story-grid">
          <div className="c-prose">
            {copy.story.map((p, i) => (
              <p key={i}>{rich(p)}</p>
            ))}
            <p>
              <a className="c-link" href="/about.html">
                {copy.storyMore}
              </a>
            </p>
          </div>
          <div className="story-art">
            <img
              src="/story-pain.jpg"
              width={2048}
              height={1365}
              alt={copy.storyArtAlt}
              loading="lazy"
            />
          </div>
        </div>
      </section>

      <section className="c-block">
        <h2 className="c-title">{copy.howTitle}</h2>
        <div className="how-grid">
          <div className="how-steps">
            {copy.howSteps.map((s, i) => (
              <div className="how-step" key={i}>
                <div className="how-num">{String(i + 1).padStart(2, '0')}</div>
                <div className="how-body">
                  <div className="how-title">{s.title}</div>
                  <div className="how-desc">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
          <aside className="perks">
            <div className="perks-title">{copy.perks.title}</div>
            <ul>
              {copy.perks.items.map((item, i) => (
                <li key={i}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M4.5 12.5l5 5 10-11" />
                  </svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      </section>

      <section className="c-block">
        <h2 className="c-title">{copy.guideTitle}</h2>
        <div className="chart-guide">
          {GUIDE_ORDER.map((type, i) => {
            const g = copy.guide[i];
            return (
              <div className="cg-card" key={type}>
                <ChartMini type={type} />
                <div className="cg-name">{chartLabel(type)}</div>
                <div className="cg-use">{g.use}</div>
                <div className="cg-meta">
                  <div className="cg-needs">
                    <span className="cg-tag">{copy.needsLabel}</span>
                    {g.needs}
                  </div>
                  <div className="cg-eg">{g.eg}</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="c-block">
        <h2 className="c-title">{copy.casesTitle}</h2>
        <div className="case-grid">
          {copy.cases.map((c, i) => (
            <div className="case-card" key={i}>
              <img
                className="case-art"
                src={CASE_ART[i % CASE_ART.length]}
                width="2048"
                height="1365"
                loading="lazy"
                alt={c.title}
              />
              <div className="case-title">{c.title}</div>
              <div className="case-desc">{c.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="c-block">
        <h2 className="c-title">{copy.fnTitle}</h2>
        <p className="fn-intro">{copy.fnIntro}</p>
        <div className="g-grid">
          {copy.fnNotes.map((n) => (
            <a className="g-card" href={n.href} key={n.num}>
              <span className="g-num">{n.num}</span>
              <h3>{n.title}</h3>
              <p>{n.desc}</p>
            </a>
          ))}
        </div>
        <a className="fn-more" href="/guides/">
          {copy.fnCta}
        </a>
      </section>

      <section className="c-block">
        <h2 className="c-title">{copy.faqTitle}</h2>
        <div className="faq">
          {copy.faq.map((f, i) => (
            <details className="faq-item" key={i}>
              <summary>{f.q}</summary>
              <p>
                {rich(f.a)}
                {f.linkText ? (
                  <>
                    {' '}
                    <a className="c-link" href={f.linkHref}>
                      {f.linkText}
                    </a>
                  </>
                ) : null}
              </p>
            </details>
          ))}
        </div>
      </section>
    </>
  );
}
