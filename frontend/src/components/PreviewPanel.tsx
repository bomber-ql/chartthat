import { useEffect, useRef, useState } from 'react';
import type { ChartSpec, SemanticLayer, SemanticTable } from '../types';
import { useI18n } from '../i18n';
import ChartCard from './ChartCard';
import Logo from './Logo';

interface PreviewPanelProps {
  table: SemanticTable | null;
  recs: ChartSpec[] | null;
  degraded: boolean;
  generating: boolean;
  selectedIds: string[];
  error: string | null;
  onToggle: (id: string) => void;
  onGenerate: () => void;
  /** 「显示数据标签」开关，透传给卡片与 GIF 采帧保持同一口径。 */
  showLabels: boolean;
}

const LAYER_ORDER: SemanticLayer[] = ['trend', 'comparison', 'rate'];
// 管线节奏：每张卡片「接通」的间隔（ms），卡片进场后内部线条继续逐段绘制。
const REVEAL_INTERVAL = 150;

export default function PreviewPanel({
  table,
  recs,
  degraded,
  generating,
  selectedIds,
  error,
  onToggle,
  onGenerate,
  showLabels,
}: PreviewPanelProps) {
  const { t, layerLabel } = useI18n();
  // 管线构建进度：已接通（可见）的卡片数；replayTick 用于「重播动画」强制重挂载。
  const [visible, setVisible] = useState(0);
  const [replayTick, setReplayTick] = useState(0);
  const [waitPct, setWaitPct] = useState(0);
  const timerRef = useRef<number | null>(null);

  const total = recs?.length ?? 0;
  const revealing = recs !== null && visible < total;
  const waiting = recs === null && generating;

  // 生成等待期：伪进度缓升至 92%，营造进程感（真实完成由 recs 到达触发）。
  useEffect(() => {
    if (!waiting) {
      setWaitPct(0);
      return undefined;
    }
    const t = window.setInterval(() => {
      setWaitPct((p) => (p >= 92 ? p : p + Math.max(1, Math.round((92 - p) * 0.06))));
    }, 90);
    return () => window.clearInterval(t);
  }, [waiting]);

  // 候选到达：清零后逐张接通；重播时同样走这条路径。
  useEffect(() => {
    if (!recs) {
      setVisible(0);
      return undefined;
    }
    setVisible(0);
    timerRef.current = window.setInterval(() => {
      setVisible((v) => {
        if (v + 1 >= total) {
          if (timerRef.current !== null) window.clearInterval(timerRef.current);
          return total;
        }
        return v + 1;
      });
    }, REVEAL_INTERVAL);
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
    };
  }, [recs, replayTick, total]);

  // 全量卡片的扁平顺序（按语义层分组顺序），用于管线索引与进场延迟。
  const ordered = recs
    ? LAYER_ORDER.flatMap((layer) => recs.filter((r) => r.semantic_layer === layer))
    : [];
  const indexOf = (id: string): number => ordered.findIndex((r) => r.id === id);

  return (
    <section className="panel main">
      <div className="panel-strip" aria-hidden />
      <div className="main-head">
        <div>
          <h2 className="main-title">{t('previewTitle')}</h2>
          <p className="muted">{t('previewHint')}</p>
        </div>
        <div className="main-actions">
          {recs?.length ? (
            <>
              <button
                className="btn btn-ghost"
                onClick={() => setReplayTick((n) => n + 1)}
                disabled={revealing}
                title={t('replayTitle')}
              >
                {revealing ? t('linking', { a: visible, b: total }) : t('replay')}
              </button>
              <button className="btn btn-ghost" onClick={onGenerate} disabled={generating || !table}>
                {generating ? t('generating') : t('regenerate')}
              </button>
            </>
          ) : null}
        </div>
      </div>

      {revealing ? (
        <div className="pipeline" role="status" aria-live="polite">
          <span className="pipeline-label">{t('pipelineBuilding', { a: visible, b: total })}</span>
          <span className="pipeline-track">
            <span className="pipeline-fill" style={{ width: `${(visible / Math.max(1, total)) * 100}%` }} />
          </span>
        </div>
      ) : null}

      {error && <p className="error banner">{error}</p>}
      {degraded && recs?.length ? (
        <p className="notice warn">{t('degradedNotice')}</p>
      ) : null}

      {!table ? (
        <div className="empty">
          <div className="hero">
            <span className="hero-logo" aria-hidden>
              <Logo size={58} />
            </span>
            <strong className="hero-name">ChartThat</strong>
            <p className="hero-tag">{t('brandSub')}</p>
            <p className="hero-intro">{t('heroIntro')}</p>
            <div className="hero-feats">
              <span>{t('heroFeat1')}</span>
              <span>{t('heroFeat2')}</span>
              <span>{t('heroFeat3')}</span>
            </div>
            <div className="hero-links">
              <a href="/make/">{t('heroLinkMakers')}</a>
              <a href="/guides/">{t('heroLinkGuides')}</a>
            </div>
          </div>
          <span className="empty-glyph" aria-hidden />
          <p>{t('emptyNoTable')}</p>
        </div>
      ) : !recs ? (
        generating ? (
          <div className="empty scan-stage">
            <span className="scan-beam" aria-hidden />
            <span className="empty-glyph pulse" aria-hidden />
            <p>{t('waitingText', { n: waitPct })}</p>
            <span className="pipeline-track wide">
              <span className="pipeline-fill" style={{ width: `${waitPct}%` }} />
            </span>
          </div>
        ) : (
          <div className="empty">
            <span className="empty-glyph" aria-hidden />
            <p>{t('failedTitle')}</p>
            <button className="btn" onClick={onGenerate} disabled={!table}>
              {t('generateBtn')}
            </button>
          </div>
        )
      ) : (
        <div className="scroll">
          {LAYER_ORDER.filter((layer) => recs.some((r) => r.semantic_layer === layer)).map((layer) => (
            <div className="layer" key={layer}>
              <h3 className="layer-title">
                <span className="layer-bar" aria-hidden />
                {layerLabel(layer)}
              </h3>
              <div className="cand-grid">
                {recs
                  .filter((r) => r.semantic_layer === layer)
                  .map((r) => {
                    const idx = indexOf(r.id);
                    if (idx >= visible) return null;
                    return (
                      <div className="card-enter" key={`${r.id}:${replayTick}`}>
                        <ChartCard
                          spec={r}
                          selected={selectedIds.includes(r.id)}
                          onSelect={onToggle}
                          showLabels={showLabels}
                        />
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
