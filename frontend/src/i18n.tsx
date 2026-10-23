// 多语言（DESIGN.md 多语言 / SPEC v1.17）：六语言 zh/en/fr/de/es；仅界面框架文案入字典，
// 图表标题/reasoning/列名保持后端原文。组件一律经 useI18n() 取词，禁止散落硬编码。
import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { ChartType, SemanticLayer } from './types';

export type Lang = 'zh' | 'en' | 'fr' | 'de' | 'es';

const STORAGE_KEY = 'dc-lang';

export const LANG_OPTIONS: ReadonlyArray<{ value: Lang; label: string }> = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Français' },
  { value: 'de', label: 'Deutsch' },
  { value: 'es', label: 'Español' },
];

const CHART_TYPE_LABELS: Record<Lang, Record<ChartType, string>> = {
  zh: {
    line: '折线图',
    bar: '柱状图',
    hbar: '条形图',
    area: '面积图',
    combo: '组合图',
    stacked: '堆叠图',
    slope: '斜率图',
    scatter: '散点图',
    waterfall: '瀑布图',
    radar: '雷达图',
    pie: '饼图',
    donut: '圆环图',
    sunburst: '旭日图',
  },
  en: {
    line: 'Line',
    bar: 'Bar',
    hbar: 'H-Bar',
    area: 'Area',
    combo: 'Combo',
    stacked: 'Stacked',
    slope: 'Slope',
    scatter: 'Scatter',
    waterfall: 'Waterfall',
    radar: 'Radar',
    pie: 'Pie',
    donut: 'Donut',
    sunburst: 'Sunburst',
  },
  fr: {
    line: 'Ligne',
    bar: 'Barres',
    hbar: 'Barres H',
    area: 'Aires',
    combo: 'Combiné',
    stacked: 'Empilé',
    slope: 'Pente',
    scatter: 'Nuage',
    waterfall: 'Cascade',
    radar: 'Radar',
    pie: 'Secteurs',
    donut: 'Anneau',
    sunburst: 'Solaire',
  },
  de: {
    line: 'Linie',
    bar: 'Säulen',
    hbar: 'Balken',
    area: 'Fläche',
    combo: 'Kombi',
    stacked: 'Gestapelt',
    slope: 'Steigung',
    scatter: 'Streudiagramm',
    waterfall: 'Wasserfall',
    radar: 'Radar',
    pie: 'Kreis',
    donut: 'Ring',
    sunburst: 'Sonnenrad',
  },
  es: {
    line: 'Líneas',
    bar: 'Barras',
    hbar: 'Barras H',
    area: 'Área',
    combo: 'Combinado',
    stacked: 'Apilado',
    slope: 'Pendiente',
    scatter: 'Dispersión',
    waterfall: 'Cascada',
    radar: 'Radar',
    pie: 'Circular',
    donut: 'Anillo',
    sunburst: 'Radial',
  },
};

const LAYER_LABELS: Record<Lang, Record<SemanticLayer, string>> = {
  zh: { trend: '趋势', comparison: '体量对比', rate: '变化率' },
  en: { trend: 'Trend', comparison: 'Comparison', rate: 'Rate' },
  fr: { trend: 'Tendance', comparison: 'Comparaison', rate: 'Taux' },
  de: { trend: 'Trend', comparison: 'Vergleich', rate: 'Rate' },
  es: { trend: 'Tendencia', comparison: 'Comparación', rate: 'Tasa' },
};

