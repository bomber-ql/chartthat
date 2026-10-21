// SPEC §8 唯一映射层：ChartSpec → ECharts option。
// 规则要点：null 断线不补 0；combo 主副轴；percent 恒为小数形态（0.112），仅展示层 ×100。
// 双主题（DESIGN.md）：深色/浅色两套色板与文字色，由 specToOption 的 theme 参数切换。
import type { EChartsOption } from 'echarts';
import type { AxisSpec, ChartSpec, ChartSeries } from '../types';
import type { Theme } from '../theme';

const GRID = { left: 8, right: 12, top: 28, bottom: 8, containLabel: true };

interface ThemeTokens {
  palette: string[];
  textDim: string;
  axisLine: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  stageBorder: string;
}

// 深色：青蓝发光色板；浅色：同色相降明度，白底可读（DESIGN.md）
const THEME_TOKENS: Record<Theme, ThemeTokens> = {
  dark: {
    palette: ['#22d3ee', '#3b82f6', '#34d399', '#fbbf24', '#fb7185', '#a78bfa'],
    textDim: '#8ea2c0',
    axisLine: 'rgba(56,189,248,.18)',
    tooltipBg: 'rgba(10,16,30,.92)',
    tooltipBorder: 'rgba(56,189,248,.3)',
    tooltipText: '#e2e8f0',
    stageBorder: 'rgba(6,10,19,.9)',
  },
  light: {
    palette: ['#0891b2', '#2563eb', '#059669', '#d97706', '#e11d48', '#7c3aed'],
    textDim: '#5b6b82',
    axisLine: 'rgba(15,28,46,.16)',
    tooltipBg: 'rgba(255,255,255,.96)',
    tooltipBorder: 'rgba(8,145,178,.3)',
    tooltipText: '#0f1c2e',
    stageBorder: 'rgba(244,248,252,.95)',
  },
};

function tooltipStyle(T: ThemeTokens) {
  return {
    backgroundColor: T.tooltipBg,
    borderColor: T.tooltipBorder,
    textStyle: { color: T.tooltipText, fontSize: 11 },
  };
}

const pct = (v: number): string => `${(v * 100).toFixed(1)}%`;

// 生成动效：折线/柱体逐段「拉出」（管线感），扇区依次扫入；数据点渐进延迟。
const ANIM = {
  animation: true,
  animationThreshold: 2000,
  animationDuration: 1500,
  animationEasing: 'cubicOut' as const,
  animationDelay: (idx: number): number => idx * 70,
  animationDurationUpdate: 320,
  animationEasingUpdate: 'cubicOut' as const,
  animationDelayUpdate: 120,
};

// 数据值不落地改造，仅 tooltip/label 展示层追加单位（SPEC §8）。
function valueFormatter(unit: string): (v: unknown) => string {
  return (v: unknown): string => {
    if (v == null || typeof v !== 'number' || Number.isNaN(v)) return '-';
    const n = Number(v);
    if (unit === 'percent') return pct(n);
    if (unit === 'yi') return `${n} 亿`;
    if (unit === 'wan') return `${n} 万`;
    return String(n);
  };
}

function axisFormatter(unit: string): (v: number) => string {
  return (v: number): string => {
    if (unit === 'percent') return pct(v);
    if (unit === 'yi') return `${v} 亿`;
    if (unit === 'wan') return `${v} 万`;
    return String(v);
  };
}

function legend(series: ChartSeries[], T: ThemeTokens) {
  return series.length > 1
    ? { top: 0, left: 0, itemWidth: 12, itemHeight: 8, icon: 'roundRect', textStyle: { fontSize: 10, color: T.textDim } }
    : undefined;
}

function cartesianSeries(spec: ChartSpec, defaultType: ChartSeries['kind'], connectNulls = false): EChartsOption['series'] {
  return spec.series.map((s) => ({
    name: s.name,
    type: s.kind ?? defaultType,
    data: s.data,
    connectNulls,
    smooth: defaultType === 'line',
    valueFormatter: valueFormatter(s.unit),
  })) as EChartsOption['series'];
}

// bar / line / slope：单主类别轴折/柱（SPEC §8）。
function singleAxisOption(spec: ChartSpec, type: ChartSeries['kind'], T: ThemeTokens): EChartsOption {
  const primary: AxisSpec = spec.axes.primary;
  return {
    ...ANIM,
    color: T.palette,
    grid: GRID,
    tooltip: { trigger: 'axis', ...tooltipStyle(T) },
    legend: legend(spec.series, T),
    xAxis: {
      type: 'category',
      data: spec.categories,
      axisLabel: { fontSize: 10, color: T.textDim },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: T.axisLine } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: T.textDim, formatter: axisFormatter(primary.unit) },
      splitLine: { lineStyle: { type: 'dashed', color: T.axisLine } },
    },
    series: cartesianSeries(spec, type),
  };
}

