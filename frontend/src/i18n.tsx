// 中英双语（DESIGN.md 多语言）：仅界面框架文案入字典；图表标题/reasoning/列名保持后端原文。
// 组件一律经 useI18n() 取词，禁止散落硬编码。
import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { ChartType, SemanticLayer } from './types';

export type Lang = 'zh' | 'en';

const STORAGE_KEY = 'dc-lang';

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
};

const LAYER_LABELS: Record<Lang, Record<SemanticLayer, string>> = {
  zh: { trend: '趋势', comparison: '体量对比', rate: '变化率' },
  en: { trend: 'Trend', comparison: 'Comparison', rate: 'Rate' },
};

const STRINGS = {
  zh: {
    brandSub: '智能数据图表 PPT 生成器',
    statusReady: '已生成 {n} 张候选',
    statusStandby: '待命',
    exportDone: '已下载 {n} 个文件。',
    exportFailed: '导出失败',
    recommendFailed: '推荐失败',
    themeToLight: '切换浅色主题',
    themeToDark: '切换深色主题',
    langToggle: 'Switch to English',
    inputTitle: '数据输入',
    inputHint: 'Markdown 表格 / CSV / xlsx；「未披露·无·—」自动识别为缺失，解析后自动生成候选图表。',
    inputPlaceholder: '粘贴表格文本，或点击「一键示例」快速体验…',
    sample: '一键示例',
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
  },
  en: {
    brandSub: 'Data Chart PPT Generator',
    statusReady: '{n} candidates ready',
    statusStandby: 'Standby',
    exportDone: 'Downloaded {n} file(s).',
    exportFailed: 'Export failed',
    recommendFailed: 'Recommendation failed',
    themeToLight: 'Switch to light theme',
    themeToDark: 'Switch to dark theme',
    langToggle: '切换到中文',
    inputTitle: 'Data Input',
    inputHint: 'Markdown table / CSV / xlsx; "N/A · none · —" are detected as missing. Candidates are generated right after parsing.',
    inputPlaceholder: 'Paste a table here, or click "Load Sample" to try…',
    sample: 'Load Sample',
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
  },
} as const;

export type StringKey = keyof (typeof STRINGS)['zh'];

interface I18nContextValue {
  lang: Lang;
  toggleLang: () => void;
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

function initialLang(): Lang {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'en' ? 'en' : 'zh';
  } catch {
    return 'zh';
  }
}

const I18nContext = createContext<I18nContextValue>({
  lang: 'zh',
  toggleLang: () => undefined,
  t: (key) => STRINGS.zh[key],
  chartLabel: (type) => CHART_TYPE_LABELS.zh[type],
  layerLabel: (layer) => LAYER_LABELS.zh[layer],
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(initialLang);

  const value = useMemo<I18nContextValue>(() => {
    const persist = (next: Lang) => {
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // 隐私模式等场景下静默降级
      }
    };
    return {
      lang,
      toggleLang: () =>
        setLang((cur) => {
          const next = cur === 'zh' ? 'en' : 'zh';
          persist(next);
          return next;
        }),
      t: (key, vars) => interpolate(STRINGS[lang][key], vars),
      chartLabel: (type) => CHART_TYPE_LABELS[lang][type],
      layerLabel: (layer) => LAYER_LABELS[lang][layer],
    };
  }, [lang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}
