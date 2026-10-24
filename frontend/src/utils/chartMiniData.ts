// 内容区图型速查卡的迷你演示数据与 option 覆写（ChartMini.tsx 用）。
// demo spec 固定内置、不走生成管线；迷你化覆写隐藏坐标轴/图例/标签/交互，只留图形形态。

import type { EChartsOption } from 'echarts';
import type { AxisSide, ChartSpec, ChartType, SeriesKind } from '../types';
import { specToOption } from './specToOption';
import type { Theme } from '../theme';

type DemoSeries = {
  name: string;
  kind?: SeriesKind;
  unit?: string;
  axis?: AxisSide;
  data: (number | null)[];
};

function demoSpec(
  type: ChartType,
  categories: string[],
  series: DemoSeries[],
  secondaryUnit?: string,
): ChartSpec {
  return {
    id: `demo-${type}`,
    chart_type: type,
    title: '',
    reasoning: '',
    semantic_layer: 'comparison',
    dimension_column: 'dim',
    categories,
    series: series.map((s, i) => ({
      name: s.name,
      source_column: `c${i}`,
      kind: s.kind,
      unit: s.unit ?? 'count',
      axis: s.axis ?? 'primary',
      data: s.data,
    })),
    axes: {
      primary: { unit: 'count' },
      ...(secondaryUnit ? { secondary: { unit: secondaryUnit } } : {}),
    },
  };
}

export const DEMO_SPECS: Record<ChartType, ChartSpec> = {
  bar: demoSpec('bar', ['Q1', 'Q2', 'Q3', 'Q4'], [
    { name: 'A', kind: 'bar', data: [5, 8, 6, 9] },
    { name: 'B', kind: 'bar', data: [4, 6, 8, 7] },
  ]),
  hbar: demoSpec('hbar', ['Q1', 'Q2', 'Q3', 'Q4'], [
    { name: 'A', kind: 'bar', data: [5, 8, 6, 9] },
    { name: 'B', kind: 'bar', data: [4, 6, 8, 7] },
  ]),
  line: demoSpec('line', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], [
    { name: 'A', kind: 'line', data: [3, 5, 4, 7, 6, 9] },
    { name: 'B', kind: 'line', data: [2, 4, 6, 5, 8, 7] },
  ]),
  area: demoSpec('area', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], [
    { name: 'A', kind: 'line', data: [3, 5, 4, 7, 6, 9] },
    { name: 'B', kind: 'line', data: [2, 4, 6, 5, 8, 7] },
  ]),
  combo: demoSpec('combo', ['Q1', 'Q2', 'Q3', 'Q4'], [
    { name: 'A', kind: 'bar', data: [5, 8, 6, 9] },
    { name: 'B', kind: 'line', unit: 'percent', axis: 'secondary', data: [0.1, 0.16, 0.12, 0.21] },
  ], 'percent'),
  stacked: demoSpec('stacked', ['Q1', 'Q2', 'Q3', 'Q4'], [
    { name: 'A', kind: 'bar', data: [3, 4, 2, 5] },
    { name: 'B', kind: 'bar', data: [2, 3, 4, 3] },
    { name: 'C', kind: 'bar', data: [1, 2, 2, 3] },
  ]),
  slope: demoSpec('slope', ['Before', 'After'], [
    { name: 'A', kind: 'line', data: [3, 6] },
    { name: 'B', kind: 'line', data: [5, 4] },
    { name: 'C', kind: 'line', data: [4, 7] },
  ]),
  scatter: demoSpec('scatter', ['A', 'B', 'C', 'D', 'E'], [
    { name: 'X', kind: 'scatter', data: [2, 4, 6, 8, 5] },
    { name: 'Y', kind: 'scatter', data: [3, 5, 4, 7, 6] },
  ]),
  waterfall: demoSpec('waterfall', ['Start', 'Up', 'Down', 'End'], [
    { name: 'A', kind: 'bar', data: [5, 3, -2, 4] },
  ]),
  radar: demoSpec('radar', ['Speed', 'Power', 'Range', 'Cost', 'Ease'], [
    { name: 'A', kind: 'line', data: [4, 5, 3, 4, 5] },
    { name: 'B', kind: 'line', data: [3, 4, 5, 3, 4] },
  ]),
  pie: demoSpec('pie', ['A', 'B', 'C', 'D'], [
    { name: 'S', kind: 'bar', data: [4, 3, 2, 1] },
  ]),
  donut: demoSpec('donut', ['A', 'B', 'C', 'D'], [
    { name: 'S', kind: 'bar', data: [4, 3, 2, 1] },
  ]),
  sunburst: demoSpec('sunburst', ['A', 'B', 'C', 'D'], [
    { name: 'S', kind: 'bar', data: [4, 3, 2, 1] },
  ]),
};

function hideAxis(axis: unknown): unknown {
  if (Array.isArray(axis)) return axis.map((a) => ({ ...(a as Record<string, unknown>), show: false }));
  if (axis && typeof axis === 'object') return { ...(axis as Record<string, unknown>), show: false };
  return axis;
}

// 迷你化覆写：去轴/图例/提示/交互/标签，网格贴边，纯形态展示。
export function miniOption(spec: ChartSpec, theme: Theme): EChartsOption {
  const option = specToOption(spec, theme) as unknown as Record<string, unknown>;
  delete option.legend;
  option.tooltip = { show: false };
  option.silent = true;
  option.grid = { left: 3, right: 3, top: 5, bottom: 3, containLabel: false };
  if (option.xAxis) option.xAxis = hideAxis(option.xAxis);
  if (option.yAxis) option.yAxis = hideAxis(option.yAxis);
  if (option.radar && typeof option.radar === 'object') {
    option.radar = {
      ...(option.radar as Record<string, unknown>),
      axisName: { show: false },
      radius: '68%',
      center: ['50%', '52%'],
    };
  }
  const series = option.series;
  if (Array.isArray(series)) {
    series.forEach((s) => {
      const sr = s as Record<string, unknown>;
      sr.label = { show: false };
      if (sr.type === 'pie') {
        sr.labelLine = { show: false };
        sr.center = ['50%', '50%'];
      }
      if (sr.type === 'sunburst') {
        sr.radius = ['12%', '92%'];
        sr.label = { show: false };
      }
      if (sr.type === 'radar') {
        sr.symbol = 'circle';
        sr.symbolSize = 3;
      }
    });
  }
  return option as unknown as EChartsOption;
}
