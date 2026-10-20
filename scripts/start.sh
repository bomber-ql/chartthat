#!/usr/bin/env bash
# 生产运行：FastAPI 直接监听 DEPLOY_RUN_PORT，并托管 frontend/dist（SPA）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DEPLOY_RUN_PORT="${DEPLOY_RUN_PORT:-5000}"

cd "$ROOT/backend"
exec uvicorn app.main:app --host 0.0.0.0 --port "${DEPLOY_RUN_PORT}"
