// SPEC §8 唯一映射层：ChartSpec → ECharts option。
// 规则要点：null 断线不补 0；combo 主副轴；percent 恒为小数形态（0.112），仅展示层 ×100。
import type { EChartsOption } from 'echarts';
import type { AxisSpec, ChartSpec, ChartSeries } from '../types';

const GRID = { left: 8, right: 12, top: 28, bottom: 8, containLabel: true };
// 深色科技感色板：青蓝为主，辅以对比亮色（DESIGN.md）
const PALETTE = ['#22d3ee', '#3b82f6', '#34d399', '#fbbf24', '#fb7185', '#a78bfa'];
const TEXT_DIM = '#8ea2c0';
const AXIS_LINE = 'rgba(56,189,248,.18)';
const TOOLTIP = {
  backgroundColor: 'rgba(10,16,30,.92)',
  borderColor: 'rgba(56,189,248,.3)',
  textStyle: { color: '#e2e8f0', fontSize: 11 },
};

const pct = (v: number): string => `${(v * 100).toFixed(1)}%`;

// 生成动效：折线/柱体逐段「拉出」（管线感），扇区依次扫入；数据点渐进延迟。
const ANIM = {
  animation: true,
  animationThreshold: 2000,
  animationDuration: 950,
  animationEasing: 'cubicOut' as const,
  animationDelay: (idx: number): number => idx * 48,
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

function legend(series: ChartSeries[]) {
  return series.length > 1
    ? { top: 0, left: 0, itemWidth: 12, itemHeight: 8, icon: 'roundRect', textStyle: { fontSize: 10, color: TEXT_DIM } }
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
function singleAxisOption(spec: ChartSpec, type: ChartSeries['kind']): EChartsOption {
  const primary: AxisSpec = spec.axes.primary;
  return {
    ...ANIM,
    color: PALETTE,
    grid: GRID,
    tooltip: { trigger: 'axis', ...TOOLTIP },
    legend: legend(spec.series),
    xAxis: {
      type: 'category',
      data: spec.categories,
      axisLabel: { fontSize: 10, color: TEXT_DIM },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: AXIS_LINE } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: TEXT_DIM, formatter: axisFormatter(primary.unit) },
      splitLine: { lineStyle: { type: 'dashed', color: AXIS_LINE } },
    },
    series: cartesianSeries(spec, type),
  };
}

// combo：bar 挂主轴(0)、percent line 挂副轴(1)；副轴按 percent 格式化（SPEC §8 / C-4）。
function comboOption(spec: ChartSpec): EChartsOption {
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
      axisLabel: { fontSize: 9, color: TEXT_DIM, formatter: axisFormatter(spec.axes.primary.unit) },
      splitLine: { lineStyle: { type: 'dashed', color: AXIS_LINE } },
    },
    ...(hasSecondary
      ? [
          {
            type: 'value',
            scale: true,
            axisLabel: { fontSize: 9, color: TEXT_DIM, formatter: axisFormatter('percent') },
            splitLine: { show: false },
          },
        ]
      : []),
  ] as EChartsOption['yAxis'];
  return {
    ...ANIM,
    color: PALETTE,
    grid: GRID,
    tooltip: { trigger: 'axis', ...TOOLTIP },
    legend: legend(spec.series),
    xAxis: {
      type: 'category',
      data: spec.categories,
      axisLabel: { fontSize: 10, color: TEXT_DIM },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: AXIS_LINE } },
    },
    yAxis,
    series,
  } as EChartsOption;
}

// scatter：两序列配成 [x, y]；任一坐标 null 的整点剔除（V-7）。
function scatterOption(spec: ChartSpec): EChartsOption {
  const [xs, ys] = spec.series;
  const data: Array<[number, number]> = [];
  (xs?.data ?? []).forEach((xv, i) => {
    const yv = ys?.data?.[i];
    if (typeof xv === 'number' && typeof yv === 'number') data.push([xv, yv]);
  });
  return {
    ...ANIM,
    color: PALETTE,
    grid: GRID,
    tooltip: {
      trigger: 'item',
      ...TOOLTIP,
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
      axisLabel: { fontSize: 9, color: TEXT_DIM },
      name: xs?.name,
      nameTextStyle: { fontSize: 10, color: TEXT_DIM },
      splitLine: { lineStyle: { type: 'dashed', color: AXIS_LINE } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 9, color: TEXT_DIM },
      name: ys?.name,
      nameTextStyle: { fontSize: 10, color: TEXT_DIM },
      splitLine: { lineStyle: { type: 'dashed', color: AXIS_LINE } },
    },
    series: [{ type: 'scatter', data, symbolSize: 7 }],
  } as EChartsOption;
}

// pie：单 measure 序列；null 扇区剔除（V-8）。
function pieOption(spec: ChartSpec): EChartsOption {
  const s = spec.series[0];
  const data = spec.categories
    .map((c, i) => ({ name: c, value: s.data[i] }))
    .filter((d) => typeof d.value === 'number');
  return {
    ...ANIM,
    color: PALETTE,
    grid: { top: 8, bottom: 8, left: 8, right: 8 },
    tooltip: { trigger: 'item', ...TOOLTIP, formatter: '{b}: {c} ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['32%', '64%'],
        center: ['50%', '50%'],
        data,
        label: { fontSize: 9, color: TEXT_DIM },
        labelLine: { lineStyle: { color: AXIS_LINE } },
        valueFormatter: valueFormatter(s.unit),
      },
    ],
  } as EChartsOption;
}

export function specToOption(spec: ChartSpec): EChartsOption {
  switch (spec.chart_type) {
    case 'combo':
      return comboOption(spec);
    case 'scatter':
      return scatterOption(spec);
    case 'pie':
      return pieOption(spec);
    case 'bar':
      return singleAxisOption(spec, 'bar');
    case 'line':
      return singleAxisOption(spec, 'line');
    case 'slope':
      // 斜率图本质是跨类目的两点趋势线（SPEC §8）：以 category 为类目、每序列一条折线。
      return singleAxisOption(spec, 'line');
    default:
      return singleAxisOption(spec, 'bar');
  }
}