from __future__ import annotations

import argparse
import asyncio
import os
import shutil

from bot.config import get_settings
from bot.db.connection import connect
from bot import database
from bot.youtube.categorizer import categorizar_video


def _extract_brand_from_description(description: str) -> str | None:
    if not description:
        return None
    first_line = description.splitlines()[0].strip()
    if first_line.startswith("📦"):
        label = first_line[1:].strip()
        candidate = label.split()[0].strip()
        known = {
            "Epson",
            "Brother",
            "HP",
            "Canon",
            "Kyocera",
            "Ricoh",
            "Lexmark",
            "Xerox",
            "Samsung",
            "Konica",
            "OKI",
        }
        if candidate in known:
            return candidate
    return None


async def _migrate_item(row, *, dry_run: bool) -> tuple[bool, str]:
    item_id = int(row["id"])
    desc = row["description"] or ""
    title = row["title"] or ""
    brand = _extract_brand_from_description(desc)
    if not brand:
        data = await categorizar_video(titulo=title, descricao=desc)
        brand = str(data.get("marca") or "").strip() or "Outros (sem marca)"
    cat = await database.get_category_by_name(name=brand)
    if not cat and not dry_run:
        cat_id = await database.create_category(name=brand, emoji="🖨️")
    else:
        cat_id = cat.id if cat else None
    if dry_run:
        return True, brand
    if cat_id is None:
        return False, brand
    settings = get_settings()
    async with connect(settings.database_path) as conn:
        await conn.execute(
            "UPDATE items SET category_id = ? WHERE id = ?", (cat_id, item_id)
        )
        await conn.commit()
    return True, brand


async def main() -> None:
    parser = argparse.ArgumentParser(description="Migra categorias por modelo para marca")
    parser.add_argument("--dry-run", action="store_true", help="Não grava alterações")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Cria cópia de backup do banco antes de migrar",
    )
    parser.add_argument(
        "--cleanup-vazias",
        action="store_true",
        help="Remove categorias vazias após migração",
    )
    args = parser.parse_args()

    settings = get_settings()
    if args.backup and not args.dry_run:
        src = settings.database_path
        base, ext = os.path.splitext(src)
        dst = f"{base}.backup_brand{ext or ''}"
        if os.path.exists(src):
            shutil.copyfile(src, dst)
            print(f"Backup: {dst}")

    total = 0
    ok = 0
    fail = 0
    async with connect(settings.database_path) as conn:
        cur = await conn.execute(
            "SELECT id, title, description FROM items WHERE type = 'link'"
        )
        rows = await cur.fetchall()
    for r in rows:
        total += 1
        try:
            done, brand = await _migrate_item(r, dry_run=args.dry_run)
            if done:
                ok += 1
            else:
                fail += 1
        except Exception:
            fail += 1
    print(f"Migração concluída. Total: {total}, atualizados: {ok}, falhas: {fail}")

    if args.cleanup_vazias and not args.dry_run:
        async with connect(settings.database_path) as conn:
            await conn.execute(
                "DELETE FROM categories WHERE id NOT IN (SELECT DISTINCT category_id FROM items)"
            )
            await conn.commit()
        print("Categorias vazias removidas")


if __name__ == "__main__":
    asyncio.run(main())
