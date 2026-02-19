from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers import admin as admin_handlers
from bot.models import Category
from conftest import make_mock_update
from telegram.ext import ConversationHandler


@pytest.mark.asyncio
async def test_admin_panel_rejeita_nao_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_ID", "999")
    update = make_mock_update(user_id=1, text="/admin")
    await admin_handlers.admin_panel(update, MagicMock())
    assert "⛔" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_panel_aceita_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_ID", "1")
    update = make_mock_update(user_id=1, text="/admin")
    await admin_handlers.admin_panel(update, MagicMock())
    assert "Painel Admin" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_add_category_sem_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin_handlers.database, "create_category", AsyncMock())
    update = make_mock_update(user_id=1, text="/addcategoria")
    await admin_handlers.add_category(update, MagicMock())
    assert "Uso" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_add_category_com_emoji(monkeypatch: pytest.MonkeyPatch) -> None:
    create = AsyncMock(return_value=10)
    monkeypatch.setattr(admin_handlers.database, "create_category", create)
    update = make_mock_update(user_id=1, text="/addcategoria 🧪 Teste")
    await admin_handlers.add_category(update, MagicMock())
    create.assert_awaited_once_with(name="Teste", emoji="🧪")


@pytest.mark.asyncio
async def test_add_category_sem_emoji(monkeypatch: pytest.MonkeyPatch) -> None:
    create = AsyncMock(return_value=10)
    monkeypatch.setattr(admin_handlers.database, "create_category", create)
    update = make_mock_update(user_id=1, text="/addcategoria Teste")
    await admin_handlers.add_category(update, MagicMock())
    create.assert_awaited_once_with(name="Teste", emoji="📁")


@pytest.mark.asyncio
async def test_add_link_url_invalida(monkeypatch: pytest.MonkeyPatch) -> None:
    update = make_mock_update(user_id=1, text='/addlink 1 "Titulo" exemplo.com')
    await admin_handlers.add_link(update, MagicMock())
    assert "URL inválida" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_add_link_categoria_inexistente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin_handlers.database, "get_category", AsyncMock(return_value=None))
    update = make_mock_update(
        user_id=1, text='/addlink 1 "Titulo" https://example.com'
    )
    await admin_handlers.add_link(update, MagicMock())
    assert "Categoria não encontrada" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_add_link_sucesso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        admin_handlers.database,
        "get_category",
        AsyncMock(return_value=Category(id=1, name="X", emoji="📁")),
    )
    monkeypatch.setattr(admin_handlers.database, "create_link_item", AsyncMock(return_value=5))
    update = make_mock_update(
        user_id=1, text='/addlink 1 "Titulo" https://example.com "Desc"'
    )
    await admin_handlers.add_link(update, MagicMock())
    assert "✅" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_add_file_step1_args_insuficientes() -> None:
    update = make_mock_update(user_id=1, text="/addfile 1")
    context = MagicMock()
    context.user_data = {}
    result = await admin_handlers.add_file_step1(update, context)
    assert result == ConversationHandler.END
    assert "Uso" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_add_file_step2_sem_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    update = make_mock_update(user_id=1, text="")
    context = MagicMock()
    context.user_data = {}
    result = await admin_handlers.add_file_step2(update, context)
    assert result == ConversationHandler.END
    assert "em andamento" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_item_nao_encontrado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin_handlers.database, "delete_item", AsyncMock(return_value=False))
    update = make_mock_update(user_id=1, text="/deletar 999")
    await admin_handlers.delete_item(update, MagicMock())
    assert "não encontrado" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_category_sucesso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        admin_handlers.database, "delete_category", AsyncMock(return_value=True)
    )
    update = make_mock_update(user_id=1, text="/deletarcategoria 1")
    await admin_handlers.delete_category(update, MagicMock())
    assert "✅" in update.message.reply_text.call_args[0][0]