// combo：bar 挂主轴(0)、percent line 挂副轴(1)；副轴按 percent 格式化（SPEC §8 / C-4）。
function comboOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const hasSecondary = spec.series.some((s) => s.axis === 'secondary') || Boolean(spec.axes.secondary);
  const series: EChartsOption['series'] = spec.series.map((s) => ({
    name: s.name,
    type: s.kind ?? 'bar',
    data: s.data,
    connectNulls: false,
    yAxisIndex: s.axis === 'secondary' ? 1 : 0,
    valueFormatter: valueFormatter(s.unit),
  })) as EChartsOption['series'];
  const yAxis = [
    {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: T.textDim, formatter: axisFormatter(spec.axes.primary.unit) },
      splitLine: { lineStyle: { type: 'dashed', color: T.axisLine } },
    },
    ...(hasSecondary
      ? [
          {
            type: 'value',
            scale: true,
            axisLabel: { fontSize: 9, color: T.textDim, formatter: axisFormatter('percent') },
            splitLine: { show: false },
          },
        ]
      : []),
  ] as EChartsOption['yAxis'];
  return {
    ...ANIM,
    color: T.palette,
    grid: GRID,
    tooltip: { trigger: 'axis', ...tooltipStyle(T) },
    legend: legend(spec.series, T),
    xAxis: {
      type: 'category',
      data: spec.categories,
      axisLabel: { fontSize: 10, color: T.textDim },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: T.axisLine } },
    },
    yAxis,
    series,
  } as EChartsOption;
}

// scatter：两序列配成 [x, y]；任一坐标 null 的整点剔除（V-7）。
function scatterOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const [xs, ys] = spec.series;
  const data: Array<[number, number]> = [];
  (xs?.data ?? []).forEach((xv, i) => {
    const yv = ys?.data?.[i];
    if (typeof xv === 'number' && typeof yv === 'number') data.push([xv, yv]);
  });
  return {
    ...ANIM,
    color: T.palette,
    grid: GRID,
    tooltip: {
      trigger: 'item',
      ...tooltipStyle(T),
      formatter: (params: unknown) => {
        const p = params as { name?: string; value?: [number, number] };
        const v = p.value ?? [0, 0];
        return `${p.name ?? ''}<br/>${xs?.name ?? 'X'}: ${valueFormatter(xs?.unit ?? 'count')(v[0])}<br/>${
          ys?.name ?? 'Y'
        }: ${valueFormatter(ys?.unit ?? 'count')(v[1])}`;
      },
    },
    xAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: T.textDim },
      name: xs?.name,
      nameTextStyle: { fontSize: 10, color: T.textDim },
      splitLine: { lineStyle: { type: 'dashed', color: T.axisLine } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: T.textDim },
      name: ys?.name,
      nameTextStyle: { fontSize: 10, color: T.textDim },
      splitLine: { lineStyle: { type: 'dashed', color: T.axisLine } },
    },
    series: [{ type: 'scatter', data, symbolSize: 7 }],
  } as EChartsOption;
}

// hbar（条形图）：类目轴/数值轴互换，类目从顶部开始。
function hbarOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const primary: AxisSpec = spec.axes.primary;
  return {
    ...ANIM,
    color: T.palette,
    grid: GRID,
    tooltip: { trigger: 'axis', ...tooltipStyle(T) },
    legend: legend(spec.series, T),
    xAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: T.textDim, formatter: axisFormatter(primary.unit) },
      splitLine: { lineStyle: { type: 'dashed', color: T.axisLine } },
    },
    yAxis: {
      type: 'category',
      data: spec.categories,
      inverse: true,
      axisLabel: { fontSize: 10, color: T.textDim },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: T.axisLine } },
    },
    series: cartesianSeries(spec, 'bar'),
  };
}

// area（面积图）：强制折线 + 半透明面积填充（kind 异常时也不退化为柱，SPEC §8 映射层兜底）。
function areaOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const base = singleAxisOption(spec, 'line', T);
  const series = ((base.series ?? []) as Array<Record<string, unknown>>).map((s) => ({
    ...s,
    type: 'line',
    areaStyle: { opacity: 0.16 },
    smooth: true,
  }));
  return { ...base, series } as EChartsOption;
}

// stacked（堆叠图，V-9 ≥2 序列同单位）：柱体共用 stack 叠加。
function stackedOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const base = singleAxisOption(spec, 'bar', T);
  const series = ((base.series ?? []) as Array<Record<string, unknown>>).map((s) => ({
    ...s,
    stack: 'total',
    barMaxWidth: 26,
  }));
  return { ...base, series } as EChartsOption;
}

