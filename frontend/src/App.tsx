import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import type { ChartSpec, RecommendResponse, SemanticTable } from './types';
import ControlPanel from './components/ControlPanel';
import PreviewPanel from './components/PreviewPanel';
import Logo from './components/Logo';
import { SiteContent } from './components/SiteContent';
import { useTheme } from './theme';
import { useI18n, LANG_OPTIONS } from './i18n';
import type { Lang } from './i18n';
import { captureFrames } from './utils/captureFrames';

/** M4 支持导出的图型（SPEC v1.6 起十三型全覆盖；waterfall 透明底座等价、sunburst 降级圆环，见 §11 R-5） */
const EXPORTABLE = new Set([
  'line', 'bar', 'hbar', 'area', 'combo', 'stacked', 'slope',
  'scatter', 'waterfall', 'radar', 'pie', 'donut', 'sunburst',
]);

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const { lang, setLang, t } = useI18n();
  // index.html 静态内容区容器（v1.22 portal 目标；main.tsx 已清空其静态英文内容）
  const siteContentEl = document.getElementById('site-content');
  const [table, setTable] = useState<SemanticTable | null>(null);
  const [initialText, setInitialText] = useState('');
  const [recs, setRecs] = useState<ChartSpec[] | null>(null);
  const [degraded, setDegraded] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [transparentGif, setTransparentGif] = useState(false);
  const [showLabels, setShowLabels] = useState(false);

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
        headers: { 'Content-Type': 'application/json', 'X-Lang': lang },
        // v1.14：携带界面语言，后端 title/reasoning/降级模板按此语言产出；列名等数据保持原文
        body: JSON.stringify({ ...target, lang }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { message?: string } | null;
        throw new Error(body?.message ?? `${t('recommendFailed')}（HTTP ${res.status}）`);
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

  // 切换界面语言后，已生成的标题/理由按新语言重新推荐（数据与选择不变）
  useEffect(() => {
    if (table) void generateRecs(table);
    // 仅在语言变化时触发，table/generateRecs 不进依赖（解析时本就会重新推荐）
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

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
          headers: { 'Content-Type': 'application/json', 'X-Lang': lang },
          body: JSON.stringify({
            chart_type: s.chart_type,
            title: s.title,
            config: { dimension: s.dimension_column },
            show_labels: showLabels,
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
          throw new Error(body?.message ?? `${t('exportFailed')}（HTTP ${res.status}）`);
        }
        const blob = await res.blob();
        const safe = (s.title || s.chart_type).replace(/[\\/:*?"<>|]/g, '_');
        downloadBlob(blob, `${safe}.pptx`);
      }
      setExportMsg(t('exportDone', { n: targets.length }));
    } catch (e) {
      setExportMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setExporting(false);
    }
  };

  // v1.12 动效产物（SPEC §5.6a）：离屏采帧 → /api/generate-gif 直出循环 GIF 文件
  const exportGif = async () => {
    const targets = selectedSpecs.filter((s) => EXPORTABLE.has(s.chart_type));
    if (!targets.length) return;
    setExporting(true);
    setExportMsg(null);
    try {
      for (const s of targets) {
        const frames = await captureFrames(s, theme, { transparent: transparentGif, showLabels });
        const res = await fetch('/api/generate-gif', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Lang': lang },
          body: JSON.stringify({ frames, frame_ms: 100, transparent: transparentGif }),
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => null)) as { message?: string } | null;
          throw new Error(body?.message ?? `${t('exportFailed')}（HTTP ${res.status}）`);
        }
        const blob = await res.blob();
        const safe = (s.title || s.chart_type).replace(/[\\/:*?"<>|]/g, '_');
        downloadBlob(blob, `${safe}.gif`);
      }
      setExportMsg(t('exportDone', { n: targets.length }));
    } catch (e) {
      setExportMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="shell">
      <div className="bg-grid" aria-hidden />
      {/* 顶栏移出 stage：全页 sticky，内容区滚动时导航仍可达 */}
      <header className="topbar">
        <div className="brand">
          <span className="brand-logo"><Logo size={32} /></span>
          <div>
            <h1>ChartThat</h1>
            <p className="brand-sub">{t('brandSub')}</p>
          </div>
        </div>
        <div className="topbar-actions">
          <a className="tb-link" href="#site-content">{t('navAbout')}</a>
          <a className="tb-link" href="/guides/">{t('navGuides')}</a>
          <div className="status">
            <span className={`dot ${recs ? 'dot-on' : ''}`} aria-hidden />
            <span className="status-text">
              {recs ? t('statusReady', { n: recs.length }) : t('statusStandby')}
            </span>
          </div>
          <a
            className="tb-icon"
            href="https://github.com/bomber-ql/chartthat"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            title="GitHub"
          >
            <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden>
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
            </svg>
          </a>
          <button
            className="tgl"
            onClick={toggleTheme}
            title={theme === 'dark' ? t('themeToLight') : t('themeToDark')}
            aria-label={theme === 'dark' ? t('themeToLight') : t('themeToDark')}
          >
            {theme === 'dark' ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" />
              </svg>
            )}
          </button>
          <select
            className="tgl lang-select"
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
            title={t('langToggle')}
            aria-label={t('langToggle')}
          >
            {LANG_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      {/* 首屏容器：workspace 维持视口应用壳（高 = 视口 − 顶栏 − 提示条）；下方内容区随 body 滚动 */}
      <div className="stage">
        <span className="corner tl" aria-hidden />
        <span className="corner tr" aria-hidden />
        <span className="corner bl" aria-hidden />
        <span className="corner br" aria-hidden />

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
          transparentGif={transparentGif}
          onToggleTransparent={setTransparentGif}
          showLabels={showLabels}
          onToggleLabels={setShowLabels}
          onExport={() => void exportPptx()}
          onExportGif={() => void exportGif()}
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
          showLabels={showLabels}
        />
      </main>
      </div>

      {/* 首屏底部滚动提示条：文档流占位（零遮挡），点击锚跳内容区，滚动后随文档流自然离开 */}
      <a className="scroll-cue" href="#site-content">
        <span>{t('navCue')}</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M6 9l6 6 6-6" />
        </svg>
      </a>

      {/* v1.22 内容区多语言：portal 渲染到 index.html 的 #site-content（静态英文版已在 main.tsx 清空） */}
      {siteContentEl ? createPortal(<SiteContent />, siteContentEl) : null}
    </div>
  );
}
