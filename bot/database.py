from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import aiosqlite

from bot.config import get_settings
from bot.models import Category, Item


@asynccontextmanager
async def _connect(db_path: str) -> AsyncIterator[aiosqlite.Connection]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        yield conn


async def init_db(*, db_path: str | None = None) -> None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        await conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT DEFAULT '📁',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('file', 'link')),
                telegram_message_id INTEGER,
                url TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_items_category_id ON items(category_id);
            CREATE INDEX IF NOT EXISTS idx_items_title ON items(title);
            """
        )
        await conn.commit()


async def create_category(
    *, name: str, emoji: str = "📁", db_path: str | None = None
) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "INSERT INTO categories(name, emoji) VALUES (?, ?)",
            (name.strip(), emoji.strip() or "📁"),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def list_categories(*, db_path: str | None = None) -> list[Category]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories ORDER BY name COLLATE NOCASE"
        )
        rows = await cur.fetchall()
        return [Category.from_row(r) for r in rows]


async def list_categories_with_counts(
    *, db_path: str | None = None
) -> list[tuple[Category, int]]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT c.id, c.name, c.emoji, COUNT(i.id) AS item_count
            FROM categories c
            LEFT JOIN items i ON i.category_id = c.id
            GROUP BY c.id
            ORDER BY c.name COLLATE NOCASE
            """
        )
        rows = await cur.fetchall()
        out: list[tuple[Category, int]] = []
        for r in rows:
            out.append((Category.from_row(r), int(r["item_count"])))
        return out


async def get_category(*, category_id: int, db_path: str | None = None) -> Category | None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories WHERE id = ?", (category_id,)
        )
        row = await cur.fetchone()
        return Category.from_row(row) if row else None


async def delete_category(*, category_id: int, db_path: str | None = None) -> bool:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await conn.commit()
        return cur.rowcount > 0


async def create_link_item(
    *,
    category_id: int,
    title: str,
    url: str,
    description: str | None = None,
    db_path: str | None = None,
) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            INSERT INTO items(category_id, title, type, url, description)
            VALUES (?, ?, 'link', ?, ?)
            """,
            (category_id, title.strip(), url.strip(), (description or None)),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def create_file_item(
    *,
    category_id: int,
    title: str,
    telegram_message_id: int,
    description: str | None = None,
    db_path: str | None = None,
) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            INSERT INTO items(category_id, title, type, telegram_message_id, description)
            VALUES (?, ?, 'file', ?, ?)
            """,
            (category_id, title.strip(), telegram_message_id, (description or None)),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def list_items_by_category(
    *, category_id: int, db_path: str | None = None
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE category_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (category_id,),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def get_item(*, item_id: int, db_path: str | None = None) -> Item | None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE id = ?
            """,
            (item_id,),
        )
        row = await cur.fetchone()
        return Item.from_row(row) if row else None


async def delete_item(*, item_id: int, db_path: str | None = None) -> bool:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        await conn.commit()
        return cur.rowcount > 0


async def search_items(
    *, term: str, limit: int = 20, db_path: str | None = None
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = term.strip()
    if not normalized:
        return []
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE title LIKE ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (f"%{normalized}%", limit),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


def format_categories_list(categories_with_counts: Sequence[tuple[Category, int]]) -> str:
    if not categories_with_counts:
        return "📭 Nenhuma categoria cadastrada ainda."
    lines = ["📚 Categorias:"]
    for cat, count in categories_with_counts:
        lines.append(f"- {cat.emoji} {cat.name} (id {cat.id}) — {count} item(ns)")
    return "\n".join(lines)
