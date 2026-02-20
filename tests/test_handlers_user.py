from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers import user as user_handlers
from bot.models import Category, Item
from conftest import make_mock_update


@pytest.mark.asyncio
async def test_show_main_menu_message() -> None:
    update = make_mock_update(user_id=1, text="/start")
    await user_handlers.show_main_menu(update, MagicMock())
    assert update.message.reply_text.await_count == 1
    assert "Bem-vindo" in update.message.reply_text.call_args[0][0]
    assert "reply_markup" in update.message.reply_text.call_args.kwargs


@pytest.mark.asyncio
async def test_show_main_menu_callback() -> None:
    update = make_mock_update(user_id=1, callback_data="back_main")
    await user_handlers.show_main_menu(update, MagicMock())
    assert update.callback_query.edit_message_text.await_count == 1


@pytest.mark.asyncio
async def test_show_categories_vazio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_handlers.database, "count_categories", AsyncMock(return_value=0))
    monkeypatch.setattr(
        user_handlers.database, "list_categories_with_counts_paged", AsyncMock(return_value=[])
    )
    update = make_mock_update(user_id=1, callback_data="categorias_1")
    await user_handlers.show_categories(update, MagicMock())
    args = update.callback_query.edit_message_text.call_args[0]
    assert "Ainda não há categorias" in args[0]


@pytest.mark.asyncio
async def test_show_items_categoria_inexistente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_handlers.database, "get_category", AsyncMock(return_value=None))
    update = make_mock_update(user_id=1, callback_data="cat_999_1")
    await user_handlers.show_items(update, MagicMock())
    assert "Categoria não encontrada" in update.callback_query.edit_message_text.call_args[0][0]


@pytest.mark.asyncio
async def test_send_item_link(monkeypatch: pytest.MonkeyPatch) -> None:
    item = Item(
        id=1,
        category_id=10,
        title="Site",
        type="link",
        telegram_message_id=None,
        url="https://example.com",
        description="Desc",
    )
    monkeypatch.setattr(user_handlers.database, "get_item", AsyncMock(return_value=item))
    monkeypatch.setattr(user_handlers.database, "add_history_entry", AsyncMock())
    monkeypatch.setattr(user_handlers.database, "is_favorite", AsyncMock(return_value=False))

    update = make_mock_update(user_id=1, callback_data="item_1")
    context = MagicMock()
    context.user_data = {"last_back_data": "back_main"}
    await user_handlers.send_item(update, context)
    assert update.callback_query.edit_message_text.await_count == 1
    kwargs = update.callback_query.edit_message_text.call_args.kwargs
    assert kwargs.get("disable_web_page_preview") is True


@pytest.mark.asyncio
async def test_send_item_file_sem_message_id(monkeypatch: pytest.MonkeyPatch) -> None:
    item = Item(
        id=1,
        category_id=10,
        title="Arquivo",
        type="file",
        telegram_message_id=None,
        url=None,
        description=None,
    )
    monkeypatch.setattr(user_handlers.database, "get_item", AsyncMock(return_value=item))
    monkeypatch.setattr(user_handlers.database, "add_history_entry", AsyncMock())
    monkeypatch.setattr(user_handlers.database, "is_favorite", AsyncMock(return_value=False))
    update = make_mock_update(user_id=1, callback_data="item_1")
    context = MagicMock()
    context.user_data = {"last_back_data": "back_main"}
    await user_handlers.send_item(update, context)
    assert "Arquivo indisponível" in update.callback_query.edit_message_text.call_args[0][0]


@pytest.mark.asyncio
async def test_send_item_adiciona_historico(monkeypatch: pytest.MonkeyPatch) -> None:
    item = Item(
        id=1,
        category_id=10,
        title="Site",
        type="link",
        telegram_message_id=None,
        url="https://example.com",
        description=None,
    )
    add_history = AsyncMock()
    monkeypatch.setattr(user_handlers.database, "get_item", AsyncMock(return_value=item))
    monkeypatch.setattr(user_handlers.database, "add_history_entry", add_history)
    monkeypatch.setattr(user_handlers.database, "is_favorite", AsyncMock(return_value=False))
    update = make_mock_update(user_id=123, callback_data="item_1")
    context = MagicMock()
    context.user_data = {"last_back_data": "back_main"}
    await user_handlers.send_item(update, context)
    add_history.assert_awaited()


