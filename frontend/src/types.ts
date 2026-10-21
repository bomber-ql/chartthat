// 前后端共享的契约类型（与 SPEC §5.3 / §5.4 对齐）。

export type ColumnRole = 'dimension' | 'measure' | 'percent' | 'meta';
export type ChartType =
  | 'bar' | 'hbar' | 'line' | 'area' | 'combo' | 'stacked' | 'slope'
  | 'scatter' | 'waterfall' | 'radar' | 'pie' | 'donut' | 'sunburst';
export type SemanticLayer = 'trend' | 'comparison' | 'rate';
export type SeriesKind = 'line' | 'bar' | 'scatter';
export type AxisSide = 'primary' | 'secondary';

export interface SemanticColumn {
  name: string;
  role: ColumnRole;
  unit: string;
  nullable: boolean;
  missing_tokens_hit?: string[];
  warnings?: string[];
  stats?: {
    min?: number | null;
    max?: number | null;
    null_count: number;
    distinct_count: number;
  };
}

export interface SemanticTable {
  columns: SemanticColumn[];
  rows: (string | number | null)[][];
  warnings?: string[];
}

export interface AxisSpec {
  unit: string;
  title?: string | null;
}

export interface ChartSeries {
  name: string;
  source_column: string;
  kind?: SeriesKind;
  unit: string;
  axis: AxisSide;
  data: (number | null)[];
}

export interface ChartSpec {
  id: string;
  chart_type: ChartType;
  title: string;
  subtitle?: string | null;
  reasoning: string;
  semantic_layer: SemanticLayer;
  dimension_column: string;
  categories: string[];
  series: ChartSeries[];
  axes: { primary: AxisSpec; secondary?: AxisSpec };
}

export interface RecommendResponse {
  recommendations: ChartSpec[];
  degraded: boolean;
}

export const SEMANTIC_LAYER_LABEL: Record<SemanticLayer, string> = {
  trend: '趋势',
  comparison: '体量对比',
  rate: '变化率',
};

export const CHART_TYPE_LABEL: Record<ChartType, string> = {
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
};

// 缺失系列提示尾缀（与后端 INCOMPLETE_NOTE 对应，双语；用于卡片「数据缺失」徽标判断）。
export const INCOMPLETE_TAIL = '该系列数据不完整，建议不纳入';
export const INCOMPLETE_TAIL_EN = 'incomplete data for this series; exclude with caution';