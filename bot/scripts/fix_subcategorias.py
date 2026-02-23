from __future__ import annotations
import asyncio
from bot.config import get_settings
from bot.db.connection import connect
from bot.youtube.subcategories import detectar_subcategoria

async def main() -> None:
    settings = get_settings()
    async with connect(settings.database_path) as conn:
        # Primeiro garantir que a coluna existe
        from bot.db.schema import _ensure_items_columns
        await _ensure_items_columns(conn)

        cur = await conn.execute("SELECT id, title, tags FROM items")
        rows = await cur.fetchall()
        atualizados = 0
        for row in rows:
            sub = detectar_subcategoria(
                titulo=str(row["title"] or ""),
                tags=str(row["tags"] or ""),
            )
            await conn.execute(
                "UPDATE items SET subcategoria = ? WHERE id = ?",
                (sub, row["id"]),
            )
            atualizados += 1
        await conn.commit()
    print(f"Atualizados: {atualizados}")

if __name__ == "__main__":
    asyncio.run(main())