@pytest.mark.asyncio
async def test_toggle_favorite_adiciona(monkeypatch: pytest.MonkeyPatch) -> None:
    item = Item(
        id=1,
        category_id=10,
        title="Site",
        type="link",
        telegram_message_id=None,
        url="https://example.com",
        description=None,
    )
    add_fav = AsyncMock()
    monkeypatch.setattr(user_handlers.database, "add_favorite", add_fav)
    monkeypatch.setattr(user_handlers.database, "get_item", AsyncMock(return_value=item))
    monkeypatch.setattr(user_handlers.database, "is_favorite", AsyncMock(return_value=True))

    update = make_mock_update(user_id=1, callback_data="fav_1")
    context = MagicMock()
    context.user_data = {"last_back_data": "back_main"}
    await user_handlers.toggle_favorite(update, context)
    add_fav.assert_awaited()
    assert update.callback_query.edit_message_text.await_count == 1


@pytest.mark.asyncio
async def test_toggle_favorite_remove(monkeypatch: pytest.MonkeyPatch) -> None:
    item = Item(
        id=1,
        category_id=10,
        title="Site",
        type="link",
        telegram_message_id=None,
        url="https://example.com",
        description=None,
    )
    remove_fav = AsyncMock()
    monkeypatch.setattr(user_handlers.database, "remove_favorite", remove_fav)
    monkeypatch.setattr(user_handlers.database, "get_item", AsyncMock(return_value=item))
    monkeypatch.setattr(user_handlers.database, "is_favorite", AsyncMock(return_value=False))

    update = make_mock_update(user_id=1, callback_data="unfav_1")
    context = MagicMock()
    context.user_data = {"last_back_data": "back_main"}
    await user_handlers.toggle_favorite(update, context)
    remove_fav.assert_awaited()
    assert update.callback_query.edit_message_text.await_count == 1


@pytest.mark.asyncio
async def test_search_sem_termo() -> None:
    update = make_mock_update(user_id=1, text="/buscar")
    context = MagicMock()
    context.args = []
    context.user_data = {}
    await user_handlers.search(update, context)
    assert "Uso" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_search_com_resultado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_handlers.database, "count_search_items", AsyncMock(return_value=1))
    monkeypatch.setattr(
        user_handlers.database,
        "search_items",
        AsyncMock(
            return_value=[
                Item(
                    id=1,
                    category_id=1,
                    title="Manual",
                    type="file",
                    telegram_message_id=10,
                    url=None,
                    description=None,
                )
            ]
        ),
    )

    update = make_mock_update(user_id=1, text="/buscar Manual")
    msg = MagicMock()
    msg.edit_text = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=msg)
    context = MagicMock()
    context.args = ["Manual"]
    context.user_data = {}
    await user_handlers.search(update, context)
    assert msg.edit_text.await_count == 1
    assert "Manual" in msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_search_sem_resultado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_handlers.database, "count_search_items", AsyncMock(return_value=0))
    monkeypatch.setattr(user_handlers.database, "search_items", AsyncMock(return_value=[]))
    update = make_mock_update(user_id=1, text="/buscar XXX")
    msg = MagicMock()
    msg.edit_text = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=msg)
    context = MagicMock()
    context.args = ["XXX"]
    context.user_data = {}
    await user_handlers.search(update, context)
    assert "Nenhum resultado" in msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_search_by_category_categoria_inexistente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_handlers.database, "get_category", AsyncMock(return_value=None))
    update = make_mock_update(user_id=1, text="/buscarcat 1 termo")
    context = MagicMock()
    context.args = ["1", "termo"]
    context.user_data = {}
    await user_handlers.search_by_category_command(update, context)
    assert "Categoria não encontrada" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_start_category_search_categoria_invalida(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(user_handlers.database, "get_category", AsyncMock(return_value=None))
    update = make_mock_update(user_id=1, callback_data="buscarcat_999")
    context = MagicMock()
    context.user_data = {}
    result = await user_handlers.start_category_search(update, context)
    assert result == user_handlers.ConversationHandler.END


@pytest.mark.asyncio
async def test_handle_pending_category_search_sem_termo(monkeypatch: pytest.MonkeyPatch) -> None:
    update = make_mock_update(user_id=1, text="   ")
    context = MagicMock()
    context.user_data = {"pending_category_search_id": 1, "pending_category_search_name": "X"}
    result = await user_handlers.handle_pending_category_search(update, context)
    assert result == user_handlers.WAITING_SEARCH_TERM
