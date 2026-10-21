/**
 * M4b 动效产物：离屏 ECharts 绘制动画采帧（SPEC §5.6a/§6a，v1.11 / v1.12）。
 *
 * 在脱离文档流的隐藏容器中 init 一张 ECharts，注入 specToOption(spec, theme)，
 * 利用其原生绘制动画，按固定间隔用 renderToCanvas 截取 PNG dataURL，产出
 * 一组帧序列（≥2 帧）交给后端合成循环 GIF。
 *
 * 背景（v1.12）：
 * - transparent=false（默认）：铺与当前 UI 主题一致的实底色，GIF 播放观感最佳；
 * - transparent=true：画布透明，后端合成二元透明 GIF（抗锯齿边缘会被硬切，
 *   且图表文字随主题配色，仅适合贴到与主题同色的背景）。
 */
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ChartSpec } from '../types';
import type { Theme } from '../theme';
import { specToOption } from './specToOption';

const FRAME_WIDTH = 960;
const FRAME_HEIGHT = 540; // 16:9
const FRAME_INTERVAL_MS = 100; // 与后端默认 frame_ms 一致
const TOTAL_FRAMES = 20; // 总时长 ≈ 1.9s，覆盖 1.5s 绘制动画
const WARMUP_MS = 60; // setOption 后留一拍让首帧上屏

/** 主题对应的实底采帧色（与卡片舞台底色一致，GIF 不支持半透明需铺实底）。 */
const THEME_BG: Record<Theme, string> = {
  dark: '#0d1424',
  light: '#f4f8fc',
};

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * 离屏播放指定图表的绘制动画并截取多帧 PNG dataURL。
 * 失败（容器/实例化异常）时保证清理 DOM 与实例并向上抛出。
 */
export async function captureFrames(
  spec: ChartSpec,
  theme: Theme,
  transparent = false
): Promise<string[]> {
  const holder = document.createElement('div');
  holder.setAttribute('aria-hidden', 'true');
  holder.style.position = 'fixed';
  holder.style.left = '-10000px';
  holder.style.top = '0';
  holder.style.width = `${FRAME_WIDTH}px`;
  holder.style.height = `${FRAME_HEIGHT}px`;
  holder.style.pointerEvents = 'none';
  holder.style.opacity = '0';
  if (!transparent) {
    holder.style.background = THEME_BG[theme];
  }
  document.body.appendChild(holder);

  let chart: echarts.ECharts | null = null;
  try {
    chart = echarts.init(holder, undefined, {
      width: FRAME_WIDTH,
      height: FRAME_HEIGHT,
      devicePixelRatio: 2,
    });
    const baseOption: EChartsOption = specToOption(spec, theme);
    chart.setOption({
      ...baseOption,
      backgroundColor: transparent ? 'transparent' : THEME_BG[theme],
      animationDuration: 1500,
      animationDurationUpdate: 1500,
      animationEasing: 'cubicOut',
    });

    await sleep(WARMUP_MS);

    const frames: string[] = [];
    for (let i = 0; i < TOTAL_FRAMES; i += 1) {
      const canvas = chart.renderToCanvas({
        backgroundColor: transparent ? 'transparent' : THEME_BG[theme],
        pixelRatio: 2,
      });
      frames.push(canvas.toDataURL('image/png'));
      await sleep(FRAME_INTERVAL_MS);
    }
    return frames;
  } finally {
    chart?.dispose();
    holder.remove();
  }
}
