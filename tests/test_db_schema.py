from __future__ import annotations

import pytest

from bot import database
from bot.db.connection import connect


@pytest.mark.asyncio
async def test_init_db_creates_tables(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    async with connect(temp_db_path) as conn:
        cur = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in await cur.fetchall()}
    assert {"categories", "items", "favorites", "history"}.issubset(tables)


@pytest.mark.asyncio
async def test_init_db_idempotent(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    await database.init_db(db_path=temp_db_path)


@pytest.mark.asyncio
async def test_init_db_indexes_exist(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    async with connect(temp_db_path) as conn:
        cur = await conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {r[0] for r in await cur.fetchall()}
    assert "idx_items_title" in indexes
    assert "idx_favorites_user_id" in indexes


@pytest.mark.asyncio
async def test_foreign_key_cascade_delete(temp_db_path: str) -> None:
    await database.init_db(db_path=temp_db_path)
    category_id = await database.create_category(
        name="Cascade", emoji="📁", db_path=temp_db_path
    )
    item_id = await database.create_link_item(
        category_id=category_id,
        title="Link",
        url="https://example.com",
        description=None,
        db_path=temp_db_path,
    )

    removed = await database.delete_category(category_id=category_id, db_path=temp_db_path)
    assert removed is True
    assert await database.get_item(item_id=item_id, db_path=temp_db_path) is None
