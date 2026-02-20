from __future__ import annotations

from bot.config import get_settings
from bot.db.connection import connect


async def _get_existing_columns(conn, table: str) -> set[str]:
    cur = await conn.execute(f"PRAGMA table_info({table})")
    rows = await cur.fetchall()
    return {str(r["name"]) for r in rows}


async def _ensure_items_columns(conn) -> None:
    existing = await _get_existing_columns(conn, "items")
    desired: list[tuple[str, str]] = [
        ("video_id", "TEXT"),
        ("marca", "TEXT"),
        ("modelo", "TEXT"),
        ("tipo", "TEXT"),
        ("nivel", "TEXT"),
        ("youtube_url", "TEXT"),
        ("tags", "TEXT"),
    ]
    for name, ddl in desired:
        if name not in existing:
            await conn.execute(f"ALTER TABLE items ADD COLUMN {name} {ddl}")


async def _ensure_indexes(conn) -> None:
    await conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_items_video_id_unique ON items(video_id)"
    )


async def init_db(*, db_path: str | None = None) -> None:
    settings = get_settings()
    resolved = db_path or settings.database_path
    async with connect(resolved) as conn:
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
                video_id TEXT,
                marca TEXT,
                modelo TEXT,
                tipo TEXT,
                nivel TEXT,
                youtube_url TEXT,
                tags TEXT,
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

            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        await _ensure_items_columns(conn)
        await _ensure_indexes(conn)
        await conn.commit()