const zhStrings = {
  brandSub: '数据给我，图表给你',
  statusReady: '已生成 {n} 张候选',
  statusStandby: '待命',
  exportDone: '已下载 {n} 个文件。',
  exportFailed: '导出失败',
  recommendFailed: '推荐失败',
  themeToLight: '切换浅色主题',
  themeToDark: '切换深色主题',
  langToggle: '界面语言',
  inputTitle: '数据输入',
  inputHint: 'Markdown 表格 / CSV / xlsx；「未披露·无·—」自动识别为缺失，解析后自动生成候选图表。',
  inputPlaceholder: '粘贴表格文本，或点击「一键示例」快速体验…',
  sample: '一键示例',
  sampleData:
    '| 产品线 | 2024营收 | 2025营收 | 同比增长 | 市场份额 | 毛利率 |\n' +
    '|---|---|---|---|---|---|\n' +
    '| 产品线甲 | 12.3亿 | 14.8亿 | +20.3% | 18.5% | 32.1% |\n' +
    '| 产品线乙 | 9.8亿 | 10.2亿 | +4.1% | 13.2% | 28.6% |\n' +
    '| 产品线丙 | 7.5亿 | 7.1亿 | -5.3% | 9.4% | 24.8% |\n' +
    '| 产品线丁 | 5.2亿 | 6.6亿 | +26.9% | 8.1% | 35.2% |\n' +
    '| 产品线戊 | 3.4亿 | 未披露 | — | 4.7% | 19.5% |',
  upload: '上传',
  analyze: '解析并生成图表',
  analyzing: '解析中…',
  parseFailed: '解析失败',
  uploadFailed: '上传解析失败',
  summaryTitle: '解析摘要',
  statFields: '字段',
  statRows: '数据行',
  statPctCols: '百分比列',
  selectedTitle: '已选图表',
  selectedEmpty: '在右侧点击卡片选择要导出的图表。',
  removeSelected: '移除',
  exportBtn: '导出 PPTX（{n}）',
  exportGifBtn: '导出动效 GIF（{n}）',
  exporting: '生成中…',
  exportHint: 'PPTX：WPS / PowerPoint 可双击编辑的原生 Chart 对象',
  exportGifHint: 'GIF：循环播放的图表绘制动画，可直接插入文档/网页；透明背景仅适合贴到同色底',
  transparentGif: '透明背景',
  showDataLabels: '显示数据标签',
  previewTitle: '候选图表',
  previewHint: '点击卡片选中，图表将按选中状态导出',
  replayTitle: '重新播放生成动画（便于单独测试前端动效）',
  replay: '重播动画',
  linking: '接通中 {a}/{b}',
  generating: '生成中…',
  regenerate: '重新生成',
  pipelineBuilding: '管线构建 {a}/{b}',
  degradedNotice: 'LLM 当前不可用，以下为启发式降级推荐（degraded=true）。',
  emptyNoTable: '在左侧解析数据，将自动生成候选图表',
  waitingText: '正在解析语义并接通图表管线… {n}%',
  failedTitle: '生成失败或未开始，请点击重试',
  generateBtn: '生成候选图表',
  incompleteTag: '数据不完整',
  noReasoning: '暂无推荐理由',
  heroIntro: '粘贴表格数据，秒级生成十三种专业图表——导出原生可编辑的 PPTX，或循环播放的动效 GIF。',
  heroFeat1: '十三种图型',
  heroFeat2: '原生可编辑 PPTX',
  heroFeat3: '动效 GIF',
};

export type StringKey = keyof typeof zhStrings;

