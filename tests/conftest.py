from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def _set_env_defaults(monkeypatch: pytest.MonkeyPatch, temp_db_path: str) -> None:
    monkeypatch.setenv("DATABASE_PATH", temp_db_path)
    monkeypatch.setenv("ADMIN_ID", "1")
    monkeypatch.setenv("STORAGE_CHANNEL_ID", "-1001")
    monkeypatch.setenv("BOT_TOKEN", "test-token")


def make_mock_update(
    *,
    user_id: int = 1,
    text: str = "",
    callback_data: str | None = None,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id

    message = MagicMock(spec=Message)
    message.text = text
    message.reply_text = AsyncMock()
    message.chat_id = 100
    message.message_id = 1

    chat = MagicMock(spec=Chat)
    chat.id = 100

    update = MagicMock(spec=Update)
    update.effective_user = user
    update.effective_chat = chat
    update.message = message
    update.callback_query = None

    if callback_data is not None:
        cq = MagicMock(spec=CallbackQuery)
        cq.data = callback_data
        cq.answer = AsyncMock()
        cq.edit_message_text = AsyncMock()
        cq.message = message
        update.callback_query = cq
        update.message = None

    return update
