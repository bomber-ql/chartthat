import type { ChartSpec, SemanticLayer, SemanticTable } from '../types';
import { SEMANTIC_LAYER_LABEL } from '../types';
import ChartCard from './ChartCard';

interface PreviewPanelProps {
  table: SemanticTable | null;
  recs: ChartSpec[] | null;
  degraded: boolean;
  generating: boolean;
  selectedIds: string[];
  error: string | null;
  onToggle: (id: string) => void;
  onGenerate: () => void;
}

const LAYER_ORDER: SemanticLayer[] = ['trend', 'comparison', 'rate'];

export default function PreviewPanel({
  table,
  recs,
  degraded,
  generating,
  selectedIds,
  error,
  onToggle,
  onGenerate,
}: PreviewPanelProps) {
  return (
    <section className="panel main">
      <div className="panel-strip" aria-hidden />
      <div className="main-head">
        <div>
          <h2 className="main-title">候选图表</h2>
          <p className="muted">点击卡片选中，图表将按选中状态导出</p>
        </div>
        <button className="btn" onClick={onGenerate} disabled={generating || !table}>
          {generating ? '生成中…' : recs?.length ? '重新生成' : '生成候选图表'}
        </button>
      </div>

      {error && <p className="error banner">{error}</p>}
      {degraded && recs?.length ? (
        <p className="notice warn">LLM 当前不可用，以下为启发式降级推荐（degraded=true）。</p>
      ) : null}

      {!table ? (
        <div className="empty">
          <span className="empty-glyph" aria-hidden />
          <p>先在左侧解析数据，再生成候选图表</p>
        </div>
      ) : !recs ? (
        <div className="empty">
          <span className="empty-glyph" aria-hidden />
          <p>数据已就绪，点击右上角「生成候选图表」</p>
        </div>
      ) : (
        <div className="scroll">
          {LAYER_ORDER.filter((layer) => recs.some((r) => r.semantic_layer === layer)).map((layer) => (
            <div className="layer" key={layer}>
              <h3 className="layer-title">
                <span className="layer-bar" aria-hidden />
                {SEMANTIC_LAYER_LABEL[layer]}
              </h3>
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
          ))}
        </div>
      )}
    </section>
  );
}
