from __future__ import annotations

import argparse
import asyncio
import csv
import os
from typing import Any

from dotenv import load_dotenv
from telegram import Bot

from bot import database


load_dotenv()


def _get_bot_token() -> str:
    value = os.getenv("BOT_TOKEN", "").strip()
    if not value:
        raise RuntimeError("BOT_TOKEN não configurado")
    return value


def _get_channel_id(value: str | None) -> str:
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


async def import_csv(
    *,
    input_path: str,
    db_path: str | None,
    default_category: str,
    category_emoji: str,
    skip_existing: bool,
    description_limit: int,
    post_to_channel: bool,
    channel_id: str | None,
    disable_preview: bool,
    sleep_seconds: float,
) -> None:
    await database.init_db(db_path=db_path)
    with open(input_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("CSV vazio")

    bot = None
    resolved_channel_id = None
    if post_to_channel:
        bot = Bot(token=_get_bot_token())
        resolved_channel_id = _get_channel_id(channel_id)

    created = 0
    skipped = 0
    posted = 0
    for row in rows:
        title = str(row.get("titulo", "")).strip()
        url = str(row.get("url", "")).strip()
        if not title or not url:
            skipped += 1
            continue

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

        existing = await database.get_item_by_url(url=url, db_path=db_path)
        if existing and skip_existing:
            skipped += 1
            continue

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
    parser.add_argument("--input", dest="input_path", default="videos_cat_revisado.csv")
    parser.add_argument("--db-path", dest="db_path")
    parser.add_argument("--default-category", dest="default_category", default="Outros")
    parser.add_argument("--category-emoji", dest="category_emoji", default="📦")
    parser.add_argument(
        "--no-skip-existing", dest="skip_existing", action="store_false"
    )
    parser.add_argument(
        "--description-limit", dest="description_limit", type=int, default=900
    )
    parser.add_argument("--post-to-channel", dest="post_to_channel", action="store_true")
    parser.add_argument("--channel-id", dest="channel_id")
    parser.add_argument("--disable-preview", dest="disable_preview", action="store_true")
    parser.add_argument("--sleep", dest="sleep_seconds", type=float, default=0.0)
    parser.set_defaults(skip_existing=True)
    args = parser.parse_args()

    asyncio.run(
        import_csv(
            input_path=args.input_path,
            db_path=args.db_path,
            default_category=args.default_category,
            category_emoji=args.category_emoji,
            skip_existing=args.skip_existing,
            description_limit=args.description_limit,
            post_to_channel=args.post_to_channel,
            channel_id=args.channel_id,
            disable_preview=args.disable_preview,
            sleep_seconds=args.sleep_seconds,
        )
    )


if __name__ == "__main__":
    main()
