from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def _set_env_defaults(monkeypatch: pytest.MonkeyPatch, temp_db_path: str) -> None:
    monkeypatch.setenv("DATABASE_PATH", temp_db_path)
    monkeypatch.setenv("ADMIN_ID", "1")
    monkeypatch.setenv("STORAGE_CHANNEL_ID", "-1001")
    monkeypatch.setenv("BOT_TOKEN", "test-token")

