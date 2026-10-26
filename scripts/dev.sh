#!/usr/bin/env bash
# 开发环境：FastAPI(127.0.0.1:BACKEND_PORT) + Vite(0.0.0.0:DEPLOY_RUN_PORT，代理 /api)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="/app/work/logs/bypass/"
mkdir -p "$LOG_DIR"

BACKEND_PORT="${BACKEND_PORT:-8000}"
export DEPLOY_RUN_PORT="${DEPLOY_RUN_PORT:-5000}"

# 本地开发默认使用沙箱内置 LLM（doubao lite，无需 API key，便于真实联调）；
# 生产部署走 .env（LLM_PROVIDER 缺省 openai + DeepSeek 配置），两者互不影响。
export LLM_PROVIDER="${LLM_PROVIDER:-coze}"
export LLM_MODEL="${LLM_MODEL:-doubao-seed-2-0-lite-260215}"

echo "[dev] starting FastAPI on 127.0.0.1:${BACKEND_PORT}"
cd "$ROOT/backend"
(
  uvicorn app.main:app --host 127.0.0.1 --port "${BACKEND_PORT}" --reload \
    > "$LOG_DIR/app.log" 2>&1
) &

# 等待后端就绪，避免首屏 /api/health 代理失败
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "[dev] starting Vite on 0.0.0.0:${DEPLOY_RUN_PORT}"
cd "$ROOT/frontend"
exec pnpm run dev
