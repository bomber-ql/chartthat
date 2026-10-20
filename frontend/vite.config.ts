import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// dev 形态：Vite 监听对外端口（DEPLOY_RUN_PORT，主仓为 5000），
// /api 代理到同机 FastAPI（BACKEND_PORT，默认 8000）。
// prod 形态：不启动 Vite，由 FastAPI 直接监听 DEPLOY_RUN_PORT 并托管 dist。
const backendPort = process.env.BACKEND_PORT ?? '8000';

export default defineConfig({
  plugins: [react()],
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
