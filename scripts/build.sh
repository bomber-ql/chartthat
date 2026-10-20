#!/usr/bin/env bash
# 生产构建：后端依赖 + 前端静态产物（frontend/dist）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[build] installing backend dependencies..."
python3 -m pip install -r "$ROOT/backend/requirements.txt" \
  || python3 -m pip install --break-system-packages -r "$ROOT/backend/requirements.txt"

echo "[build] building frontend..."
cd "$ROOT/frontend"
pnpm install
pnpm run build

echo "[build] done."
