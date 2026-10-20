import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ChartSpec } from '../types';
import { CHART_TYPE_LABEL, INCOMPLETE_TAIL, SEMANTIC_LAYER_LABEL } from '../types';
import { specToOption } from '../utils/specToOption';

interface ChartCardProps {
  spec: ChartSpec;
  selected: boolean;
  onSelect: (id: string) => void;
}

export default function ChartCard({ spec, selected, onSelect }: ChartCardProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ReturnType<typeof echarts.init> | null>(null);
  const optionRef = useRef<EChartsOption | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const option: EChartsOption = specToOption(spec);
    chart.setOption(option);
    chartRef.current = chart;
    optionRef.current = option;
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
      chartRef.current = null;
      optionRef.current = null;
    };
  }, [spec]);

  const replayChart = () => {
    const chart = chartRef.current;
    const option = optionRef.current;
    if (!chart || !option) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    chart.clear();
    chart.setOption(option, true);
  };

  const incomplete = spec.reasoning.includes(INCOMPLETE_TAIL);

  return (
    <article
      className={`cand ${selected ? 'cand-selected' : ''}`}
      role="button"
      tabIndex={0}
      onClick={() => onSelect(spec.id)}
      onMouseEnter={replayChart}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(spec.id);
        }
      }}
    >
      <header className="cand-head">
        <div className="cand-title">
          <span className="cand-name">{spec.title || CHART_TYPE_LABEL[spec.chart_type]}</span>
          <span className="cand-type">{CHART_TYPE_LABEL[spec.chart_type]}</span>
        </div>
        <span className="check" aria-hidden>
          {selected ? '✓' : ''}
        </span>
      </header>

      <div className="cand-stage">
        <div ref={ref} className="chart-holder" />
        <span className="cand-layer">{SEMANTIC_LAYER_LABEL[spec.semantic_layer]}</span>
      </div>

      <div className="cand-reasoning">
        {incomplete && <span className="tag-incomplete">数据不完整</span>}
        <p>{spec.reasoning || '暂无推荐理由'}</p>
      </div>
    </article>
  );
}