import { useState } from 'react';
import { useI18n } from '../i18n';

const SITE = 'https://chartthat.com/';

interface ShareTarget {
  id: string;
  label: string;
  buildUrl: (text: string, url: string) => string;
}

// 各平台官方分享 URL，无需 API key；LinkedIn 只收 url，标题/描述/预览图从 OG 标签抓取
const TARGETS: ShareTarget[] = [
  {
    id: 'x',
    label: 'X',
    buildUrl: (text, url) =>
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
  },
  {
    id: 'linkedin',
    label: 'in',
    buildUrl: (_text, url) =>
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
  },
  {
    id: 'facebook',
    label: 'f',
    buildUrl: (_text, url) =>
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
  },
  {
    id: 'reddit',
    label: 'r/',
    buildUrl: (text, url) =>
      `https://www.reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(text)}`,
  },
];

export default function ShareButtons() {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const text = t('shareText');

  const open = (target: ShareTarget) => {
    const url = `${SITE}?ref=share-${target.id}`;
    window.open(target.buildUrl(text, url), '_blank', 'noopener,noreferrer,width=640,height=560');
  };

  const copy = async () => {
    const url = `${SITE}?ref=share-copy`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // 剪贴板 API 不可用（非安全上下文等）时回退 execCommand
      const ta = document.createElement('textarea');
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="share-row">
      <span className="share-label">{t('shareLabel')}</span>
      <div className="share-btns">
        {TARGETS.map((target) => (
          <button
            key={target.id}
            type="button"
            className="share-btn"
            title={`Share on ${target.id}`}
            onClick={() => open(target)}
          >
            {target.label}
          </button>
        ))}
        <button type="button" className="share-btn share-btn-copy" onClick={copy}>
          {copied ? t('copied') : t('copyLink')}
        </button>
      </div>
    </div>
  );
}
