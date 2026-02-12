from __future__ import annotations

import pytest

from bot import database


@pytest.mark.asyncio
async def test_init_and_category_crud(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_id = await database.create_category(name="Docs", emoji="📁", db_path=temp_db_path)
    cats = await database.list_categories(db_path=temp_db_path)
    assert [c.id for c in cats] == [cat_id]
    assert cats[0].name == "Docs"
    assert cats[0].emoji == "📁"
    removed = await database.delete_category(category_id=cat_id, db_path=temp_db_path)
    assert removed is True
    cats2 = await database.list_categories(db_path=temp_db_path)
    assert cats2 == []


@pytest.mark.asyncio
async def test_item_crud_and_search(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    cat_id = await database.create_category(name="Links", emoji="🔗", db_path=temp_db_path)
    link_id = await database.create_link_item(
        category_id=cat_id,
        title="Site Oficial",
        url="https://example.com",
        description="desc",
        db_path=temp_db_path,
    )
    file_id = await database.create_file_item(
        category_id=cat_id,
        title="Manual",
        telegram_message_id=123,
        description=None,
        db_path=temp_db_path,
    )
    items = await database.list_items_by_category(category_id=cat_id, db_path=temp_db_path)
    assert {it.id for it in items} == {link_id, file_id}
    res = await database.search_items(term="Manual", db_path=temp_db_path)
    assert len(res) == 1
    assert res[0].id == file_id
    removed = await database.delete_item(item_id=link_id, db_path=temp_db_path)
    assert removed is True

