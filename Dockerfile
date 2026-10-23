# syntax=docker/dockerfile:1
# 单容器全栈镜像：前端 Vite 构建 + 后端 FastAPI 托管静态产物。
# 生产启动与 scripts/start.sh 等价：uvicorn 监听 ${DEPLOY_RUN_PORT}（容器内固定 8000）。

# ---- Stage 1: 前端构建 ----
FROM node:20-alpine AS frontend
# 显式安装 pnpm（版本与 pnpm-lock.yaml lockfileVersion 9 对齐）：
# 不用 corepack 自动解析——旧镜像内置签名 key 过期会导致 pnpm 下载校验失败
RUN npm install -g pnpm@9.15.9 && pnpm --version
WORKDIR /app/frontend
# 依赖层单独拷贝，命中 Docker 缓存
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm run build

# ---- Stage 2: Python 运行时 ----
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEPLOY_RUN_PORT=8000 \
    DATA_DIR=/app/data

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
# main.py 的 FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"（即 /app/frontend/dist）
COPY --from=frontend /app/frontend/dist frontend/dist

WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request,os;urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['DEPLOY_RUN_PORT']}/healthz\",timeout=3)"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${DEPLOY_RUN_PORT}"]
