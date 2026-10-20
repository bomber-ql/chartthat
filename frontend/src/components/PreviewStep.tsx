import type { ChartSpec, SemanticLayer } from '../types';
import { SEMANTIC_LAYER_LABEL } from '../types';
import ChartCard from './ChartCard';

interface PreviewStepProps {
  recs: ChartSpec[] | null;
  degraded: boolean;
  generating: boolean;
  selectedIds: string[];
  onToggle: (id: string) => void;
  onGenerate: () => void;
  onNext: () => void;
  onBack: () => void;
}

const LAYER_ORDER: SemanticLayer[] = ['trend', 'comparison', 'rate'];

export default function PreviewStep({
  recs,
  degraded,
  generating,
  selectedIds,
  onToggle,
  onGenerate,
  onNext,
  onBack,
}: PreviewStepProps) {
  return (
    <section className="panel wide">
      <p className="badge">STEP 2 / 3 · 候选图表</p>
      <div className="head-row">
        <h2>选择要纳入 PPT 的图表</h2>
        <button className="btn btn-ghost" onClick={onGenerate} disabled={generating}>
          {generating ? '生成中…' : recs?.length ? '重新生成' : '生成候选图表'}
        </button>
      </div>

      {degraded && recs?.length ? (
        <p className="notice">LLM 当前不可用，以下为启发式降级推荐（
        <code>degraded=true</code>）。</p>
      ) : null}

      {!recs ? (
        <p className="muted">尚未生成候选图表，请点击右上角「生成候选图表」。</p>
      ) : (
        LAYER_ORDER.filter((layer) => recs.some((r) => r.semantic_layer === layer)).map((layer) => (
          <div className="layer" key={layer}>
            <h3 className="layer-title">{SEMANTIC_LAYER_LABEL[layer]}</h3>
            <div className="cand-grid">
              {recs
                .filter((r) => r.semantic_layer === layer)
                .map((r) => (
                  <ChartCard
                    key={r.id}
                    spec={r}
                    selected={selectedIds.includes(r.id)}
                    onSelect={onToggle}
                  />
                ))}
            </div>
          </div>
        ))
      )}

      <div className="foot-row">
        <button className="btn btn-ghost" onClick={onBack}>
          上一步
        </button>
        <span className="muted">已选 {selectedIds.length} 张</span>
        <button className="btn" disabled={!selectedIds.length} onClick={onNext}>
          下一步：导出
        </button>
      </div>
    </section>
  );
}