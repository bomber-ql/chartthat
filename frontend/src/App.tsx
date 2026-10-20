import { useEffect, useState } from 'react';

type HealthState =
  | { status: 'checking' }
  | { status: 'ok' }
  | { status: 'error'; message: string };

export default function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'checking' });

  useEffect(() => {
    let cancelled = false;
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json() as Promise<{ status: string }>;
      })
      .then((data) => {
        if (!cancelled) {
          setHealth(data.status === 'ok' ? { status: 'ok' } : { status: 'error', message: 'unexpected payload' });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setHealth({ status: 'error', message: err instanceof Error ? err.message : String(err) });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="page">
      <section className="card">
        <p className="badge">SPEC v1.0 · 骨架已就绪</p>
        <h1>智能数据图表 PPT 生成器</h1>
        <p className="desc">
          输入不规整数据（文本 / CSV / Excel），自动分析语义并推荐图表，
          导出含原生可编辑 Chart 对象的 .pptx。
        </p>
        <div className={`health health-${health.status}`}>
          后端连通性：
          {health.status === 'checking' && <span>检测中…</span>}
          {health.status === 'ok' && <span>正常（/api/health → ok）</span>}
          {health.status === 'error' && <span>异常（{health.message}）</span>}
        </div>
        <ol className="steps">
          <li>数据输入与语义解析（M1 parser / M2 semantic）</li>
          <li>LLM 图表推荐与 ECharts 候选预览（M3 recommender）</li>
          <li>导出原生图表 PPTX（M4 pptx_builder）</li>
        </ol>
        <p className="notice">业务模块将在 SPEC.md 评审确认后按规格实现。</p>
      </section>
    </main>
  );
}