const enStrings: Record<StringKey, string> = {
  brandSub: 'Give us your data, we’ll chart that.',
  statusReady: '{n} candidates ready',
  statusStandby: 'Standby',
  exportDone: 'Downloaded {n} file(s).',
  exportFailed: 'Export failed',
  recommendFailed: 'Recommendation failed',
  themeToLight: 'Switch to light theme',
  themeToDark: 'Switch to dark theme',
  langToggle: 'Interface language',
  inputTitle: 'Data Input',
  inputHint: 'Markdown table / CSV / xlsx; "N/A · none · —" are detected as missing. Candidates are generated right after parsing.',
  inputPlaceholder: 'Paste a table here, or click "Load Sample" to try…',
  sample: 'Load Sample',
  sampleData:
    '| Product Line | Revenue 2024 | Revenue 2025 | YoY Growth | Market Share | Gross Margin |\n' +
    '|---|---|---|---|---|---|\n' +
    '| Product A | 123 | 148 | +20.3% | 18.5% | 32.1% |\n' +
    '| Product B | 98 | 102 | +4.1% | 13.2% | 28.6% |\n' +
    '| Product C | 75 | 71 | -5.3% | 9.4% | 24.8% |\n' +
    '| Product D | 52 | 66 | +26.9% | 8.1% | 35.2% |\n' +
    '| Product E | 34 | N/A | — | 4.7% | 19.5% |',
  upload: 'Upload',
  analyze: 'Parse & Generate',
  analyzing: 'Parsing…',
  parseFailed: 'Parse failed',
  uploadFailed: 'Upload parse failed',
  summaryTitle: 'Parse Summary',
  statFields: 'Fields',
  statRows: 'Rows',
  statPctCols: 'Percent',
  selectedTitle: 'Selected Charts',
  selectedEmpty: 'Click cards on the right to choose charts for export.',
  removeSelected: 'Remove',
  exportBtn: 'Export PPTX ({n})',
  exportGifBtn: 'Export Animated GIF ({n})',
  exporting: 'Generating…',
  exportHint: 'PPTX: native chart objects — double-click to edit in WPS / PowerPoint',
  exportGifHint: 'GIF: looping chart draw animation, drop into docs/web; transparent bg suits same-color backdrops only',
  transparentGif: 'Transparent background',
  showDataLabels: 'Show data labels',
  previewTitle: 'Candidate Charts',
  previewHint: 'Click cards to select; selected charts will be exported',
  replayTitle: 'Replay the generation animation (front-end motion test)',
  replay: 'Replay',
  linking: 'Linking {a}/{b}',
  generating: 'Generating…',
  regenerate: 'Regenerate',
  pipelineBuilding: 'Building {a}/{b}',
  degradedNotice: 'LLM unavailable; showing heuristic fallback recommendations (degraded=true).',
  emptyNoTable: 'Parse data on the left to generate candidate charts',
  waitingText: 'Parsing semantics and linking chart pipeline… {n}%',
  failedTitle: 'Generation failed or not started — please retry',
  generateBtn: 'Generate Charts',
  incompleteTag: 'Incomplete data',
  noReasoning: 'No rationale provided',
  heroIntro: 'Paste your table data and get thirteen pro chart types in seconds — export as native editable PPTX or looping animated GIFs.',
  heroFeat1: '13 chart types',
  heroFeat2: 'Native editable PPTX',
  heroFeat3: 'Animated GIF',
};

