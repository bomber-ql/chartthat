import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

// dev 形态：Vite 监听对外端口（DEPLOY_RUN_PORT，主仓为 5000），
// /api 代理到同机 FastAPI（BACKEND_PORT，默认 8000）。
// prod 形态：不启动 Vite，由 FastAPI 直接监听 DEPLOY_RUN_PORT 并托管 dist。
const backendPort = process.env.BACKEND_PORT ?? '8000';

export default defineConfig({
  plugins: [react()],
  build: {
    // echarts 全量引入体积较大，属预期；提高告警阈值避免误报。
    chunkSizeWarningLimit: 2048,
    rollupOptions: {
      // 多页构建：主应用 SPA + 独立静态页（SEO / AdSense 审核，不依赖客户端渲染）
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        about: fileURLToPath(new URL('./about.html', import.meta.url)),
        privacy: fileURLToPath(new URL('./privacy.html', import.meta.url)),
        // Guides 文章页（Charts That Sell 系列）
        guidesIndex: fileURLToPath(new URL('./guides/index.html', import.meta.url)),
        guideChooseChart: fileURLToPath(
          new URL('./guides/choose-chart-by-conclusion.html', import.meta.url),
        ),
        guideOneSlide: fileURLToPath(
          new URL('./guides/one-slide-one-claim.html', import.meta.url),
        ),
        guideSevenEdits: fileURLToPath(
          new URL('./guides/seven-edits-after-double-click.html', import.meta.url),
        ),
        guideColors: fileURLToPath(new URL('./guides/colors-that-sell.html', import.meta.url)),
        guideCleanup: fileURLToPath(
          new URL('./guides/friday-night-data-cleanup.html', import.meta.url),
        ),
        guideMissing: fileURLToPath(
          new URL('./guides/never-replace-missing-with-zero.html', import.meta.url),
        ),
        guidePyramid: fileURLToPath(
          new URL('./guides/answer-first-pyramid-principle.html', import.meta.url),
        ),
        guideScqa: fileURLToPath(new URL('./guides/scqa-four-beats.html', import.meta.url)),
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: Number(process.env.DEPLOY_RUN_PORT ?? 5000),
    strictPort: true,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
      },
    },
  },
});
