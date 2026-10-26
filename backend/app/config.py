"""应用配置：所有运行时信息从环境变量读取，禁止硬编码密钥。"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _cors_origins() -> list[str]:
    # 生产为同源部署（Caddy 反代前端与 /api），同源请求不触发 CORS，
    # 故默认不放行任何跨域来源；需要跨域时由 CORS_ORIGINS 显式配置白名单。
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    # LLM provider：openai=OpenAI 兼容 HTTP（默认，生产 DeepSeek）；
    # coze=开发沙箱内置 LLM SDK（仅开发环境可用，生产镜像无此依赖，勿在生产开启）
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    cors_origins: tuple[str, ...] = tuple(_cors_origins())
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    # 使用统计埋点（SPEC v1.19 §7.1）：STATS_TOKEN 未配置则 /api/stats 恒 404
    stats_token: str = os.getenv("STATS_TOKEN", "")

    # 上传与解析限制（SPEC §M1）
    max_upload_bytes: int = 10 * 1024 * 1024
    max_data_rows: int = 10_000

    # 安全防护（SPEC v1.24 §7.2）
    # 速率限制默认开启；测试置 RATE_LIMIT_ENABLED=false 关闭。
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in ("0", "false", "no")
    # POST/PUT 请求体硬上限（GIF 帧约 20×2x DPR PNG base64，15MB 充裕）。
    max_request_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", str(15 * 1024 * 1024)))


settings = Settings()
