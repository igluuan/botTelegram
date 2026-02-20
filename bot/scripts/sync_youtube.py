from __future__ import annotations

import argparse
import asyncio
from datetime import date
import logging
import re

import httpx

from bot.config import get_settings
from bot.db.connection import connect
from bot.db.schema import init_db
from bot import database
from bot.youtube.extractor import extrair_lista_canal_flat, extrair_video_full
from bot.youtube.categorizer import categorizar_video, montar_description
from bot.youtube.formatter import formatar_mensagem_canal


_SEM = asyncio.Semaphore(5)


def normalize_youtube_url(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url


def _extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url or "")
    if match:
        return str(match.group(1))
    return None


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


async def _get_config_value(*, key: str, db_path: str) -> str | None:
    async with connect(db_path) as conn:
        cur = await conn.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = await cur.fetchone()
        return str(row["value"]) if row else None


async def _set_config_value(*, key: str, value: str, db_path: str) -> None:
    async with connect(db_path) as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO config(key, value) VALUES (?, ?)", (key, value)
        )
        await conn.commit()


async def publicar_no_canal(
    *, bot_token: str, channel_id: int, texto: str
) -> int | None:
    logger = logging.getLogger(__name__)
    if not bot_token or not channel_id:
        logger.warning(
            "publicar_no_canal: bot_token ou channel_id ausentes (bot_token_presente=%s, channel_id=%s)",
            bool(bot_token),
            channel_id,
        )
        return None
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        status = resp.status_code
        body = resp.text
        try:
            data = resp.json()
        except Exception:
            logger.error(
                "publicar_no_canal: resposta inválida do Telegram (status=%s, body=%r)",
                status,
                body[:500],
            )
            return None
        if data.get("ok"):
            try:
                return int(data["result"]["message_id"])
            except Exception:
                logger.error(
                    "publicar_no_canal: resposta ok porém sem message_id válido (status=%s, data_keys=%s)",
                    status,
                    list(data.keys()),
                )
                return None
        logger.error(
            "publicar_no_canal: erro ao enviar mensagem (status=%s, error_code=%s, description=%r)",
            status,
            data.get("error_code"),
            data.get("description"),
        )
    return None


async def _processar_video(
    video: dict, categoria_por: str, *, bot_token: str, channel_id: int
) -> tuple[bool, str | None]:
    video_id = str(video.get("video_id") or "").strip() or None
    url = normalize_youtube_url(str(video["url"]))
    if video_id and await database.get_item_by_video_id(video_id=video_id):
        return False, None
    if await database.get_item_by_url(url=url):
        return False, None
    dados = await categorizar_video(
        titulo=str(video.get("titulo_original") or ""),
        descricao=str(video.get("descricao") or ""),
    )
    cat_name = _nome_categoria(dados, categoria_por)
    cat_id = await _get_or_create_categoria(cat_name)
    desc = montar_description(dados)
    texto = formatar_mensagem_canal(dados, url)
    telegram_message_id = await publicar_no_canal(
        bot_token=bot_token, channel_id=channel_id, texto=texto
    )
    marca = str(dados.get("marca") or "").strip() or None
    modelo = str(dados.get("modelo") or "").strip() or None
    tipo = str(dados.get("tipo") or "").strip() or None
    nivel = str(dados.get("nivel") or "").strip() or None
    if telegram_message_id:
        await database.create_file_item(
            category_id=cat_id,
            title=str(video.get("titulo_original") or "").strip(),
            telegram_message_id=telegram_message_id,
            description=desc,
            video_id=video_id,
            marca=marca,
            modelo=modelo,
            tipo=tipo,
            nivel=nivel,
            youtube_url=url,
        )
    else:
        await database.create_link_item(
            category_id=cat_id,
            title=str(video.get("titulo_original") or "").strip(),
            url=url,
            description=desc,
            video_id=video_id,
            marca=marca,
            modelo=modelo,
            tipo=tipo,
            nivel=nivel,
            youtube_url=url,
        )
    return True, cat_name


async def _processar_com_semaforo(
    video: dict, categoria_por: str, *, bot_token: str, channel_id: int
) -> tuple[bool, str | None]:
    async with _SEM:
        return await _processar_video(
            video, categoria_por, bot_token=bot_token, channel_id=channel_id
        )


async def _reprocessar_itens_sem_description(*, categoria_por: str) -> tuple[int, int]:
    ok = 0
    fail = 0
    settings = get_settings()
    async with connect(settings.database_path) as conn:
        cur = await conn.execute(
            """
            SELECT id, url, video_id, youtube_url
            FROM items
            WHERE type = 'link' AND (description IS NULL OR TRIM(description) = '')
            """
        )
        rows = await cur.fetchall()
    for r in rows:
        item_id = int(r["id"])
        url = str(r["youtube_url"] or r["url"] or "")
        video_id = str(r["video_id"] or "").strip() or _extract_video_id(url)
        try:
            meta = await extrair_video_full(video_id) if video_id else {}
            dados = await categorizar_video(
                titulo=str(meta.get("titulo_original") or ""),
                descricao=str(meta.get("descricao") or ""),
            )
            cat_name = _nome_categoria(dados, categoria_por)
            cat_id = await _get_or_create_categoria(cat_name)
            desc = montar_description(dados)
            title = str(meta.get("titulo_original") or "").strip()
            marca = str(dados.get("marca") or "").strip() or None
            modelo = str(dados.get("modelo") or "").strip() or None
            tipo = str(dados.get("tipo") or "").strip() or None
            nivel = str(dados.get("nivel") or "").strip() or None
            async with connect(settings.database_path) as conn:
                await conn.execute(
                    """
                    UPDATE items
                    SET category_id = ?,
                        title = ?,
                        description = ?,
                        video_id = ?,
                        marca = ?,
                        modelo = ?,
                        tipo = ?,
                        nivel = ?,
                        youtube_url = ?
                    WHERE id = ?
                    """,
                    (cat_id, title, desc, video_id, marca, modelo, tipo, nivel, url, item_id),
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
        ok, fail = await _reprocessar_itens_sem_description(categoria_por=args.categoria_por)
        print(f"Reprocessados: {ok}, erros: {fail}")
        return

    raw = args.canal or settings.youtube_channel_id
    if not raw:
        raise SystemExit("Defina YOUTUBE_CHANNEL_ID (UC, UU, @handle, playlist) ou use --canal")
    channel_url = _resolver_canal(raw)

    last_sync_date = await _get_config_value(
        key="last_sync_date", db_path=settings.database_path
    )
    videos = await extrair_lista_canal_flat(
        channel_url, limite=args.limite, last_sync_date=last_sync_date
    )
    inseridos = 0
    duplicatas = 0
    erros = 0
    results = await asyncio.gather(
        *[
            _processar_com_semaforo(
                v,
                args.categoria_por,
                bot_token=settings.bot_token,
                channel_id=settings.storage_channel_id,
            )
            for v in videos
        ],
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            erros += 1
            continue
        created, _ = r
        if created:
            inseridos += 1
        else:
            duplicatas += 1
    await _set_config_value(
        key="last_sync_date",
        value=date.today().strftime("%Y%m%d"),
        db_path=settings.database_path,
    )
    print(f"Inseridos: {inseridos}, duplicatas: {duplicatas}, erros: {erros}")


if __name__ == "__main__":
    asyncio.run(main())
