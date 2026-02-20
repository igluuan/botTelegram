from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_id: int
    storage_channel_id: int
    database_path: str
    youtube_api_key: str | None = None
    youtube_channel_id: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None


load_dotenv()


def _get_int_env(name: str, default: str | None = None) -> int | None:
    raw = os.getenv(name, default)
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Variável de ambiente %s=%r não é um inteiro válido.", name, raw)
        return None


def get_settings(*, strict: bool = True) -> Settings:
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = _get_int_env("ADMIN_ID")
    storage_channel_id = _get_int_env("STORAGE_CHANNEL_ID")
    database_path = os.getenv("DATABASE_PATH", "bot.db")
    youtube_api_key = os.getenv("YOUTUBE_API_KEY") or None
    youtube_channel_id = os.getenv("YOUTUBE_CHANNEL_ID") or None
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or None
    anthropic_model = os.getenv("ANTHROPIC_MODEL") or "claude-3-haiku-20240307"

    if strict:
        missing = []
        if not bot_token:
            missing.append("BOT_TOKEN")
        if admin_id is None:
            missing.append("ADMIN_ID")
        if storage_channel_id is None:
            missing.append("STORAGE_CHANNEL_ID")
        if missing:
            raise RuntimeError(
                "Variáveis de ambiente ausentes/invalidas: " + ", ".join(missing)
            )

    return Settings(
        bot_token=bot_token or "",
        admin_id=admin_id or 0,
        storage_channel_id=storage_channel_id or 0,
        database_path=database_path,
        youtube_api_key=youtube_api_key,
        youtube_channel_id=youtube_channel_id,
        anthropic_api_key=anthropic_api_key,
        anthropic_model=anthropic_model,
    )