const frStrings: Record<StringKey, string> = {
  brandSub: 'Donnez-nous vos données, on vous fait des graphiques.',
  statusReady: '{n} graphiques prêts',
  statusStandby: 'En attente',
  exportDone: '{n} fichier(s) téléchargé(s).',
  exportFailed: "Échec de l'export",
  recommendFailed: 'Échec de la recommandation',
  themeToLight: 'Passer au thème clair',
  themeToDark: 'Passer au thème sombre',
  langToggle: "Langue de l'interface",
  inputTitle: 'Saisie des données',
  inputHint: 'Tableau Markdown / CSV / xlsx ; "N/A · aucun · —" détecté comme manquant. Les graphiques candidats sont générés juste après analyse.',
  inputPlaceholder: 'Collez un tableau ici, ou cliquez sur "Exemple" pour essayer…',
  sample: 'Exemple',
  sampleData:
    '| Gamme | Revenus 2024 | Revenus 2025 | Croissance | Part de marché | Marge brute |\n' +
    '|---|---|---|---|---|---|\n' +
    '| Product A | 123 | 148 | +20.3% | 18.5% | 32.1% |\n' +
    '| Product B | 98 | 102 | +4.1% | 13.2% | 28.6% |\n' +
    '| Product C | 75 | 71 | -5.3% | 9.4% | 24.8% |\n' +
    '| Product D | 52 | 66 | +26.9% | 8.1% | 35.2% |\n' +
    '| Product E | 34 | N/A | — | 4.7% | 19.5% |',
  upload: 'Importer',
  analyze: 'Analyser et générer',
  analyzing: 'Analyse…',
  parseFailed: "Échec de l'analyse",
  uploadFailed: "Échec de l'import",
  summaryTitle: "Résumé d'analyse",
  statFields: 'Champs',
  statRows: 'Lignes',
  statPctCols: 'Pourcentages',
  selectedTitle: 'Graphiques sélectionnés',
  selectedEmpty: 'Cliquez sur les cartes à droite pour choisir les graphiques à exporter.',
  removeSelected: 'Retirer',
  exportBtn: 'Exporter PPTX ({n})',
  exportGifBtn: 'Exporter GIF animé ({n})',
  exporting: 'Génération…',
  exportHint: 'PPTX : objets graphiques natifs, modifiables par double-clic dans WPS / PowerPoint',
  exportGifHint: 'GIF : animation de tracé en boucle pour docs/web ; fond transparent réservé aux fonds de même couleur',
  transparentGif: 'Fond transparent',
  showDataLabels: 'Afficher les étiquettes',
  previewTitle: 'Graphiques candidats',
  previewHint: 'Cliquez sur les cartes pour sélectionner ; les graphiques sélectionnés seront exportés',
  replayTitle: "Rejouer l'animation de génération (test d'animation front-end)",
  replay: 'Rejouer',
  linking: 'Connexion {a}/{b}',
  generating: 'Génération…',
  regenerate: 'Régénérer',
  pipelineBuilding: 'Construction {a}/{b}',
  degradedNotice: 'LLM indisponible ; recommandations heuristiques affichées (degraded=true).',
  emptyNoTable: 'Analysez des données à gauche pour générer des graphiques',
  waitingText: 'Analyse sémantique et connexion du pipeline… {n}%',
  failedTitle: 'Échec ou non démarré — veuillez réessayer',
  generateBtn: 'Générer les graphiques',
  incompleteTag: 'Données incomplètes',
  noReasoning: 'Aucune justification',
  heroIntro: 'Collez vos données et obtenez treize types de graphiques en quelques secondes — PPTX natif modifiable ou GIF animés en boucle.',
  heroFeat1: '13 types de graphiques',
  heroFeat2: 'PPTX natif modifiable',
  heroFeat3: 'GIF animé',
};

const deStrings: Record<StringKey, string> = {
  brandSub: 'Gib uns Daten, wir machen Diagramme draus.',
  statusReady: '{n} Diagramme bereit',
  statusStandby: 'Standby',
  exportDone: '{n} Datei(en) heruntergeladen.',
  exportFailed: 'Export fehlgeschlagen',
  recommendFailed: 'Empfehlung fehlgeschlagen',
  themeToLight: 'Zum hellen Design wechseln',
  themeToDark: 'Zum dunklen Design wechseln',
  langToggle: 'Oberflächensprache',
  inputTitle: 'Dateneingabe',
  inputHint: 'Markdown-Tabelle / CSV / xlsx; "N/A · keine · —" werden als fehlend erkannt. Kandidaten werden direkt nach dem Parsen erzeugt.',
  inputPlaceholder: 'Tabelle hier einfügen oder "Beispiel laden" klicken…',
  sample: 'Beispiel laden',
  sampleData:
    '| Produktlinie | Umsatz 2024 | Umsatz 2025 | Wachstum | Marktanteil | Bruttomarge |\n' +
    '|---|---|---|---|---|---|\n' +
    '| Product A | 123 | 148 | +20.3% | 18.5% | 32.1% |\n' +
    '| Product B | 98 | 102 | +4.1% | 13.2% | 28.6% |\n' +
    '| Product C | 75 | 71 | -5.3% | 9.4% | 24.8% |\n' +
    '| Product D | 52 | 66 | +26.9% | 8.1% | 35.2% |\n' +
    '| Product E | 34 | N/A | — | 4.7% | 19.5% |',
  upload: 'Hochladen',
  analyze: 'Parsen & Generieren',
  analyzing: 'Parsen…',
  parseFailed: 'Parsen fehlgeschlagen',
  uploadFailed: 'Upload-Parsen fehlgeschlagen',
  summaryTitle: 'Parse-Zusammenfassung',
  statFields: 'Felder',
  statRows: 'Zeilen',
  statPctCols: 'Prozent',
  selectedTitle: 'Ausgewählte Diagramme',
  selectedEmpty: 'Karten rechts anklicken, um Diagramme für den Export zu wählen.',
  removeSelected: 'Entfernen',
  exportBtn: 'PPTX exportieren ({n})',
  exportGifBtn: 'Animiertes GIF exportieren ({n})',
  exporting: 'Erstellen…',
  exportHint: 'PPTX: native Diagrammobjekte — per Doppelklick in WPS / PowerPoint bearbeitbar',
  exportGifHint: 'GIF: Zeichen-Animation im Loop für Docs/Web; transparenter Hintergrund nur für gleichfarbige Flächen',
  transparentGif: 'Transparenter Hintergrund',
  showDataLabels: 'Datenlabels anzeigen',
  previewTitle: 'Kandidaten-Diagramme',
  previewHint: 'Karten anklicken zum Auswählen; ausgewählte Diagramme werden exportiert',
  replayTitle: 'Generierungs-Animation erneut abspielen (Front-End-Motion-Test)',
  replay: 'Erneut abspielen',
  linking: 'Verbinde {a}/{b}',
  generating: 'Erstellen…',
  regenerate: 'Neu generieren',
  pipelineBuilding: 'Aufbau {a}/{b}',
  degradedNotice: 'LLM nicht verfügbar; heuristische Empfehlungen (degraded=true).',
  emptyNoTable: 'Links Daten parsen, um Kandidaten zu erzeugen',
  waitingText: 'Semantik wird geparst und Pipeline verbunden… {n}%',
  failedTitle: 'Fehlgeschlagen oder nicht gestartet — bitte erneut versuchen',
  generateBtn: 'Diagramme generieren',
  incompleteTag: 'Unvollständige Daten',
  noReasoning: 'Keine Begründung verfügbar',
  heroIntro: 'Tabellendaten einfügen und in Sekunden dreizehn Diagrammtypen erhalten — nativ editierbares PPTX oder animierte GIFs im Loop.',
  heroFeat1: '13 Diagrammtypen',
  heroFeat2: 'Nativ editierbares PPTX',
  heroFeat3: 'Animierte GIFs',
};