// waterfall（瀑布图，V-10 恰好 1 序列）：透明底座（前值累计）+ 增量柱，同 stack 等价表达（SPEC §11 R-5）。
// null 保持空点不补 0（C-3）：底座与增量同位置都置 null。
function waterfallOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const s: ChartSeries = spec.series[0] ?? { name: '', source_column: '', unit: '', axis: 'primary', data: [] };
  const base: Array<number | null> = [];
  const delta: Array<number | null> = [];
  let cumulative = 0;
  s.data.forEach((v) => {
    if (typeof v !== 'number' || Number.isNaN(v)) {
      base.push(null);
      delta.push(null);
      return;
    }
    if (v >= 0) {
      base.push(cumulative);
      delta.push(v);
    } else {
      base.push(cumulative + v);
      delta.push(-v);
    }
    cumulative += v;
  });
  const fmt = valueFormatter(s.unit);
  return {
    ...ANIM,
    color: T.palette,
    grid: GRID,
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle(T),
      formatter: (params: unknown) => {
        const list = params as Array<{ name?: string; dataIndex?: number }>;
        const idx = list[0]?.dataIndex ?? 0;
        return `${list[0]?.name ?? ''}<br/>${s.name}: ${fmt(s.data[idx])}`;
      },
    },
    xAxis: {
      type: 'category',
      data: spec.categories,
      axisLabel: { fontSize: 10, color: T.textDim },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: T.axisLine } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: T.textDim, formatter: axisFormatter(spec.axes.primary.unit) },
      splitLine: { lineStyle: { type: 'dashed', color: T.axisLine } },
    },
    series: [
      {
        name: '__base__',
        type: 'bar',
        stack: 'wf',
        data: base,
        silent: true,
        itemStyle: { color: 'transparent' },
        emphasis: { itemStyle: { color: 'transparent' } },
        tooltip: { show: false },
      },
      { name: s.name, type: 'bar', stack: 'wf', data: delta, barMaxWidth: 26 },
    ],
  } as EChartsOption;
}

// radar（雷达图，V-11 ≥3 序列同单位禁 percent）：类目为维度指标，多序列互比。
function radarOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const maxVal = Math.max(
    0,
    ...spec.series.flatMap((s) => s.data.filter((v): v is number => typeof v === 'number')),
  );
  const top = maxVal > 0 ? maxVal * 1.2 : 1;
  const indicator = spec.categories.map((c) => ({ name: c, max: top }));
  return {
    ...ANIM,
    color: T.palette,
    tooltip: {
      trigger: 'item',
      ...tooltipStyle(T),
      formatter: (params: unknown) => {
        const p = params as { name?: string; value?: Array<number | null> };
        const rows = (p.value ?? [])
          .map((v, i) => `${spec.categories[i] ?? ''}: ${v == null || typeof v !== 'number' ? '-' : valueFormatter(spec.axes.primary.unit)(v)}`)
          .join('<br/>');
        return `${p.name ?? ''}<br/>${rows}`;
      },
    },
    legend: legend(spec.series, T),
    radar: {
      indicator,
      radius: '60%',
      center: ['50%', '54%'],
      axisName: { color: T.textDim, fontSize: 9 },
      splitLine: { lineStyle: { color: T.axisLine } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: T.axisLine } },
    },
    series: [
      {
        type: 'radar',
        symbolSize: 4,
        data: spec.series.map((s) => ({
          name: s.name,
          value: s.data,
          areaStyle: { opacity: 0.12 },
        })),
      },
    ],
  } as EChartsOption;
}

// sunburst（旭日图）：契约数据为单 measure 平铺序列（V-12），预览用单层旭日表达；导出降级为圆环（R-5）。
function sunburstOption(spec: ChartSpec, T: ThemeTokens): EChartsOption {
  const s = spec.series[0];
  const data = spec.categories
    .map((c, i) => ({ name: c, value: s?.data[i] }))
    .filter((d) => typeof d.value === 'number');
  return {
    ...ANIM,
    color: T.palette,
    tooltip: { trigger: 'item', ...tooltipStyle(T), formatter: '{b}: {c}' },
    series: [
      {
        type: 'sunburst',
        radius: ['16%', '78%'],
        center: ['50%', '50%'],
        data,
        label: { fontSize: 9, color: T.textDim, rotate: 'radial' },
        itemStyle: { borderColor: T.stageBorder, borderWidth: 1 },
      },
    ],
  } as EChartsOption;
}

