from __future__ import annotations

from collections.abc import Sequence

from bot.config import get_settings
from bot.db.connection import connect
from bot.models import Category, Item


_DB_PATH: str = ""


def configure(*, db_path: str) -> None:
    global _DB_PATH
    _DB_PATH = db_path


def _resolve_db_path(db_path: str | None) -> str:
    if db_path:
        return db_path
    if _DB_PATH:
        return _DB_PATH
    return get_settings().database_path


async def create_category(
    *, name: str, emoji: str = "📁", db_path: str | None = None
) -> int:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "INSERT INTO categories(name, emoji) VALUES (?, ?)",
            (name.strip(), emoji.strip() or "📁"),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def list_categories(
    *, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Category]:
    resolved = _resolve_db_path(db_path)
    offset = (page - 1) * limit
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cur.fetchall()
        return [Category.from_row(r) for r in rows]


async def count_categories(*, db_path: str | None = None) -> int:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM categories")
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def list_categories_with_counts(
    *, db_path: str | None = None
) -> list[tuple[Category, int]]:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
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
    resolved = _resolve_db_path(db_path)
    offset = (page - 1) * limit
    async with connect(resolved) as conn:
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
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories WHERE id = ?", (category_id,)
        )
        row = await cur.fetchone()
        return Category.from_row(row) if row else None


async def get_category_by_name(
    *, name: str, db_path: str | None = None
) -> Category | None:
    resolved = _resolve_db_path(db_path)
    normalized = name.strip()
    if not normalized:
        return None
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT id, name, emoji FROM categories WHERE LOWER(name) = LOWER(?)",
            (normalized,),
        )
        row = await cur.fetchone()
        return Category.from_row(row) if row else None


async def delete_category(*, category_id: int, db_path: str | None = None) -> bool:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await conn.commit()
        return cur.rowcount > 0


async def create_link_item(
    *,
    category_id: int,
    title: str,
    url: str,
    description: str | None = None,
    video_id: str | None = None,
    marca: str | None = None,
    modelo: str | None = None,
    tipo: str | None = None,
    nivel: str | None = None,
    youtube_url: str | None = None,
    subcategoria: str | None = None,
    db_path: str | None = None,
) -> int:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            INSERT INTO items(
                category_id,
                title,
                type,
                url,
                description,
                video_id,
                marca,
                modelo,
                tipo,
                nivel,
                youtube_url,
                subcategoria
            )
            VALUES (?, ?, 'link', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category_id,
                title.strip(),
                url.strip(),
                (description or None),
                (video_id.strip() if video_id else None),
                (marca or None),
                (modelo or None),
                (tipo or None),
                (nivel or None),
                (youtube_url.strip() if youtube_url else None),
                (subcategoria or None),
            ),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def create_file_item(
    *,
    category_id: int,
    title: str,
    telegram_message_id: int,
    description: str | None = None,
    video_id: str | None = None,
    marca: str | None = None,
    modelo: str | None = None,
    tipo: str | None = None,
    nivel: str | None = None,
    youtube_url: str | None = None,
    subcategoria: str | None = None,
    db_path: str | None = None,
) -> int:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            INSERT INTO items(
                category_id,
                title,
                type,
                telegram_message_id,
                description,
                video_id,
                marca,
                modelo,
                tipo,
                nivel,
                youtube_url,
                subcategoria
            )
            VALUES (?, ?, 'file', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category_id,
                title.strip(),
                telegram_message_id,
                (description or None),
                (video_id.strip() if video_id else None),
                (marca or None),
                (modelo or None),
                (tipo or None),
                (nivel or None),
                (youtube_url.strip() if youtube_url else None),
                (subcategoria or None),
            ),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def update_item_telegram_message_id(
    *, item_id: int, telegram_message_id: int, db_path: str | None = None
) -> bool:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "UPDATE items SET telegram_message_id = ? WHERE id = ?",
            (telegram_message_id, item_id),
        )
        await conn.commit()
        return cur.rowcount > 0


async def list_items_by_category(
    *, category_id: int, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Item]:
    resolved = _resolve_db_path(db_path)
    offset = (page - 1) * limit
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
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
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM items WHERE category_id = ?", (category_id,)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def get_item(*, item_id: int, db_path: str | None = None) -> Item | None:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
            FROM items
            WHERE id = ?
            """,
            (item_id,),
        )
        row = await cur.fetchone()
        return Item.from_row(row) if row else None


async def get_item_by_url(*, url: str, db_path: str | None = None) -> Item | None:
    resolved = _resolve_db_path(db_path)
    normalized = url.strip()
    if not normalized:
        return None
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
            FROM items
            WHERE url = ?
            """,
            (normalized,),
        )
        row = await cur.fetchone()
        return Item.from_row(row) if row else None


