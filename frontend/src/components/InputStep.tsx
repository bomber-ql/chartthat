import { useRef, useState } from 'react';
import type { SemanticTable } from '../types';

interface InputStepProps {
  onParsed: (table: SemanticTable) => void;
  initialText: string;
  onInitialText: (t: string) => void;
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

export default function InputStep({ onParsed, initialText, onInitialText }: InputStepProps) {
  const [text, setText] = useState(initialText);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const run = async (fn: () => Promise<SemanticTable>) => {
    setLoading(true);
    setError(null);
    try {
      const table = await fn();
      onInitialText(text);
      onParsed(table);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <p className="badge">STEP 1 / 3 · 数据输入</p>
      <h2>粘贴文本或上传 CSV / Excel</h2>
      <p className="muted">支持 Markdown 表格 / CSV / xlsx；「未披露 · 无 · —」自动识别为缺失。</p>

      <textarea
        className="input-text"
        rows={8}
        value={text}
        placeholder={'或直接粘贴表格文本…'}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="row-gap">
        <button className="btn" disabled={loading || !text.trim()} onClick={() => void run(() => parseText(text))}>
          {loading ? '解析中…' : '解析数据'}
        </button>
        <button
          className="btn btn-ghost"
          onClick={() => {
            setText(SAMPLE);
            onInitialText(SAMPLE);
          }}
        >
          填入示例
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
          上传文件
        </button>
      </div>

      {error && <p className="error">{error}</p>}
    </section>
  );
}