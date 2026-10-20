import { useState } from 'react';
import type { ChartSpec, RecommendResponse, SemanticTable } from './types';
import InputStep from './components/InputStep';
import PreviewStep from './components/PreviewStep';
import ExportStep from './components/ExportStep';

type Step = 1 | 2 | 3;

export default function App() {
  const [step, setStep] = useState<Step>(1);
  const [table, setTable] = useState<SemanticTable | null>(null);
  const [initialText, setInitialText] = useState('');
  const [recs, setRecs] = useState<ChartSpec[] | null>(null);
  const [degraded, setDegraded] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 全局选中态（按点击顺序维护，供导出端使用）
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const recById = new Map((recs ?? []).map((r) => [r.id, r]));
  const selectedSpecs = selectedIds
    .map((id) => recById.get(id))
    .filter((s): s is ChartSpec => Boolean(s));

  const handleParsed = (t: SemanticTable) => {
    setTable(t);
    setRecs(null);
    setSelectedIds([]);
    setError(null);
    setStep(2);
  };

  const generateRecs = async () => {
    if (!table) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(table),
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
  };

  return (
    <main className="page flow">
      <header className="app-head">
        <h1>智能数据图表 PPT 生成器</h1>
        <p className="muted">输入 → 候选图表预览 → 导出原生可编辑 Chart 对象的 .pptx</p>
      </header>

      {error && <p className="error banner">{error}</p>}

      {step === 1 && (
        <InputStep onParsed={handleParsed} initialText={initialText} onInitialText={setInitialText} />
      )}
      {step === 2 && (
        <PreviewStep
          recs={recs}
          degraded={degraded}
          generating={generating}
          selectedIds={selectedIds}
          onToggle={toggleSelect}
          onGenerate={() => void generateRecs()}
          onNext={() => setStep(3)}
          onBack={() => setStep(1)}
        />
      )}
      {step === 3 && (
        <ExportStep selectedSpecs={selectedSpecs} onBack={() => setStep(2)} />
      )}
    </main>
  );
}