async def get_item_by_video_id(
    *, video_id: str, db_path: str | None = None
) -> Item | None:
    resolved = _resolve_db_path(db_path)
    normalized = video_id.strip()
    if not normalized:
        return None
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
            FROM items
            WHERE video_id = ?
            """,
            (normalized,),
        )
        row = await cur.fetchone()
        return Item.from_row(row) if row else None


async def delete_item(*, item_id: int, db_path: str | None = None) -> bool:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        await conn.commit()
        return cur.rowcount > 0


async def search_items(
    *, term: str, page: int = 1, limit: int = 20, db_path: str | None = None
) -> list[Item]:
    resolved = _resolve_db_path(db_path)
    normalized = term.strip()
    if not normalized:
        return []
    offset = (page - 1) * limit
    param = f"%{normalized}%"
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
            FROM items
            WHERE (title LIKE ? OR description LIKE ? OR marca LIKE ? OR modelo LIKE ? OR tags LIKE ?)
            ORDER BY
              CASE
                WHEN LOWER(modelo) = LOWER(?) THEN 0
                WHEN LOWER(marca) = LOWER(?) THEN 1
                WHEN title LIKE ? THEN 2
                ELSE 3
              END, id DESC
            LIMIT ? OFFSET ?
            """,
            (param, param, param, param, param, normalized, normalized, param, limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_search_items(*, term: str, db_path: str | None = None) -> int:
    resolved = _resolve_db_path(db_path)
    normalized = term.strip()
    if not normalized:
        return 0
    param = f"%{normalized}%"
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM items WHERE (title LIKE ? OR description LIKE ? OR marca LIKE ? OR modelo LIKE ? OR tags LIKE ?)",
            (param, param, param, param, param),
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
    resolved = _resolve_db_path(db_path)
    normalized = term.strip()
    if not normalized:
        return []
    offset = (page - 1) * limit
    param = f"%{normalized}%"
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
            FROM items
            WHERE category_id = ? AND (title LIKE ? OR description LIKE ? OR marca LIKE ? OR modelo LIKE ? OR tags LIKE ?)
            ORDER BY
              CASE
                WHEN LOWER(modelo) = LOWER(?) THEN 0
                WHEN LOWER(marca) = LOWER(?) THEN 1
                WHEN title LIKE ? THEN 2
                ELSE 3
              END, id DESC
            LIMIT ? OFFSET ?
            """,
            (
                category_id,
                param,
                param,
                param,
                param,
                param,
                normalized,
                normalized,
                param,
                limit,
                offset,
            ),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_search_items_by_category(
    *, category_id: int, term: str, db_path: str | None = None
) -> int:
    resolved = _resolve_db_path(db_path)
    normalized = term.strip()
    if not normalized:
        return 0
    param = f"%{normalized}%"
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM items WHERE category_id = ? AND (title LIKE ? OR description LIKE ? OR marca LIKE ? OR modelo LIKE ? OR tags LIKE ?)",
            (category_id, param, param, param, param, param),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def add_favorite(
    *, user_id: int, item_id: int, db_path: str | None = None
) -> None:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO favorites(user_id, item_id) VALUES (?, ?)",
            (user_id, item_id),
        )
        await conn.commit()


async def remove_favorite(
    *, user_id: int, item_id: int, db_path: str | None = None
) -> None:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        )
        await conn.commit()


async def is_favorite(
    *, user_id: int, item_id: int, db_path: str | None = None
) -> bool:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        )
        row = await cur.fetchone()
        return row is not None


async def list_favorites(
    *, user_id: int, page: int = 1, limit: int = 10, db_path: str | None = None
) -> list[Item]:
    resolved = _resolve_db_path(db_path)
    offset = (page - 1) * limit
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT i.id, i.category_id, i.title, i.type, i.telegram_message_id, i.url, i.description,
                   i.video_id, i.marca, i.modelo, i.tipo, i.nivel, i.youtube_url, i.subcategoria
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
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def add_history_entry(
    *, user_id: int, item_id: int, limit: int = 20, db_path: str | None = None
) -> None:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
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
    resolved = _resolve_db_path(db_path)
    offset = (page - 1) * limit
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT i.id, i.category_id, i.title, i.type, i.telegram_message_id, i.url, i.description,
                   i.video_id, i.marca, i.modelo, i.tipo, i.nivel, i.youtube_url, i.subcategoria
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
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
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


async def list_marcas(db_path: str | None = None) -> list[str]:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT DISTINCT marca FROM items
            WHERE marca IS NOT NULL AND TRIM(marca) != ''
            ORDER BY marca COLLATE NOCASE
            """
        )
        rows = await cur.fetchall()
        return [str(r["marca"]) for r in rows]


async def list_subcategorias_by_marca(
    marca: str, db_path: str | None = None
) -> list[str]:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT DISTINCT subcategoria FROM items
            WHERE marca = ? AND subcategoria IS NOT NULL AND TRIM(subcategoria) != ''
            ORDER BY subcategoria COLLATE NOCASE
            """,
            (marca,),
        )
        rows = await cur.fetchall()
        return [str(r["subcategoria"]) for r in rows]


async def list_items_by_marca_subcategoria(
    *,
    marca: str,
    subcategoria: str,
    page: int = 1,
    limit: int = 10,
    db_path: str | None = None,
) -> list[Item]:
    resolved = _resolve_db_path(db_path)
    offset = (page - 1) * limit
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT id, category_id, title, type, telegram_message_id, url, description,
                   video_id, marca, modelo, tipo, nivel, youtube_url, subcategoria
            FROM items
            WHERE marca = ? AND subcategoria = ?
            ORDER BY title COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (marca, subcategoria, limit, offset),
        )
        rows = await cur.fetchall()
        return [Item.from_row(r) for r in rows]


async def count_items_by_marca_subcategoria(
    *, marca: str, subcategoria: str, db_path: str | None = None
) -> int:
    resolved = _resolve_db_path(db_path)
    async with connect(resolved) as conn:
        cur = await conn.execute(
            """
            SELECT COUNT(*) FROM items
            WHERE marca = ? AND subcategoria = ?
            """,
            (marca, subcategoria),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0
