from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_id: int
    storage_channel_id: int
    database_path: str


load_dotenv()


def _get_int_env(name: str, default: str | None = None) -> int | None:
    raw = os.getenv(name, default)
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def get_settings(*, strict: bool = False) -> Settings:
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = _get_int_env("ADMIN_ID")
    storage_channel_id = _get_int_env("STORAGE_CHANNEL_ID")
    database_path = os.getenv("DATABASE_PATH", "bot.db")

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
    )

