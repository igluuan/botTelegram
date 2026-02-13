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

            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, item_id)
            );

            CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_history_user_id ON history(user_id);
            CREATE INDEX IF NOT EXISTS idx_history_item_id ON history(item_id);
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


async def list_categories(
    *, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Category]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cur.fetchall()
        return [Category.from_row(r) for r in rows]


async def count_categories(*, db_path: str | None = None) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM categories")
        row = await cur.fetchone()
        return int(row[0]) if row else 0


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


async def list_categories_with_counts_paged(
    *, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[tuple[Category, int]]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT c.id, c.name, c.emoji, COUNT(i.id) AS item_count
            FROM categories c
            LEFT JOIN items i ON i.category_id = c.id
            GROUP BY c.id
            ORDER BY c.name COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
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


async def get_category_by_name(
    *, name: str, db_path: str | None = None
) -> Category | None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = name.strip()
    if not normalized:
        return None
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories WHERE LOWER(name) = LOWER(?)",
            (normalized,),
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


async def update_item_telegram_message_id(
    *, item_id: int, telegram_message_id: int, db_path: str | None = None
) -> bool:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "UPDATE items SET telegram_message_id = ? WHERE id = ?",
            (telegram_message_id, item_id),
        )
        await conn.commit()
        return cur.rowcount > 0


async def list_items_by_category(
    *, category_id: int, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE category_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (category_id, limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_items_by_category(
    *, category_id: int, db_path: str | None = None
) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM items WHERE category_id = ?", (category_id,)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


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


async def get_item_by_url(*, url: str, db_path: str | None = None) -> Item | None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = url.strip()
    if not normalized:
        return None
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE url = ?
            """,
            (normalized,),
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
    *, term: str, page: int = 1, limit: int = 20, db_path: str | None = None
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = term.strip()
    if not normalized:
        return []
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE title LIKE ?
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (f"%{normalized}%", limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_search_items(*, term: str, db_path: str | None = None) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = term.strip()
    if not normalized:
        return 0
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM items WHERE title LIKE ?", (f"%{normalized}%",)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def search_items_by_category(
    *,
    category_id: int,
    term: str,
    page: int = 1,
    limit: int = 20,
    db_path: str | None = None,
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = term.strip()
    if not normalized:
        return []
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description
            FROM items
            WHERE category_id = ? AND title LIKE ?
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (category_id, f"%{normalized}%", limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_search_items_by_category(
    *, category_id: int, term: str, db_path: str | None = None
) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    normalized = term.strip()
    if not normalized:
        return 0
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM items WHERE category_id = ? AND title LIKE ?",
            (category_id, f"%{normalized}%"),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def add_favorite(
    *, user_id: int, item_id: int, db_path: str | None = None
) -> None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO favorites(user_id, item_id) VALUES (?, ?)",
            (user_id, item_id),
        )
        await conn.commit()


async def remove_favorite(
    *, user_id: int, item_id: int, db_path: str | None = None
) -> None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        )
        await conn.commit()


async def is_favorite(
    *, user_id: int, item_id: int, db_path: str | None = None
) -> bool:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        )
        row = await cur.fetchone()
        return row is not None


async def list_favorites(
    *, user_id: int, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT i.id, i.category_id, i.title, i.type, i.telegram_message_id, i.url, i.description
            FROM favorites f
            JOIN items i ON i.id = f.item_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_favorites(*, user_id: int, db_path: str | None = None) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def add_history_entry(
    *, user_id: int, item_id: int, limit: int = 20, db_path: str | None = None
) -> None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        await conn.execute(
            "INSERT INTO history(user_id, item_id) VALUES (?, ?)", (user_id, item_id)
        )
        await conn.execute(
            """
            DELETE FROM history
            WHERE id IN (
                SELECT id FROM history
                WHERE user_id = ?
                ORDER BY accessed_at DESC, id DESC
                LIMIT -1 OFFSET ?
            )
            """,
            (user_id, limit),
        )
        await conn.commit()


async def list_history(
    *, user_id: int, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Item]:
    settings = get_settings()
    resolved = db_path or settings.database_path
    offset = (page - 1) * limit
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT i.id, i.category_id, i.title, i.type, i.telegram_message_id, i.url, i.description
            FROM history h
            JOIN items i ON i.id = h.item_id
            WHERE h.user_id = ?
            ORDER BY h.accessed_at DESC, h.id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_history(*, user_id: int, db_path: str | None = None) -> int:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with _connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


def format_categories_list(categories_with_counts: Sequence[tuple[Category, int]]) -> str:
    if not categories_with_counts:
        return "📭 Nenhuma categoria cadastrada ainda."
    lines = ["📚 Categorias:"]
    for cat, count in categories_with_counts:
        lines.append(f"- {cat.emoji} {cat.name} (id {cat.id}) — {count} item(ns)")
    return "\n".join(lines)
