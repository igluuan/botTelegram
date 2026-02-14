from __future__ import annotations

import asyncio
from typing import Any

from yt_dlp import YoutubeDL


def _extract_sync(channel_url: str, limite: int | None) -> list[dict]:
    opts: dict[str, Any] = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
    }
    if limite and limite > 0:
        opts["playlistend"] = int(limite)
    out: list[dict] = []
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        entries = info.get("entries") if isinstance(info, dict) else None
        if not entries and isinstance(info, dict):
            entries = [info]
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            video_id = entry.get("id")
            url = entry.get("webpage_url") or entry.get("url")
            title = entry.get("title") or ""
            desc = entry.get("description") or ""
            duration = entry.get("duration")
            upload_date = entry.get("upload_date")
            thumb = entry.get("thumbnail")
            if not url or not video_id:
                continue
            out.append(
                {
                    "video_id": str(video_id),
                    "url": str(url),
                    "titulo_original": str(title),
                    "descricao": str(desc),
                    "duracao_seg": int(duration) if isinstance(duration, (int, float)) else None,
                    "data_publicacao": str(upload_date) if upload_date else None,
                    "thumbnail_url": str(thumb) if thumb else None,
                }
            )
    return out


async def extrair_videos_canal(channel_url: str, limite: int | None = None) -> list[dict]:
    return await asyncio.to_thread(_extract_sync, channel_url, limite)
