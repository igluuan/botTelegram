from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil

from bot.config import get_settings
from bot.db.connection import connect


def extract_video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove duplicatas de links do YouTube (mantém o menor id por vídeo)"
    )
    parser.add_argument("--apply", action="store_true", help="Executa a remoção no banco")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Cria cópia de backup do banco antes de remover",
    )
    args = parser.parse_args()

    settings = get_settings()
    if args.backup and args.apply:
        src = settings.database_path
        base, ext = os.path.splitext(src)
        dst = f"{base}.backup_youtube_dupes{ext or ''}"
        if os.path.exists(src):
            shutil.copyfile(src, dst)
            print(f"Backup: {dst}")

    async with connect(settings.database_path) as conn:
        cur = await conn.execute("SELECT id, url FROM items WHERE type = 'link'")
        rows = await cur.fetchall()

    seen: dict[str, int] = {}
    to_delete: list[int] = []
    for r in rows:
        item_id = int(r["id"])
        url = str(r["url"] or "")
        vid = extract_video_id(url)
        if not vid:
            continue
        if vid in seen:
            to_delete.append(item_id)
        else:
            seen[vid] = item_id

    print(f"Duplicatas encontradas: {len(to_delete)}")
    if not to_delete:
        return

    if not args.apply:
        preview = ", ".join(str(i) for i in to_delete[:20])
        print(f"Exemplos de IDs (até 20): {preview}")
        print("Use --apply para remover")
        return

    async with connect(settings.database_path) as conn:
        await conn.executemany("DELETE FROM items WHERE id = ?", [(i,) for i in to_delete])
        await conn.commit()
    print(f"Removidas: {len(to_delete)}")


if __name__ == "__main__":
    asyncio.run(main())
