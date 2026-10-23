# ChartThat

> **Data in, charts out.** / 数据给我，图表给你。

Paste text, CSV or Excel data — get presentation-ready charts recommended by AI, previewed live in the browser, and exported as **native editable PowerPoint charts** (.pptx) or **animated GIFs**.

🌐 **https://chartthat.com**

[English](#english) · [中文指南](#中文指南)

---

<a id="english"></a>

## Features

- **13 chart types** — bar, horizontal bar, line, area, combo (bar + rate line), stacked, slope, scatter, waterfall, radar, pie, donut, sunburst
- **Native editable PPTX** — charts are real PowerPoint chart objects (double-click to edit in PowerPoint / WPS), never screenshots
- **Animated GIF export** — captures the draw animation frame-by-frame; solid or transparent background
- **AI recommendations** — an LLM reads your table semantics (trend / comparison / rate) and picks the right charts; falls back to a built-in heuristic engine when no API key is configured, so the app works 100% offline
- **6 UI languages** — 中文 / English / Français / Deutsch / Español, auto-detected from the browser; chart titles & reasoning are generated natively in 5 languages
- **Dark / light themes**, responsive down to mobile
- **Data-labels toggle** — reflected in preview, GIF and PPTX exports

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | React 18 · TypeScript · Vite 5 · ECharts 5 |
| Backend | FastAPI (Python 3.12) · python-pptx · ablechart · Pillow |
| Deploy | Docker (multi-stage) · docker-compose · Caddy (auto HTTPS) |

## Quick Start (local development)

Prerequisites: **Node.js 20+** with `pnpm`, **Python 3.12**.

```bash
git clone https://github.com/bomber-ql/chartthat.git
cd chartthat

bash scripts/setup.sh   # install backend + frontend dependencies
bash scripts/dev.sh     # start dev: frontend on :5000, backend on :8000 (auto-proxied /api)
```

Open http://localhost:5000 — click **Load sample** → **Generate charts**.

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_API_KEY` | No | _(empty)_ | DeepSeek (or any OpenAI-compatible) API key. **Leave empty to use the free heuristic engine.** |
| `LLM_BASE_URL` | No | `https://api.deepseek.com` | OpenAI-compatible endpoint |
| `LLM_MODEL` | No | `deepseek-chat` | Model name |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins; set to your domain in production |
| `DEPLOY_RUN_PORT` | No | `5000` (dev) / `8000` (docker) | Port the server listens on |

## Deploy to production (Docker, one command)

The repo ships a single-container full-stack image (frontend build + FastAPI serving it) plus an optional Caddy sidecar that obtains and renews HTTPS certificates automatically.

**1. Get a server** — any Linux VPS with a public IP (≥1 vCPU / 2 GB RAM, Ubuntu 22.04/24.04 recommended). Point your domain's **A record** to the server IP.

**2. One-time server setup** (SSH in as root):

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Firewall: SSH + HTTP + HTTPS only
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

# Pull the code
git clone https://github.com/bomber-ql/chartthat.git /opt/chartthat
cd /opt/chartthat

# Configure
cp .env.example .env
nano .env        # paste your LLM_API_KEY (optional), set CORS_ORIGINS to your domain
```

**3. Launch:**

```bash
docker compose up -d --build
docker compose ps            # app + caddy should both be "running"
docker compose logs -f app   # Ctrl+C to detach
```

First boot takes ~30 s while Caddy issues the Let's Encrypt certificate. Then visit `https://<your-domain>`.

> **Note:** edit `deploy/Caddyfile` first and replace `chartthat.com` with your own domain.

**4. Update later:**

```bash
cd /opt/chartthat
git pull && docker compose up -d --build
```

**5. Verify health:** `curl https://<your-domain>/healthz` → `{"status":"ok"}`

For a full walkthrough (Hetzner + Cloudflare, firewall, backups, troubleshooting) see **[DEPLOY.md](DEPLOY.md)**.

## Scripts

| Command | Purpose |
|---|---|
| `bash scripts/setup.sh` | Install all dependencies (backend + frontend) |
| `bash scripts/dev.sh` | Local development with hot reload |
| `bash scripts/build.sh` | Production build (`frontend/dist`) |
| `bash scripts/start.sh` | Run production server locally |
| `python3 scripts/smoke_pptx_export.py` | Smoke-test PPTX export for all 13 chart types |

## Testing

```bash
cd backend && python3 -m pytest   # 104 tests: parser / semantic / recommender / pptx / gif
```

## Project Structure

```
frontend/          React + Vite app (src/components, src/utils/specToOption.ts …)
backend/           FastAPI app
  app/modules/     parser → semantic → recommender → pptx_builder / gif_builder
  tests/           pytest suite (no network, LLM always mocked)
scripts/           setup / dev / build / start helpers
deploy/Caddyfile   HTTPS reverse proxy config
Dockerfile         Multi-stage: Node build → python:3.12-slim runtime
docker-compose.yml app + caddy
```

## Documentation

| File | Contents |
|---|---|
| [SPEC.md](SPEC.md) | The single source of truth: contracts, constraints, chart mappings |
| [DEPLOY.md](DEPLOY.md) | Step-by-step production deployment handbook |
| [AGENTS.md](AGENTS.md) | Architecture & conventions for contributors |
| [DESIGN.md](DESIGN.md) | Brand, design tokens, i18n wording rules |

---

<a id="中文指南"></a>

# 中文指南

## 这是什么

把文本 / CSV / Excel 数据粘贴进来，AI 自动推荐图表，浏览器里实时预览，一键导出**原生可编辑的 PPT 图表**（.pptx，双击还能改数据）或**动效 GIF**。支持 13 种图型、六语言界面、深浅双主题。不配任何 API Key 也能用（自动走内置启发式引擎）。

## 本地开发

环境要求：**Node.js 20+**（含 pnpm）、**Python 3.12**。

```bash
git clone https://github.com/bomber-ql/chartthat.git
cd chartthat
bash scripts/setup.sh   # 安装后端 + 前端依赖
bash scripts/dev.sh     # 启动开发服务：前端 :5000，后端 :8000（/api 自动代理）
```

浏览器打开 http://localhost:5000 ，点「一键示例」→「生成图表」即可体验。

## 配置项（.env）

```bash
cp .env.example .env
```

| 变量 | 必填 | 说明 |
|---|---|---|
| `LLM_API_KEY` | 否 | DeepSeek API Key（https://platform.deepseek.com → API Keys 申请）。**留空则免费走启发式引擎** |
| `LLM_BASE_URL` | 否 | 默认 `https://api.deepseek.com`，可换任何 OpenAI 兼容端点 |
| `LLM_MODEL` | 否 | 默认 `deepseek-chat` |
| `CORS_ORIGINS` | 否 | 生产环境改成自己的域名，如 `https://chartthat.com,https://www.chartthat.com` |

## 服务器部署（从零开始，照抄即可）

适用任何一台有公网 IP 的 Linux VPS（1 vCPU / 2G 内存起步，Ubuntu 22.04/24.04）。

**第 0 步：域名解析** —— 在 DNS 服务商处加 A 记录：`@` 和 `www` 都指向服务器 IP。

**第 1 步：服务器初始化**（SSH 登录后执行，只需一次）：

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 防火墙只放行 SSH/HTTP/HTTPS
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

# 拉取代码
git clone https://github.com/bomber-ql/chartthat.git /opt/chartthat
cd /opt/chartthat

# 改域名：把 deploy/Caddyfile 里的 chartthat.com 全部替换成你的域名
nano deploy/Caddyfile

# 配置环境变量
cp .env.example .env
nano .env        # 填 LLM_API_KEY（可选），CORS_ORIGINS 改成你的域名
```

**第 2 步：启动**

```bash
docker compose up -d --build
docker compose ps            # app 和 caddy 都应是 running
docker compose logs -f app   # 查看日志，Ctrl+C 退出
```

首次启动 Caddy 自动申请 HTTPS 证书（约 30 秒），然后访问 `https://你的域名`。

**第 3 步：验证**

```bash
curl https://你的域名/healthz     # 应返回 {"status":"ok"}
```

**以后更新代码：**

```bash
cd /opt/chartthat && git pull && docker compose up -d --build
```

**常见问题：**

- 证书没签下来 → 检查 DNS A 记录是否生效（`ping 你的域名` 应解析到服务器 IP）、80/443 端口是否放行
- 页面能开但图表推荐很"笨" → 没配 `LLM_API_KEY`，当前走的是启发式引擎，配上 DeepSeek Key 重启即可
- 想看实时日志 → `docker compose logs -f app` 或 `docker compose logs -f caddy`

更完整的运维手册（Cloudflare 接入、备份、故障排查）见 **[DEPLOY.md](DEPLOY.md)**。
