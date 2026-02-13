from __future__ import annotations

import argparse
import csv
import os
from typing import Any

from googleapiclient.discovery import build
from dotenv import load_dotenv


load_dotenv()


def _get_api_key() -> str:
    value = os.getenv("YOUTUBE_API_KEY", "").strip() or os.getenv("API_YT", "").strip()
    if not value:
        raise RuntimeError("YOUTUBE_API_KEY não configurado (ou API_YT)")
    return value


def _get_channel_id(value: str | None) -> str:
    channel_id = (
        value
        or os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
        or os.getenv("CHANNEL_ID_YT", "").strip()
    )
    if not channel_id:
        raise RuntimeError("YOUTUBE_CHANNEL_ID não configurado (ou CHANNEL_ID_YT)")
    return channel_id


def _collect_videos(
    channel_id: str, *, limit: int | None, max_pages: int | None
) -> list[dict[str, Any]]:
    yt = build("youtube", "v3", developerKey=_get_api_key())
    videos: list[dict[str, Any]] = []
    token: str | None = None
    pages = 0

    while True:
        if max_pages is not None and pages >= max_pages:
            break
        res = (
            yt.search()
            .list(
                part="snippet",
                channelId=channel_id,
                maxResults=50,
                pageToken=token,
                type="video",
                order="date",
            )
            .execute()
        )
        pages += 1
        for item in res.get("items", []):
            snippet = item.get("snippet", {})
            vid = item.get("id", {}).get("videoId")
            if not vid:
                continue
            published = snippet.get("publishedAt", "")
            videos.append(
                {
                    "video_id": vid,
                    "titulo": snippet.get("title", ""),
                    "descricao": snippet.get("description", ""),
                    "url": f"https://youtu.be/{vid}",
                    "data": published[:10],
                    "equipamento": "",
                    "topico": "",
                    "tags": "",
                    "nivel": "",
                }
            )
            if limit is not None and len(videos) >= limit:
                return videos

        token = res.get("nextPageToken")
        if not token:
            break

    return videos


def exportar_canal(
    *, channel_id: str, output_path: str, limit: int | None, max_pages: int | None
) -> int:
    videos = _collect_videos(channel_id, limit=limit, max_pages=max_pages)
    if not videos:
        raise RuntimeError("Nenhum vídeo encontrado para o canal informado")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(videos[0].keys()))
        writer.writeheader()
        writer.writerows(videos)
    return len(videos)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel-id", dest="channel_id")
    parser.add_argument("--output", dest="output", default="videos.csv")
    parser.add_argument("--limit", dest="limit", type=int, default=50)
    parser.add_argument("--max-pages", dest="max_pages", type=int)
    args = parser.parse_args()

    channel_id = _get_channel_id(args.channel_id)
    count = exportar_canal(
        channel_id=channel_id,
        output_path=args.output,
        limit=args.limit,
        max_pages=args.max_pages,
    )
    print(f"{count} vídeos exportados para {args.output}")


if __name__ == "__main__":
    main()
