/** 动效版导出的离屏采帧工具（SPEC §5.6a/§6a，v1.11，R-6）。
 *
 * 创建隐藏容器初始化离屏 ECharts，播放绘制动画的同时以固定帧间隔采样
 * canvas.toDataURL('image/png')，得到上传给 /api/generate-animated-pptx 的帧序列。
 */
import * as echarts from 'echarts';
import type { ChartSpec } from '../types';
import type { Theme } from '../theme';
import { specToOption } from './specToOption';

export interface CaptureResult {
  frames: string[];
  frameMs: number;
}

export interface CaptureOptions {
  /** 帧间隔（GIF duration），默认 100ms */
  frameMs?: number;
  /** 总采样时长，需覆盖绘制动画周期（specToOption 动画 1500ms + 渐进延迟），默认 1900ms */
  durationMs?: number;
  /** 离屏画布尺寸（CSS px；devicePixelRatio=2 输出 2 倍像素保证清晰度） */
  width?: number;
  height?: number;
}

/** 采帧底色：ECharts canvas 默认透明，GIF 不支持半透明（透明区会被填黑），
 * 必须按当前主题铺实底（与 styles.css 的 --stage-bg 深色/浅色取值一致）。 */
const STAGE_BG: Record<Theme, string> = {
  dark: '#0d1424',
  light: '#f4f8fc',
};

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export async function captureChartFrames(
  spec: ChartSpec,
  theme: Theme,
  options: CaptureOptions = {},
): Promise<CaptureResult> {
  const { frameMs = 100, durationMs = 1900, width = 960, height = 600 } = options;

  const host = document.createElement('div');
  host.style.cssText =
    `position:fixed;left:-10000px;top:0;width:${width}px;height:${height}px;` +
    'pointer-events:none;visibility:hidden;';
  document.body.appendChild(host);

  const chart = echarts.init(host, undefined, { devicePixelRatio: 2, renderer: 'canvas' });
  try {
    const option = specToOption(spec, theme);
    option.backgroundColor = STAGE_BG[theme];
    chart.setOption(option);

    const frames: string[] = [];
    const totalFrames = Math.max(2, Math.round(durationMs / frameMs) + 1);
    for (let i = 0; i < totalFrames; i += 1) {
      frames.push(chart.renderToCanvas().toDataURL('image/png'));
      if (i < totalFrames - 1) await sleep(frameMs);
    }
    return { frames, frameMs };
  } finally {
    chart.dispose();
    host.remove();
  }
}
