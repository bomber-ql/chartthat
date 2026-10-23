import { useRef, useState } from 'react';
import type { ChartSpec, SemanticTable } from '../types';
import { useI18n } from '../i18n';
import ShareButtons from './ShareButtons';

interface ControlPanelProps {
  table: SemanticTable | null;
  initialText: string;
  onInitialText: (t: string) => void;
  onParsed: (table: SemanticTable) => void;
  selectedSpecs: ChartSpec[];
  exportableCount: number;
  exporting: boolean;
  exportMsg: string | null;
  transparentGif: boolean;
  onToggleTransparent: (v: boolean) => void;
  showLabels: boolean;
  onToggleLabels: (v: boolean) => void;
  onExport: () => void;
  onExportGif: () => void;
  onRemove: (id: string) => void;
}

async function parseText(text: string, failMsg: string, lang: string): Promise<SemanticTable> {
  const res = await fetch('/api/parse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Lang': lang },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { message?: string } | null;
    throw new Error(body?.message ?? `${failMsg}（HTTP ${res.status}）`);
  }
  return (await res.json()) as SemanticTable;
}

async function parseFile(file: File, failMsg: string, lang: string): Promise<SemanticTable> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/parse', { method: 'POST', headers: { 'X-Lang': lang }, body: form });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { message?: string } | null;
    throw new Error(body?.message ?? `${failMsg}（HTTP ${res.status}）`);
  }
  return (await res.json()) as SemanticTable;
}

export default function ControlPanel({
  table,
  initialText,
  onInitialText,
  onParsed,
  selectedSpecs,
  exportableCount,
  exporting,
  exportMsg,
  onExport,
  onExportGif,
  transparentGif,
  onToggleTransparent,
  showLabels,
  onToggleLabels,
  onRemove,
}: ControlPanelProps) {
  const { t, lang, chartLabel } = useI18n();
  const [text, setText] = useState(initialText);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const run = async (fn: () => Promise<SemanticTable>, sourceText?: string) => {
    setLoading(true);
    setError(null);
    try {
      const t = await fn();
      onInitialText(sourceText ?? text);
      onParsed(t);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="panel side">
      <div className="panel-strip" aria-hidden />

      <section className="blk">
        <h2 className="blk-title">
          <span className="idx">01</span>
          {t('inputTitle')}
        </h2>
        <p className="muted">{t('inputHint')}</p>
        <textarea
          className="input-text"
          rows={7}
          value={text}
          placeholder={t('inputPlaceholder')}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="btn-row">
          <button
            className="btn"
            disabled={loading || !text.trim()}
            onClick={() => void run(() => parseText(text, t('parseFailed'), lang))}
          >
            {loading ? t('analyzing') : t('analyze')}
          </button>
          <button
            className="btn btn-ghost"
            disabled={loading}
            onClick={() => {
              const sample = t('sampleData');
              setText(sample);
              void run(() => parseText(sample, t('parseFailed'), lang), sample);
            }}
          >
            {t('sample')}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx"
            style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void run(() => parseFile(f, t('uploadFailed'), lang));
              e.target.value = '';
            }}
          />
          <button
            className="btn btn-ghost"
            disabled={loading}
            onClick={() => {
              if (fileRef.current) fileRef.current.click();
            }}
          >
            {t('upload')}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      {table && (
        <section className="blk">
          <h2 className="blk-title">
            <span className="idx">02</span>
            {t('summaryTitle')}
          </h2>
          <div className="stat-grid">
            <div className="stat">
              <span className="stat-num">{table.columns.length}</span>
              <span className="stat-label">{t('statFields')}</span>
            </div>
            <div className="stat">
              <span className="stat-num">{table.rows.length}</span>
              <span className="stat-label">{t('statRows')}</span>
            </div>
            <div className="stat">
              <span className="stat-num">{table.columns.filter((c) => c.role === 'percent').length}</span>
              <span className="stat-label">{t('statPctCols')}</span>
            </div>
          </div>
        </section>
      )}

      <section className="blk blk-grow">
        <h2 className="blk-title">
          <span className="idx">03</span>
          {t('selectedTitle')}
          <span className="count">{selectedSpecs.length}</span>
        </h2>
        {selectedSpecs.length === 0 ? (
          <p className="muted">{t('selectedEmpty')}</p>
        ) : (
          <ul className="sel-list">
            {selectedSpecs.map((s) => (
              <li key={s.id}>
                <span className="sel-dot" aria-hidden />
                <span className="sel-name">{s.title || chartLabel(s.chart_type)}</span>
                <span className="cand-type">{chartLabel(s.chart_type)}</span>
                <button className="sel-x" title={t('removeSelected')} onClick={() => onRemove(s.id)}>
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="blk blk-foot">
        <button
          className="btn btn-primary btn-block"
          disabled={exporting || exportableCount === 0}
          onClick={onExport}
        >
          {exporting ? t('exporting') : t('exportBtn', { n: exportableCount })}
        </button>
        <button
          className="btn btn-ghost btn-block"
          disabled={exporting || exportableCount === 0}
          onClick={onExportGif}
        >
          {exporting ? t('exporting') : t('exportGifBtn', { n: exportableCount })}
        </button>
        <label className="gif-opt">
          <input
            type="checkbox"
            checked={showLabels}
            disabled={exporting}
            onChange={(e) => onToggleLabels(e.target.checked)}
          />
          <span>{t('showDataLabels')}</span>
        </label>
        <label className="gif-opt">
          <input
            type="checkbox"
            checked={transparentGif}
            disabled={exporting}
            onChange={(e) => onToggleTransparent(e.target.checked)}
          />
          <span>{t('transparentGif')}</span>
        </label>
        {exportMsg && <p className="notice">{exportMsg}</p>}
        <p className="muted tiny">{t('exportHint')}</p>
        <p className="muted tiny">{t('exportGifHint')}</p>
        <ShareButtons />
      </section>
    </aside>
  );
}
