from __future__ import annotations

import argparse
import asyncio
import re
from typing import Any

from bot.config import get_settings
from bot.db.connection import connect
from bot.db.schema import init_db
from bot import database
from bot.youtube.extractor import extrair_videos_canal
from bot.youtube.categorizer import categorizar_video, montar_description


def normalize_youtube_url(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url


def _resolver_canal(raw: str) -> str:
    v = raw.strip()
    up = v.upper()
    if v.startswith("http"):
        return v
    if v.startswith("@"):
        return f"https://www.youtube.com/{v}"
    if up.startswith("UC") and len(v) > 2:
        return f"https://www.youtube.com/playlist?list=UU{v[2:]}"
    if up.startswith("UU") or up.startswith("PL"):
        return f"https://www.youtube.com/playlist?list={v}"
    return f"https://www.youtube.com/{v}"


async def _get_or_create_categoria(nome: str) -> int:
    cat = await database.get_category_by_name(name=nome)
    if cat:
        return cat.id
    return await database.create_category(name=nome, emoji="🖨️")


def _nome_categoria(dados: dict, categoria_por: str) -> str:
    if categoria_por == "modelo":
        nome = str(dados.get("equipamento") or "").strip()
        return nome or "Outros (sem marca)"
    marca = str(dados.get("marca") or "").strip()
    return marca or "Outros (sem marca)"


async def _processar_video(video: dict, categoria_por: str) -> tuple[bool, str | None]:
    url = normalize_youtube_url(str(video["url"]))
    existing = await database.get_item_by_url(url=url)
    if existing:
        return False, None
    dados = await categorizar_video(
        titulo=str(video.get("titulo_original") or ""),
        descricao=str(video.get("descricao") or ""),
    )
    cat_name = _nome_categoria(dados, categoria_por)
    cat_id = await _get_or_create_categoria(cat_name)
    desc = montar_description(dados)
    await database.create_link_item(
        category_id=cat_id,
        title=dados["topico"],
        url=url,
        description=desc,
    )
    return True, cat_name


async def _reprocessar_itens_sem_description() -> tuple[int, int]:
    ok = 0
    fail = 0
    settings = get_settings()
    async with connect(settings.database_path) as conn:
        cur = await conn.execute(
            "SELECT id, url FROM items WHERE type = 'link' AND (description IS NULL OR TRIM(description) = '')"
        )
        rows = await cur.fetchall()
    for r in rows:
        item_id = int(r["id"])
        url = str(r["url"])
        try:
            videos = await extrair_videos_canal(url, limite=1)
            meta = videos[0] if videos else {"titulo_original": "", "descricao": ""}
            dados = await categorizar_video(
                titulo=str(meta.get("titulo_original") or ""),
                descricao=str(meta.get("descricao") or ""),
            )
            cat_id = await _get_or_create_categoria(dados["equipamento"])
            desc = montar_description(dados)
            title = dados["topico"]
            async with connect(settings.database_path) as conn:
                await conn.execute(
                    "UPDATE items SET category_id = ?, title = ?, description = ? WHERE id = ?",
                    (cat_id, title, desc, item_id),
                )
                await conn.commit()
            ok += 1
        except Exception:
            fail += 1
    return ok, fail


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza vídeos do YouTube para o banco")
    parser.add_argument("--limite", type=int, default=None, help="Quantidade de vídeos a processar")
    parser.add_argument("--reprocessar", action="store_true", help="Reprocessa itens sem description")
    parser.add_argument("--canal", type=str, default=None, help="URL/@handle/UC/UU/playlist")
    parser.add_argument(
        "--categoria-por",
        type=str,
        choices=["marca", "modelo"],
        default="marca",
        help="Agrupar por marca (padrão) ou modelo",
    )
    args = parser.parse_args()

    settings = get_settings()
    await init_db()

    if args.reprocessar:
        ok, fail = await _reprocessar_itens_sem_description()
        print(f"Reprocessados: {ok}, erros: {fail}")
        return

    raw = args.canal or settings.youtube_channel_id
    if not raw:
        raise SystemExit("Defina YOUTUBE_CHANNEL_ID (UC, UU, @handle, playlist) ou use --canal")
    channel_url = _resolver_canal(raw)

    videos = await extrair_videos_canal(channel_url, limite=args.limite)
    inseridos = 0
    duplicatas = 0
    erros = 0
    for v in videos:
        try:
            created, _ = await _processar_video(v, args.categoria_por)
            if created:
                inseridos += 1
            else:
                duplicatas += 1
        except Exception as e:
            try:
                print(f"Erro ao processar {v.get('url')}: {e}")
            except Exception:
                print("Erro ao processar item")
            erros += 1
    print(f"Inseridos: {inseridos}, duplicatas: {duplicatas}, erros: {erros}")


if __name__ == "__main__":
    asyncio.run(main())
