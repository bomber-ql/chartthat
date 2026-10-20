import { useRef, useState } from 'react';
import type { ChartSpec, SemanticTable } from '../types';
import { CHART_TYPE_LABEL } from '../types';

interface ControlPanelProps {
  table: SemanticTable | null;
  initialText: string;
  onInitialText: (t: string) => void;
  onParsed: (table: SemanticTable) => void;
  selectedSpecs: ChartSpec[];
  exportableCount: number;
  exporting: boolean;
  exportMsg: string | null;
  onExport: () => void;
  onRemove: (id: string) => void;
}

async function parseText(text: string): Promise<SemanticTable> {
  const res = await fetch('/api/parse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { message?: string } | null;
    throw new Error(body?.message ?? `解析失败（HTTP ${res.status}）`);
  }
  return (await res.json()) as SemanticTable;
}

async function parseFile(file: File): Promise<SemanticTable> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/parse', { method: 'POST', body: form });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { message?: string } | null;
    throw new Error(body?.message ?? `上传解析失败（HTTP ${res.status}）`);
  }
  return (await res.json()) as SemanticTable;
}

const SAMPLE =
  '| 平台 | 2024 MAU | 2025 MAU | 同比 | 2024 DAU | 2025 DAU |\n' +
  '|---|---|---|---|---|---|\n' +
  '| 微信 | 13.9亿 | 14.2亿 | +2.4% | 未披露 | 未披露 |\n' +
  '| 抖音 | 10.5亿 | 11.7亿 | +11.2% | 7.0亿 | 7.6亿 |\n' +
  '| 快手 | 7.2亿 | 7.0亿 | -2.8% | 4.1亿 | 4.0亿 |\n' +
  '| 微博 | 5.9亿 | 5.7亿 | -3.9% | 2.6亿 | 2.5亿 |';

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
  onRemove,
}: ControlPanelProps) {
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
          <span className="idx">01</span>数据输入
        </h2>
        <p className="muted">Markdown 表格 / CSV / xlsx；「未披露·无·—」自动识别为缺失，解析后自动生成候选图表。</p>
        <textarea
          className="input-text"
          rows={7}
          value={text}
          placeholder="粘贴表格文本，或点击「填入示例」快速体验…"
          onChange={(e) => setText(e.target.value)}
        />
        <div className="btn-row">
          <button className="btn" disabled={loading || !text.trim()} onClick={() => void run(() => parseText(text))}>
            {loading ? '解析中…' : '解析并生成图表'}
          </button>
          <button
            className="btn btn-ghost"
            disabled={loading}
            onClick={() => {
              setText(SAMPLE);
              void run(() => parseText(SAMPLE), SAMPLE);
            }}
          >
            一键示例
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx"
            style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void run(() => parseFile(f));
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
            上传
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      {table && (
        <section className="blk">
          <h2 className="blk-title">
            <span className="idx">02</span>解析摘要
          </h2>
          <div className="stat-grid">
            <div className="stat">
              <span className="stat-num">{table.columns.length}</span>
              <span className="stat-label">字段</span>
            </div>
            <div className="stat">
              <span className="stat-num">{table.rows.length}</span>
              <span className="stat-label">数据行</span>
            </div>
            <div className="stat">
              <span className="stat-num">{table.columns.filter((c) => c.role === 'percent').length}</span>
              <span className="stat-label">百分比列</span>
            </div>
          </div>
        </section>
      )}

      <section className="blk blk-grow">
        <h2 className="blk-title">
          <span className="idx">03</span>已选图表
          <span className="count">{selectedSpecs.length}</span>
        </h2>
        {selectedSpecs.length === 0 ? (
          <p className="muted">在右侧点击卡片选择要导出的图表。</p>
        ) : (
          <ul className="sel-list">
            {selectedSpecs.map((s) => (
              <li key={s.id}>
                <span className="sel-dot" aria-hidden />
                <span className="sel-name">{s.title || CHART_TYPE_LABEL[s.chart_type]}</span>
                <span className="cand-type">{CHART_TYPE_LABEL[s.chart_type]}</span>
                <button className="sel-x" title="移除" onClick={() => onRemove(s.id)}>
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
          {exporting ? '生成中…' : `导出 PPTX（${exportableCount}）`}
        </button>
        {exportMsg && <p className="notice">{exportMsg}</p>}
        <p className="muted tiny">图表为 WPS / PowerPoint 可双击编辑的原生 Chart 对象</p>
      </section>
    </aside>
  );
}
