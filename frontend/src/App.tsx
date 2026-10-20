import { useState } from 'react';
import type { ChartSpec, RecommendResponse, SemanticTable } from './types';
import ControlPanel from './components/ControlPanel';
import PreviewPanel from './components/PreviewPanel';

/** M4 支持导出的图型（SPEC v1.5 起六型全覆盖） */
const EXPORTABLE = new Set(['line', 'bar', 'combo', 'slope', 'scatter', 'pie']);

export default function App() {
  const [table, setTable] = useState<SemanticTable | null>(null);
  const [initialText, setInitialText] = useState('');
  const [recs, setRecs] = useState<ChartSpec[] | null>(null);
  const [degraded, setDegraded] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const recById = new Map((recs ?? []).map((r) => [r.id, r]));
  const selectedSpecs = selectedIds
    .map((id) => recById.get(id))
    .filter((s): s is ChartSpec => Boolean(s));
  const exportableCount = selectedSpecs.filter((s) => EXPORTABLE.has(s.chart_type)).length;

  // 解析成功 → 自动继续生成候选图表（合并为一次操作，无需再点「生成图表」）
  const handleParsed = (t: SemanticTable) => {
    setTable(t);
    setRecs(null);
    setSelectedIds([]);
    setError(null);
    setExportMsg(null);
    void generateRecs(t);
  };

  const generateRecs = async (target: SemanticTable | null = table) => {
    if (!target) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(target),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { message?: string } | null;
        throw new Error(body?.message ?? `推荐失败（HTTP ${res.status}）`);
      }
      const data = (await res.json()) as RecommendResponse;
      setRecs(data.recommendations);
      setDegraded(data.degraded);
      setSelectedIds((prev) => prev.filter((id) => data.recommendations.some((r) => r.id === id)));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    setExportMsg(null);
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const exportPptx = async () => {
    const targets = selectedSpecs.filter((s) => EXPORTABLE.has(s.chart_type));
    if (!targets.length) return;
    setExporting(true);
    setExportMsg(null);
    try {
      for (const s of targets) {
        const res = await fetch('/api/generate-pptx', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chart_type: s.chart_type,
            title: s.title,
            config: { dimension: s.dimension_column },
            data: {
              categories: s.categories,
              series: s.series.map((x) => ({
                name: x.name,
                kind: x.kind,
                axis: x.axis,
                unit: x.unit,
                data: x.data,
              })),
            },
          }),
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => null)) as { message?: string } | null;
          throw new Error(body?.message ?? `导出失败（HTTP ${res.status}）`);
        }
        const blob = await res.blob();
        const safe = (s.title || s.chart_type).replace(/[\\/:*?"<>|]/g, '_');
        downloadBlob(blob, `${safe}.pptx`);
      }
      setExportMsg(`已下载 ${targets.length} 个 .pptx 文件。`);
    } catch (e) {
      setExportMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="shell">
      <div className="bg-grid" aria-hidden />
      <span className="corner tl" aria-hidden />
      <span className="corner tr" aria-hidden />
      <span className="corner bl" aria-hidden />
      <span className="corner br" aria-hidden />

      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden />
          <div>
            <h1>DATA CHART PPTX</h1>
            <p className="brand-sub">智能数据图表 PPT 生成器</p>
          </div>
        </div>
        <div className="status">
          <span className={`dot ${recs ? 'dot-on' : ''}`} aria-hidden />
          <span className="status-text">{recs ? `已生成 ${recs.length} 张候选` : '待命'}</span>
        </div>
      </header>

      <main className="workspace">
        <ControlPanel
          table={table}
          initialText={initialText}
          onInitialText={setInitialText}
          onParsed={handleParsed}
          selectedSpecs={selectedSpecs}
          exportableCount={exportableCount}
          exporting={exporting}
          exportMsg={exportMsg}
          onExport={() => void exportPptx()}
          onRemove={toggleSelect}
        />
        <PreviewPanel
          table={table}
          recs={recs}
          degraded={degraded}
          generating={generating}
          selectedIds={selectedIds}
          error={error}
          onToggle={toggleSelect}
          onGenerate={() => void generateRecs()}
        />
      </main>
    </div>
  );
}
