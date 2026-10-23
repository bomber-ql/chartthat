import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ChartSpec } from '../types';
import { INCOMPLETE_TAIL, INCOMPLETE_TAIL_EN } from '../types';
import { applyDataLabels, specToOption } from '../utils/specToOption';
import { useTheme } from '../theme';
import { useI18n } from '../i18n';

interface ChartCardProps {
  spec: ChartSpec;
  selected: boolean;
  onSelect: (id: string) => void;
  /** 与导出 GIF 的「显示数据标签」同一开关：勾选后预览卡片同步显示数值。 */
  showLabels?: boolean;
}

export default function ChartCard({ spec, selected, onSelect, showLabels = false }: ChartCardProps) {
  const { theme } = useTheme();
  const { t, chartLabel, layerLabel, lang } = useI18n();
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ReturnType<typeof echarts.init> | null>(null);
  const optionRef = useRef<EChartsOption | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const option: EChartsOption = specToOption(spec, theme);
    if (showLabels) applyDataLabels(option, spec, theme);
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
  }, [spec, theme, showLabels]);

  const replayChart = () => {
    const chart = chartRef.current;
    const option = optionRef.current;
    if (!chart || !option) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    chart.clear();
    chart.setOption(option, true);
  };

  // v1.17：后端 lang 归一化为 zh/其余→en，徽标判断同样二分；大小写不敏感以兼容提示语在句中/句首
  const incompleteTail = lang === 'zh' ? INCOMPLETE_TAIL : INCOMPLETE_TAIL_EN;
  const incomplete = spec.reasoning.toLowerCase().includes(incompleteTail.toLowerCase());

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
          <span className="cand-name">{spec.title || chartLabel(spec.chart_type)}</span>
          <span className="cand-type">{chartLabel(spec.chart_type)}</span>
        </div>
        <span className="check" aria-hidden>
          {selected ? '✓' : ''}
        </span>
      </header>

      <div className="cand-stage">
        <div ref={ref} className="chart-holder" />
        <span className="cand-layer">{layerLabel(spec.semantic_layer)}</span>
      </div>

      <div className="cand-reasoning">
        {incomplete && <span className="tag-incomplete">{t('incompleteTag')}</span>}
        <p>{spec.reasoning || t('noReasoning')}</p>
      </div>
    </article>
  );
}