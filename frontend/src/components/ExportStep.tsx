import type { ChartSpec } from '../types';
import { CHART_TYPE_LABEL, SEMANTIC_LAYER_LABEL } from '../types';

interface ExportStepProps {
  selectedSpecs: ChartSpec[];
  onBack: () => void;
}

export default function ExportStep({ selectedSpecs, onBack }: ExportStepProps) {
  return (
    <section className="panel wide">
      <p className="badge">STEP 3 / 3 · 导出 PPTX</p>
      <h2>确认选中的图表</h2>

      <ul className="export-list">
        {selectedSpecs.map((s) => (
          <li key={s.id}>
            <span className="cand-name">{s.title || CHART_TYPE_LABEL[s.chart_type]}</span>
            <span className="cand-type">{CHART_TYPE_LABEL[s.chart_type]}</span>
            <span className="cand-layer">{SEMANTIC_LAYER_LABEL[s.semantic_layer]}</span>
          </li>
        ))}
      </ul>

      <div className="notice">M4 导出模块尚未实现，生成 .pptx 按钮待 `/api/generate` 就绪后启用。</div>

      <div className="foot-row">
        <button className="btn btn-ghost" onClick={onBack}>
          上一步
        </button>
        <button className="btn" disabled title="M4 未实现">
          生成 PPTX（待 M4）
        </button>
      </div>
    </section>
  );
}