const esStrings: Record<StringKey, string> = {
  brandSub: 'Danos tus datos, te damos gráficos.',
  statusReady: '{n} gráficos listos',
  statusStandby: 'En espera',
  exportDone: '{n} archivo(s) descargado(s).',
  exportFailed: 'Error al exportar',
  recommendFailed: 'Error de recomendación',
  themeToLight: 'Cambiar a tema claro',
  themeToDark: 'Cambiar a tema oscuro',
  langToggle: 'Idioma de la interfaz',
  inputTitle: 'Entrada de datos',
  inputHint: 'Tabla Markdown / CSV / xlsx; "N/A · ninguno · —" se detectan como faltantes. Los candidatos se generan tras el análisis.',
  inputPlaceholder: 'Pega una tabla aquí o haz clic en "Ejemplo" para probar…',
  sample: 'Ejemplo',
  sampleData:
    '| Línea de producto | Ingresos 2024 | Ingresos 2025 | Crecimiento | Cuota de mercado | Margen bruto |\n' +
    '|---|---|---|---|---|---|\n' +
    '| Product A | 123 | 148 | +20.3% | 18.5% | 32.1% |\n' +
    '| Product B | 98 | 102 | +4.1% | 13.2% | 28.6% |\n' +
    '| Product C | 75 | 71 | -5.3% | 9.4% | 24.8% |\n' +
    '| Product D | 52 | 66 | +26.9% | 8.1% | 35.2% |\n' +
    '| Product E | 34 | N/A | — | 4.7% | 19.5% |',
  upload: 'Subir',
  analyze: 'Analizar y generar',
  analyzing: 'Analizando…',
  parseFailed: 'Error de análisis',
  uploadFailed: 'Error al analizar el archivo',
  summaryTitle: 'Resumen de análisis',
  statFields: 'Campos',
  statRows: 'Filas',
  statPctCols: 'Porcentaje',
  selectedTitle: 'Gráficos seleccionados',
  selectedEmpty: 'Haz clic en las tarjetas de la derecha para elegir los gráficos a exportar.',
  removeSelected: 'Quitar',
  exportBtn: 'Exportar PPTX ({n})',
  exportGifBtn: 'Exportar GIF animado ({n})',
  exporting: 'Generando…',
  exportHint: 'PPTX: objetos de gráfico nativos, editables con doble clic en WPS / PowerPoint',
  exportGifHint: 'GIF: animación de trazado en bucle para docs/web; fondo transparente solo para fondos del mismo color',
  transparentGif: 'Fondo transparente',
  showDataLabels: 'Mostrar etiquetas de datos',
  previewTitle: 'Gráficos candidatos',
  previewHint: 'Haz clic en las tarjetas para seleccionar; se exportarán los gráficos elegidos',
  replayTitle: 'Repetir la animación de generación (prueba de animación front-end)',
  replay: 'Repetir',
  linking: 'Conectando {a}/{b}',
  generating: 'Generando…',
  regenerate: 'Regenerar',
  pipelineBuilding: 'Construyendo {a}/{b}',
  degradedNotice: 'LLM no disponible; recomendaciones heurísticas (degraded=true).',
  emptyNoTable: 'Analiza datos a la izquierda para generar gráficos candidatos',
  waitingText: 'Analizando semántica y conectando la canalización… {n}%',
  failedTitle: 'Error o no iniciado — inténtalo de nuevo',
  generateBtn: 'Generar gráficos',
  incompleteTag: 'Datos incompletos',
  noReasoning: 'Sin justificación',
  heroIntro: 'Pega tus datos y obtén trece tipos de gráficos en segundos — PPTX nativo editable o GIF animados en bucle.',
  heroFeat1: '13 tipos de gráficos',
  heroFeat2: 'PPTX nativo editable',
  heroFeat3: 'GIF animado',
};

