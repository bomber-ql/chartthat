// ChartThat 品牌标记：对话气泡 + 上升折线（"Chart that!" 的口语祈使感）。
// 站内使用，随深/浅主题自适应：描边取主题变量，折线固定品牌青蓝渐变。
import { useId } from 'react';

export default function Logo({ size = 34 }: { size?: number }) {
  // 页面存在多个实例（顶栏/hero），渐变 id 必须唯一，否则都引用第一个定义。
  const gid = useId();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      role="img"
      aria-label="ChartThat"
    >
      <defs>
        <linearGradient id={gid} x1="8" y1="34" x2="40" y2="14" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22d3ee" />
          <stop offset="1" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      {/* 对话气泡 */}
      <path
        d="M8 12a4 4 0 0 1 4-4h24a4 4 0 0 1 4 4v18a4 4 0 0 1-4 4H20l-8 7v-7h0a4 4 0 0 1-4-4z"
        fill="var(--accent-bg)"
        stroke="var(--accent-border)"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* 上升折线（数据 -> 图表） */}
      <path
        d="M14 27l7-7 5 4 9-9"
        stroke={`url(#${gid})`}
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="14" cy="27" r="2" fill="#22d3ee" />
      <circle cx="35" cy="15" r="2" fill="#3b82f6" />
    </svg>
  );
}
