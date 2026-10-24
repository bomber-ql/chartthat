// 内容区图型速查卡的迷你演示：真实 ECharts 渲染 + 内置固定 demo 数据（不走生成管线）。
// 迷你模式隐藏坐标轴/图例/标签/交互，只保留图形形态；入场播一次绘制动画，hover 重播。

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ChartType } from '../types';
import { useTheme } from '../theme';
import { DEMO_SPECS, miniOption } from '../utils/chartMiniData';

export default function ChartMini({ type }: { type: ChartType }) {
  const { theme } = useTheme();
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const optionRef = useRef<EChartsOption | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const option = miniOption(DEMO_SPECS[type], theme);
    chart.setOption(option);
    chartRef.current = chart;
    optionRef.current = option;
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
      chartRef.current = null;
    };
  }, [type, theme]);

  const replay = () => {
    const chart = chartRef.current;
    const option = optionRef.current;
    if (!chart || !option) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    chart.clear();
    chart.setOption(option, true);
  };

  return <div className="cg-demo" ref={ref} onMouseEnter={replay} />;
}