// pie / donut：单 measure 序列；null 扇区剔除（V-8 / V-12）。donut 加大空心半径。
function pieOption(spec: ChartSpec, T: ThemeTokens, hollow = false): EChartsOption {
  const s = spec.series[0];
  const data = spec.categories
    .map((c, i) => ({ name: c, value: s.data[i] }))
    .filter((d) => typeof d.value === 'number');
  return {
    ...ANIM,
    color: T.palette,
    grid: { top: 8, bottom: 8, left: 8, right: 8 },
    tooltip: { trigger: 'item', ...tooltipStyle(T), formatter: '{b}: {c} ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: hollow ? ['42%', '68%'] : ['0%', '64%'],
        center: ['50%', '50%'],
        data,
        label: { fontSize: 9, color: T.textDim },
        labelLine: { lineStyle: { color: T.axisLine } },
        valueFormatter: valueFormatter(s.unit),
      },
    ],
  } as EChartsOption;
}

export function specToOption(spec: ChartSpec, theme: Theme = 'dark'): EChartsOption {
  const T = THEME_TOKENS[theme];
  switch (spec.chart_type) {
    case 'combo':
      return comboOption(spec, T);
    case 'scatter':
      return scatterOption(spec, T);
    case 'pie':
      return pieOption(spec, T);
    case 'donut':
      return pieOption(spec, T, true);
    case 'sunburst':
      return sunburstOption(spec, T);
    case 'hbar':
      return hbarOption(spec, T);
    case 'area':
      return areaOption(spec, T);
    case 'stacked':
      return stackedOption(spec, T);
    case 'waterfall':
      return waterfallOption(spec, T);
    case 'radar':
      return radarOption(spec, T);
    case 'bar':
      return singleAxisOption(spec, 'bar', T);
    case 'line':
      return singleAxisOption(spec, 'line', T);
    case 'slope':
      // 斜率图本质是跨类目的两点趋势线（SPEC §8）：以 category 为类目、每序列一条折线。
      return singleAxisOption(spec, 'line', T);
    default:
      return singleAxisOption(spec, 'bar', T);
  }
}

interface LabelParams {
  name?: string;
  value?: unknown;
  dataIndex?: number;
}

// v1.13：GIF 采帧可选「显示数据标签」（SPEC 修订记录 v1.13）。GIF 为位图导出后不可
// 编辑，数值显示须在导出期决定；仅用于动效采帧，预览与标准 pptx 不启用。
export function applyDataLabels(option: EChartsOption, spec: ChartSpec, theme: Theme = 'dark'): void {
  const T = THEME_TOKENS[theme];
  const byName = new Map(spec.series.map((s) => [s.name, s]));
  const list = (Array.isArray(option.series) ? option.series : option.series ? [option.series] : []) as Array<Record<string, unknown>>;
  list.forEach((serie) => {
    if (!serie || typeof serie !== 'object') return;
    if (serie.name === '__base__') return; // waterfall 透明底座不标值
    const def = byName.get(String(serie.name ?? '')) ?? spec.series[0];
    if (!def) return;
    const fmt = valueFormatter(def.unit);
    const type = String(serie.type ?? '');
    const prev = (serie.label && typeof serie.label === 'object' ? serie.label : {}) as Record<string, unknown>;
    let label: Record<string, unknown>;
    if (spec.chart_type === 'waterfall') {
      // 显示带正负的真实增量（option 内存的是 abs 堆叠值，不能直接用）
      label = {
        show: true,
        position: 'top',
        fontSize: 9,
        color: T.tooltipText,
        formatter: (p: LabelParams): string => {
          const v = typeof p.dataIndex === 'number' ? def.data[p.dataIndex] : null;
          return typeof v === 'number' && !Number.isNaN(v) ? fmt(v) : '';
        },
      };
    } else if (type === 'pie' || type === 'sunburst') {
      label = {
        show: true,
        fontSize: 9,
        color: T.tooltipText,
        formatter: (p: LabelParams): string => {
          const v = p.value;
          return typeof v === 'number' && !Number.isNaN(v) ? `${p.name ?? ''}: ${fmt(v)}` : String(p.name ?? '');
        },
      };
    } else {
      label = {
        show: true,
        position: spec.chart_type === 'hbar' ? 'right' : spec.chart_type === 'stacked' ? 'inside' : 'top',
        fontSize: 9,
        color: T.tooltipText,
        formatter: (p: LabelParams): string => {
          const raw = Array.isArray(p.value) ? p.value[p.value.length - 1] : p.value;
          return typeof raw === 'number' && !Number.isNaN(raw) ? fmt(raw) : '';
        },
      };
    }
    serie.label = { ...prev, ...label };
  });
}
