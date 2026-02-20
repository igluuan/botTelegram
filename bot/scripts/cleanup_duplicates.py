from __future__ import annotations

import re
import sqlite3
from typing import Any

from bot.config import get_settings


def extract_video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def main() -> None:
    settings = get_settings()
    con = sqlite3.connect(settings.database_path)
    try:
        rows = con.execute("SELECT id, url FROM items WHERE type='link'").fetchall()
        seen: dict[str, int] = {}
        to_delete: list[int] = []
        
        for item_id, url in rows:
            vid = extract_video_id(url)
            if not vid:
                continue
            if vid in seen:
                to_delete.append(item_id)
            else:
                seen[vid] = item_id
        
        print(f"Duplicatas encontradas: {len(to_delete)}")
        if to_delete:
            print("Removendo duplicatas...")
            con.executemany("DELETE FROM items WHERE id=?", [(i,) for i in to_delete])
            con.commit()
            print("Duplicatas removidas com sucesso.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