const STRINGS: Record<Lang, Record<StringKey, string>> = {
  zh: zhStrings,
  en: enStrings,
  fr: frStrings,
  de: deStrings,
  es: esStrings,
};

interface I18nContextValue {
  lang: Lang;
  setLang: (next: Lang) => void;
  t: (key: StringKey, vars?: Record<string, string | number>) => string;
  chartLabel: (type: ChartType) => string;
  layerLabel: (layer: SemanticLayer) => string;
}

function interpolate(text: string, vars?: Record<string, string | number>): string {
  if (!vars) return text;
  return Object.entries(vars).reduce(
    (acc, [k, v]) => acc.split(`{${k}}`).join(String(v)),
    text,
  );
}

function isLang(value: string): value is Lang {
  return LANG_OPTIONS.some((o) => o.value === value);
}

// v1.17：浏览器语言检测——zh/fr/de/es 前缀直通，其余一律英文兜底（出海默认英文而非中文）。
function detectBrowserLang(): Lang {
  try {
    const nav =
      (navigator.languages && navigator.languages[0]) || navigator.language || '';
    const prefix = nav.toLowerCase().split('-')[0];
    if (prefix === 'zh' || prefix === 'fr' || prefix === 'de' || prefix === 'es') {
      return prefix;
    }
  } catch {
    // SSR / 异常环境下静默走英文
  }
  return 'en';
}

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && isLang(saved)) return saved;
  } catch {
    // 隐私模式等场景下静默降级
  }
  return detectBrowserLang();
}

const I18nContext = createContext<I18nContextValue>({
  lang: 'en',
  setLang: () => undefined,
  t: (key) => STRINGS.en[key],
  chartLabel: (type) => CHART_TYPE_LABELS.en[type],
  layerLabel: (layer) => LAYER_LABELS.en[layer],
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);

  const value = useMemo<I18nContextValue>(() => {
    const setLang = (next: Lang) => {
      setLangState(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // 隐私模式等场景下静默降级
      }
    };
    return {
      lang,
      setLang,
      t: (key, vars) => interpolate(STRINGS[lang][key] ?? STRINGS.en[key], vars),
      chartLabel: (type) => CHART_TYPE_LABELS[lang][type],
      layerLabel: (layer) => LAYER_LABELS[lang][layer],
    };
  }, [lang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}
