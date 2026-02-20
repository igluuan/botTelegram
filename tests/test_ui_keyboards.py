from __future__ import annotations

from bot.models import Category, Item
from bot.ui.keyboards import (
    categories_menu,
    item_actions_menu,
    items_menu,
    main_menu,
    paginated_items_menu,
)


def test_main_menu_structure() -> None:
    kb = main_menu()
    assert len(kb.inline_keyboard) == 2
    assert kb.inline_keyboard[0][0].callback_data == "categorias_1"
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "favoritos_1" in callbacks
    assert "recentes_1" in callbacks


def test_categories_menu_no_pagination() -> None:
    cat = Category(id=1, name="Docs", emoji="📁")
    kb = categories_menu([(cat, 0)], page=1, total_pages=1)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "categorias_2" not in callbacks
    assert "categorias_0" not in callbacks
    assert "back_main" in callbacks


def test_categories_menu_with_pagination() -> None:
    cat = Category(id=1, name="Docs", emoji="📁")
    kb = categories_menu([(cat, 0)], page=1, total_pages=2)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "categorias_2" in callbacks
    assert "categorias_0" not in callbacks


def test_categories_menu_back_button() -> None:
    kb = categories_menu([], page=1, total_pages=1)
    assert kb.inline_keyboard[-1][0].callback_data == "back_main"


def test_items_menu_search_button() -> None:
    item = Item(
        id=1,
        category_id=10,
        title="A",
        type="link",
        telegram_message_id=None,
        url="https://example.com",
        description=None,
    )
    kb = items_menu([item], category_id=10, page=1, total_pages=1, back_data="back_categories")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "buscarcat_10" in callbacks


def test_item_actions_menu_with_url() -> None:
    kb = item_actions_menu(item_id=1, is_favorite=False, back_data="back_main", url="https://x")
    assert kb.inline_keyboard[0][0].url == "https://x"


def test_item_actions_menu_no_url() -> None:
    kb = item_actions_menu(item_id=1, is_favorite=False, back_data="back_main", url=None)
    urls = [btn.url for row in kb.inline_keyboard for btn in row]
    assert all(u is None for u in urls)


def test_item_actions_menu_fav_toggle() -> None:
    kb = item_actions_menu(item_id=1, is_favorite=True, back_data="back_main")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "unfav_1" in callbacks


def test_paginated_items_menu_prefix() -> None:
    item = Item(
        id=1,
        category_id=10,
        title="A",
        type="link",
        telegram_message_id=None,
        url="https://example.com",
        description=None,
    )
    kb = paginated_items_menu(
        [item],
        page=2,
        total_pages=3,
        back_data="back_main",
        page_callback_prefix="favoritos",
    )
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "favoritos_1" in callbacks
    assert "favoritos_3" in callbacks
