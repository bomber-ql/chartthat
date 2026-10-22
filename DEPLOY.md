# DEPLOY.md — chartthat.com 生产部署手册

目标：**一台 VPS + 一条命令**跑起全栈（前端 + FastAPI + 自动 HTTPS）。
架构：`Cloudflare(DNS/CDN) → Caddy(HTTPS/反代) → app(FastAPI 托管 frontend/dist)`，全部跑在单个 Docker Compose 里，无状态。

---

## 0. 前置条件

| 项 | 说明 |
|---|---|
| VPS | Hetzner Cloud（建议 US East / Ashburn），最低配 CX22（2 vCPU / 4G）足够；Ubuntu 24.04 LTS |
| 域名 | chartthat.com，NS 已托管到 Cloudflare |
| LLM Key | https://platform.deepseek.com → API Keys 创建（可选；不配则走启发式降级引擎） |
| 本地 | 能 SSH 到 VPS；代码已推到 GitHub 私有仓 |

## 1. Cloudflare DNS（先做，证书签发依赖解析生效）

在 Cloudflare → DNS → Records 添加两条 A 记录（`<VPS_IP>` 换成实际 IP）：

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `@` | `<VPS_IP>` | 开启（橙云） |
| A | `www` | `<VPS_IP>` | 开启（橙云） |

SSL/TLS → Overview：加密模式设为 **Full (strict)**（Caddy 会签有效证书，源站不是裸 HTTP）。

> Caddy 用 HTTP-01/TLS-ALPN 挑战签 Let's Encrypt 证书，Cloudflare 橙云代理会正常转发 80/443 的挑战请求，无需额外配置。

## 2. VPS 初始化（只需一次）

```bash
ssh root@<VPS_IP>

# 1) 安装 Docker（官方一键脚本）
curl -fsSL https://get.docker.com | sh

# 2) 防火墙：只放行 SSH/HTTP/HTTPS
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

# 3) 拉代码（HTTPS 或配 deploy key）
git clone <你的仓库地址> /opt/chartthat
cd /opt/chartthat

# 4) 配置环境变量
cp .env.example .env
nano .env          # 填入 LLM_API_KEY（DeepSeek）
```

## 3. 启动

```bash
cd /opt/chartthat
docker compose up -d --build
docker compose ps          # app / caddy 均应为 running
docker compose logs -f app # 看启动日志，Ctrl+C 退出
```

首次启动 Caddy 会自动申请证书（约 30 秒）。验证：

```bash
curl -s https://chartthat.com/healthz        # {"status":"ok"}
curl -s https://chartthat.com/api/health     # {"status":"ok"}
```

浏览器打开 `https://chartthat.com` 即上线完成。

## 4. 日常更新

```bash
cd /opt/chartthat
git pull
docker compose up -d --build   # 只重建有变更的镜像层
```

## 5. 运维速查

| 操作 | 命令 |
|---|---|
| 看日志 | `docker compose logs -f app` / `... caddy` |
| 重启 | `docker compose restart app` |
| 改配置后重载 Caddy | `docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile` |
| 进容器排查 | `docker compose exec app sh` |
| 磁盘清理 | `docker system prune -f`（每月一次，清旧镜像层） |

**备份**：本阶段无数据库，代码在 GitHub、密钥在 `.env`（另行离线保存）。在 Hetzner 控制台开启 **自动快照**（+20% 费用）即可兜底；后续加了 Postgres 再补 `pg_dump` 定时任务。

**监控**：UptimeRobot 免费档添加监控 `https://chartthat.com/healthz`，宕机邮件提醒。

## 6. 环境变量清单（.env）

| 变量 | 必填 | 说明 |
|---|---|---|
| `LLM_API_KEY` | 否 | DeepSeek API Key；为空时推荐走启发式降级引擎（零成本） |
| `LLM_BASE_URL` | 否 | 默认 `https://api.deepseek.com` |
| `LLM_MODEL` | 否 | 默认 `deepseek-chat` |
| `CORS_ORIGINS` | 否 | 默认本域名双记录 |

## 7. 常见坑

- **502 Bad Gateway**：`docker compose logs app` 看 app 是否起来；多半是首次构建未完或 `.env` 语法错误（值不要加引号、不要有多余空格）。
- **证书一直签不下来**：确认 DNS 已生效（`dig chartthat.com +short` 返回 VPS IP 或 CF 边缘 IP）、防火墙 80/443 已放行；`docker compose logs caddy` 看挑战细节。
- **换域名**：改 `deploy/Caddyfile` 里的域名 + Cloudflare DNS，重启 compose 即可，Caddy 自动签新证书。
- **DeepSeek 不生效**：`docker compose exec app env | grep LLM_` 确认变量注入；LLM 故障会自动降级为启发式推荐（`degraded=true`），不影响出图。
