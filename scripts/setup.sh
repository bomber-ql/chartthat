#!/usr/bin/env bash
# 开发环境依赖安装：后端 Python 依赖 + 前端 pnpm 依赖
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[setup] installing backend dependencies..."
python3 -m pip install -r "$ROOT/backend/requirements.txt" \
  || python3 -m pip install --break-system-packages -r "$ROOT/backend/requirements.txt"

echo "[setup] installing frontend dependencies..."
cd "$ROOT/frontend"
pnpm install

echo "[setup] done."
