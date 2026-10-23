"""应用配置：所有运行时信息从环境变量读取，禁止硬编码密钥。"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if raw == "*" or not raw:
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    cors_origins: tuple[str, ...] = tuple(_cors_origins())
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    # 使用统计埋点（SPEC v1.19 §7.1）：STATS_TOKEN 未配置则 /api/stats 恒 404
    stats_token: str = os.getenv("STATS_TOKEN", "")

    # 上传与解析限制（SPEC §M1）
    max_upload_bytes: int = 10 * 1024 * 1024
    max_data_rows: int = 10_000


settings = Settings()
