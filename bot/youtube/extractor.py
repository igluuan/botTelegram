from __future__ import annotations

import asyncio
from typing import Any

from yt_dlp import YoutubeDL


def _extract_flat_sync(
    channel_url: str, limite: int | None, last_sync_date: str | None
) -> list[dict]:
    opts: dict[str, Any] = {
    "quiet": True,
    "skip_download": True,
    "extract_flat": "in_playlist",
    "ignoreerrors": True,
    "extractor_args": {"youtube": {"lang": ["pt"]}},
    "http_headers": {"Accept-Language": "pt,pt-PT;q=0.9"},
}
    if limite and limite > 0:
        opts["playlistend"] = int(limite)
    if last_sync_date and last_sync_date.strip():
        opts["dateafter"] = last_sync_date.strip()
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
            title = entry.get("title") or ""
            if not video_id:
                continue
            out.append(
                {
                    "video_id": str(video_id),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "titulo_original": str(title),
                    "descricao": "",
                    "duracao_seg": None,
                    "data_publicacao": None,
                    "thumbnail_url": None,
                }
            )
    return out


def _extract_video_full_sync(video_id: str) -> dict:
    v = (video_id or "").strip()
    if not v:
        return {}
    opts: dict[str, Any] = {
    "quiet": True,
    "skip_download": True,
    "extract_flat": False,
    "ignoreerrors": True,
    "extractor_args": {"youtube": {"lang": ["pt"]}},
    "http_headers": {"Accept-Language": "pt,pt-PT;q=0.9"},
}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={v}", download=False)
        if not isinstance(info, dict):
            return {}
        url = info.get("webpage_url") or info.get("url") or f"https://www.youtube.com/watch?v={v}"
        title = info.get("title") or ""
        desc = info.get("description") or ""
        duration = info.get("duration")
        upload_date = info.get("upload_date")
        thumb = info.get("thumbnail")
        return {
            "video_id": v,
            "url": str(url),
            "titulo_original": str(title),
            "descricao": str(desc),
            "duracao_seg": int(duration) if isinstance(duration, (int, float)) else None,
            "data_publicacao": str(upload_date) if upload_date else None,
            "thumbnail_url": str(thumb) if thumb else None,
        }


def _extract_sync(channel_url: str, limite: int | None) -> list[dict]:
    opts: dict[str, Any] = {
    "quiet": True,
    "skip_download": True,
    "extract_flat": False,
    "ignoreerrors": True,
    "extractor_args": {"youtube": {"lang": ["pt"]}},
    "http_headers": {"Accept-Language": "pt,pt-PT;q=0.9"},
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


async def extrair_lista_canal_flat(
    channel_url: str, limite: int | None = None, *, last_sync_date: str | None = None
) -> list[dict]:
    return await asyncio.to_thread(_extract_flat_sync, channel_url, limite, last_sync_date)


async def extrair_video_full(video_id: str) -> dict:
    return await asyncio.to_thread(_extract_video_full_sync, video_id)


async def extrair_videos_canal(channel_url: str, limite: int | None = None) -> list[dict]:
    return await asyncio.to_thread(_extract_sync, channel_url, limite)
