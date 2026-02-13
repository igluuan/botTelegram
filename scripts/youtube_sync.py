from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

import anthropic
from dotenv import load_dotenv
from telegram import Bot

from bot import database
from scripts.youtube_categorize import (
    _categorizar,
    _get_api_key as _get_anthropic_key,
    _load_categories,
    _normalize_result,
    _system_prompt,
)
from scripts.youtube_export import _collect_videos, _get_channel_id


load_dotenv()


def _get_bot_token() -> str:
    value = os.getenv("BOT_TOKEN", "").strip()
    if not value:
        raise RuntimeError("BOT_TOKEN não configurado")
    return value


def _get_storage_channel_id(value: str | None) -> str:
    channel_id = value or os.getenv("STORAGE_CHANNEL_ID", "").strip()
    if not channel_id:
        raise RuntimeError("STORAGE_CHANNEL_ID não configurado")
    return channel_id


def _build_description(row: dict[str, Any], *, max_chars: int) -> str | None:
    lines: list[str] = []
    topico = str(row.get("topico", "")).strip()
    tags = str(row.get("tags", "")).strip()
    nivel = str(row.get("nivel", "")).strip()
    data = str(row.get("data", "")).strip()
    descricao = str(row.get("descricao", "")).strip()

    if topico:
        lines.append(f"🔧 Tópico: {topico}")
    if tags:
        lines.append(f"🏷️ Tags: {tags}")
    if nivel:
        lines.append(f"📊 Nível: {nivel}")
    if data:
        lines.append(f"📅 Data: {data}")
    if descricao:
        if lines:
            lines.append("")
        if len(descricao) > max_chars:
            descricao = descricao[:max_chars].rstrip() + "…"
        lines.append(descricao)
    if not lines:
        return None
    return "\n".join(lines)


def _build_caption(row: dict[str, Any]) -> str:
    lines: list[str] = []
    equipamento = str(row.get("equipamento", "")).strip()
    topico = str(row.get("topico", "")).strip()
    tags = str(row.get("tags", "")).strip()
    nivel = str(row.get("nivel", "")).strip()
    url = str(row.get("url", "")).strip()

    if equipamento:
        lines.append(f"📦 Equipamento: {equipamento}")
    if topico:
        lines.append(f"🔧 Tópico: {topico}")
    if tags:
        lines.append(f"🏷️ Tags: {tags}")
    if nivel:
        lines.append(f"📊 Nível: {nivel}")
    if url:
        if lines:
            lines.append("")
        lines.append(f"🔗 {url}")
    return "\n".join(lines).strip()


async def sync_videos(
    *,
    channel_id: str | None,
    db_path: str | None,
    categories_path: str,
    default_category: str,
    category_emoji: str,
    limit: int | None,
    max_pages: int | None,
    sleep_seconds: float,
    description_limit: int,
    dry_run: bool,
    post_to_channel: bool,
    channel_storage_id: str | None,
    disable_preview: bool,
) -> None:
    await database.init_db(db_path=db_path)
    channel_id = _get_channel_id(channel_id)
    videos = _collect_videos(channel_id, limit=limit, max_pages=max_pages)
    if not videos:
        print("Nenhum vídeo encontrado para sincronizar.")
        return

    client = None
    system_prompt = ""
    if not dry_run:
        categories = _load_categories(categories_path)
        client = anthropic.Anthropic(api_key=_get_anthropic_key())
        system_prompt = _system_prompt(categories)

    bot = None
    resolved_channel_id = None
    if post_to_channel:
        bot = Bot(token=_get_bot_token())
        resolved_channel_id = _get_storage_channel_id(channel_storage_id)

    created = 0
    skipped = 0
    posted = 0
    for video in videos:
        url = str(video.get("url", "")).strip()
        title = str(video.get("titulo", "")).strip()
        if not url or not title:
            skipped += 1
            continue

        existing = await database.get_item_by_url(url=url, db_path=db_path)
        if existing:
            skipped += 1
            continue

        if dry_run:
            normalized = {"equipamento": "", "topico": "", "tags": "", "nivel": ""}
        else:
            try:
                result = _categorizar(
                    client,
                    system_prompt=system_prompt,
                    titulo=video.get("titulo", ""),
                    descricao=video.get("descricao", ""),
                )
            except Exception:
                result = {}
            normalized = _normalize_result(result)

        row = dict(video)
        row.update(normalized)

        equipamento = str(row.get("equipamento", "")).strip() or default_category
        category = await database.get_category_by_name(
            name=equipamento, db_path=db_path
        )
        if category:
            category_id = category.id
        else:
            category_id = await database.create_category(
                name=equipamento, emoji=category_emoji, db_path=db_path
            )

        description = _build_description(row, max_chars=description_limit)
        item_id = await database.create_link_item(
            category_id=category_id,
            title=title,
            url=url,
            description=description,
            db_path=db_path,
        )
        created += 1

        if bot and resolved_channel_id:
            caption = _build_caption(row)
            msg = await bot.send_message(
                chat_id=resolved_channel_id,
                text=caption,
                disable_web_page_preview=disable_preview,
            )
            await database.update_item_telegram_message_id(
                item_id=item_id,
                telegram_message_id=int(msg.message_id),
                db_path=db_path,
            )
            posted += 1

        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)

    print(f"Itens criados: {created}")
    print(f"Itens ignorados: {skipped}")
    if post_to_channel:
        print(f"Posts enviados ao canal: {posted}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel-id", dest="channel_id")
    parser.add_argument("--db-path", dest="db_path")
    parser.add_argument("--categories", dest="categories_path", default="categorias.json")
    parser.add_argument("--default-category", dest="default_category", default="Outros")
    parser.add_argument("--category-emoji", dest="category_emoji", default="📦")
    parser.add_argument("--limit", dest="limit", type=int, default=50)
    parser.add_argument("--max-pages", dest="max_pages", type=int)
    parser.add_argument("--sleep", dest="sleep_seconds", type=float, default=0.3)
    parser.add_argument(
        "--description-limit", dest="description_limit", type=int, default=900
    )
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--post-to-channel", dest="post_to_channel", action="store_true")
    parser.add_argument("--channel-storage-id", dest="channel_storage_id")
    parser.add_argument("--disable-preview", dest="disable_preview", action="store_true")
    args = parser.parse_args()

    asyncio.run(
        sync_videos(
            channel_id=args.channel_id,
            db_path=args.db_path,
            categories_path=args.categories_path,
            default_category=args.default_category,
            category_emoji=args.category_emoji,
            limit=args.limit,
            max_pages=args.max_pages,
            sleep_seconds=args.sleep_seconds,
            description_limit=args.description_limit,
            dry_run=args.dry_run,
            post_to_channel=args.post_to_channel,
            channel_storage_id=args.channel_storage_id,
            disable_preview=args.disable_preview,
        )
    )


if __name__ == "__main__":
    main()
