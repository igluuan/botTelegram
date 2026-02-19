from __future__ import annotations

import pytest

from bot.config import Settings, get_settings


def test_get_settings_all_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "x")
    monkeypatch.setenv("ADMIN_ID", "10")
    monkeypatch.setenv("STORAGE_CHANNEL_ID", "-100200")
    monkeypatch.setenv("DATABASE_PATH", "my.db")
    monkeypatch.setenv("YOUTUBE_API_KEY", "yk")
    monkeypatch.setenv("YOUTUBE_CHANNEL_ID", "cid")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ak")

    settings = get_settings(strict=True)
    assert isinstance(settings, Settings)
    assert settings.bot_token == "x"
    assert settings.admin_id == 10
    assert settings.storage_channel_id == -100200
    assert settings.database_path == "my.db"
    assert settings.youtube_api_key == "yk"
    assert settings.youtube_channel_id == "cid"
    assert settings.anthropic_api_key == "ak"


def test_get_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    settings = get_settings(strict=False)
    assert settings.database_path == "bot.db"


def test_get_settings_strict_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="BOT_TOKEN"):
        get_settings(strict=True)


def test_get_settings_strict_missing_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ADMIN_ID", raising=False)
    with pytest.raises(RuntimeError, match="ADMIN_ID"):
        get_settings(strict=True)


def test_get_settings_strict_missing_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STORAGE_CHANNEL_ID", raising=False)
    with pytest.raises(RuntimeError, match="STORAGE_CHANNEL_ID"):
        get_settings(strict=True)


def test_get_settings_invalid_admin_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_ID", "abc")
    settings = get_settings(strict=False)
    assert settings.admin_id == 0


def test_get_settings_optional_youtube(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("YOUTUBE_CHANNEL_ID", raising=False)
    settings = get_settings(strict=False)
    assert settings.youtube_api_key is None
    assert settings.youtube_channel_id is None


def test_get_settings_optional_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings = get_settings(strict=False)
    assert settings.anthropic_api_key is None
