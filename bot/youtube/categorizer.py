from __future__ import annotations

import json
import logging
import os
import re

from bot.config import get_settings
from bot.youtube.known_models import (
    lookup_brand_from_text,
    validate_model,
    _MODEL_TO_BRAND,
    _normalize_token,
)
from bot.youtube.unknown_tracker import registrar

logger = logging.getLogger(__name__)

STOPWORDS = {
    "de", "e", "na", "no", "o", "a", "do", "da", "para", "em",
    "um", "uma", "com", "por", "se", "ao", "os", "as", "ou",
    "the", "of", "on", "in", "and", "to", "for", "how", "fix",
    "via", "with", "from", "its", "this", "that", "are", "was",
}

_CATEGORY_CACHE: dict[str, dict] = {}
def montar_description(dados: dict) -> str:
    equipamento = dados.get("equipamento") or dados.get("marca") or "Desconhecido"
    tipo = (dados.get("tipo") or "informativo").capitalize()
    nivel = dados.get("nivel") or "Básico"
    tags = dados.get("tags") or ""
    return f"📦 {equipamento}\n📂 {tipo}\n📊 {nivel}\n🏷️ {tags}"


def formatar_mensagem_canal(dados: dict, url: str) -> str:
    marca = dados.get("marca") or "—"
    modelo = dados.get("modelo") or "—"
    equipamento = dados.get("equipamento") or marca
    titulo = dados.get("topico") or "—"
    tipo = (dados.get("tipo") or "informativo").capitalize()
    nivel = dados.get("nivel") or "Básico"

    return (
        f"🖨️ *{equipamento}*\n\n"
        f"📌 *Título:* {titulo}\n"
        f"🏷️ *Marca:* {marca}\n"
        f"🔧 *Modelo:* {modelo}\n"
        f"📂 *Tipo:* {tipo}\n"
        f"📊 *Nível:* {nivel}\n\n"
        f"🔗 [Assistir no YouTube]({url})"
    )


def _normalize_tags(tags: list[str]) -> tuple[list[str], str]:
    seen: set[str] = set()
    norm: list[str] = []
    for t in tags:
        v = re.sub(r"[^\w]", "", str(t).lower())
        if v and len(v) > 1 and v not in seen and v not in STOPWORDS:
            seen.add(v)
            norm.append(v)
    return norm, ", ".join(norm)


def _json_from_text(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
        raise


def _build_equipamento(marca: str, modelo: str | None) -> str:
    if marca and modelo:
        return f"{marca} {modelo}"
    if marca:
        return marca
    return "Desconhecido"


def _fallback_categorizar(titulo: str, descricao: str) -> dict:
    text = f"{titulo} {descricao}"
    marca, modelo_oficial = lookup_brand_from_text(text)

    if not marca:
        for m in ["Epson", "Brother", "HP", "Canon", "Kyocera",
                  "Ricoh", "Lexmark", "Xerox", "Samsung", "OKI"]:
            if m.lower() in text.lower():
                marca = m
                break

    modelo = modelo_oficial
    if not modelo:
        m = re.search(
            r"\b([A-Za-z]{1,5}[-\s]?[A-Z0-9]{2,8}(?:[-\s][A-Z0-9]{2,6})?)\b",
            text,
            re.IGNORECASE,
        )
        if m:
            modelo = validate_model(m.group(1), marca)

    equipamento = _build_equipamento(marca, modelo)
    topico = titulo.strip() or "Vídeo"

    tags_input = []
    if marca:
        tags_input.append(marca)
    if modelo:
        tags_input.append(modelo)
    tags_input += [w for w in topico.split() if len(w) > 2]
    tags_list, tags = _normalize_tags(tags_input)

    return {
        "marca": marca,
        "modelo": modelo,
        "familia": None,
        "equipamento": equipamento,
        "topico": topico,
        "tipo": "informativo",
        "nivel": "Básico",
        "tags_lista": tags_list,
        "tags": tags,
        "resumo": "",
    }


async def categorizar_video(titulo: str, descricao: str = "") -> dict:
    cache_key = titulo.strip().lower()
    if cache_key in _CATEGORY_CACHE:
        return _CATEGORY_CACHE[cache_key]

    settings = get_settings()
    if not settings.anthropic_api_key:
        result = _fallback_categorizar(titulo, descricao)
        _CATEGORY_CACHE[cache_key] = result
        return result

    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    except ImportError:
        logger.error("Biblioteca 'anthropic' não instalada.")
        result = _fallback_categorizar(titulo, descricao)
        _CATEGORY_CACHE[cache_key] = result
        return result
    except Exception as e:
        logger.exception("Erro ao inicializar cliente Anthropic: %s", e)
        result = _fallback_categorizar(titulo, descricao)
        _CATEGORY_CACHE[cache_key] = result
        return result

    model_env = settings.anthropic_model or "claude-3-haiku-20240307"

    sys_prompt = (
        "Você é um assistente que classifica vídeos de manutenção de impressoras. "
        "Responda SOMENTE em JSON minificado, sem explicações, sem markdown.\n\n"
        "Campos: marca, modelo, familia, equipamento, tipo, nivel, tags_lista, resumo.\n\n"
        "REGRAS:\n"
        "- marca: APENAS o fabricante (Epson, Brother, Kyocera, HP, Canon, Ricoh, Samsung, Xerox, OKI, Lexmark). "
        "String vazia se não identificado.\n"
        "- modelo: APENAS o código alfanumérico (ex: L5212, AM-C5000, MA4000cix, HL-L5212DW). "
        "NUNCA use palavras comuns. null se não identificado.\n"
        "- equipamento: SEMPRE 'Marca Modelo'. Se sem modelo, só a marca. NUNCA palavras do título.\n"
        "- tipo: uma de: tutorial, configuração, manutenção, diagnóstico, instalação, informativo.\n"
        "- nivel: uma de: Básico, Intermediário, Avançado.\n"
        "- tags_lista: marca, modelo e palavras-chave. NUNCA artigos ou preposições.\n"
    )

    user_prompt = (
        f"Título: {titulo}\n\n"
        "Exemplo:\n"
        '{"marca":"Brother","modelo":"HL-L5212DW","familia":"HL","equipamento":"Brother HL-L5212DW",'
        '"tipo":"tutorial","nivel":"Básico",'
        '"tags_lista":["brother","hll5212dw","toner","troca"],"resumo":"Tutorial de troca de toner."}'
    )

    try:
        msg = await client.messages.create(
            model=model_env,
            max_tokens=600,
            temperature=0,
            system=sys_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as e:
        logger.error("Erro na chamada Anthropic API: %s", e)
        result = _fallback_categorizar(titulo, descricao)
        _CATEGORY_CACHE[cache_key] = result
        return result

    text = ""
    for part in msg.content:
        if getattr(part, "type", None) == "text":
            text += getattr(part, "text", "")

    try:
        raw = _json_from_text(text)
    except Exception as e:
        logger.warning("Falha ao parsear JSON do Claude: %s | Resposta: %r", e, text)
        result = _fallback_categorizar(titulo, descricao)
        _CATEGORY_CACHE[cache_key] = result
        return result

    marca = str(raw.get("marca") or "").strip()
    modelo_raw = str(raw.get("modelo") or "").strip() or None
    familia = str(raw.get("familia") or "").strip() or None

    modelo = None
    if modelo_raw:
        modelo = validate_model(modelo_raw, marca)
        if not modelo:
            logger.warning(
                "MODELO_DESCONHECIDO | titulo=%r | marca=%r | candidato=%r",
                titulo, marca, modelo_raw,
            )
            registrar(marca, modelo_raw, titulo)

    # Título tem prioridade sobre retorno do Claude
    marca_titulo, modelo_titulo = lookup_brand_from_text(titulo)
    if marca_titulo:
        marca = marca_titulo
    if modelo_titulo:
        modelo = modelo_titulo

    # Fallback: recuperar do dicionário se ainda sem modelo
    if not modelo:
        _, modelo_oficial = lookup_brand_from_text(titulo)
        modelo = modelo_oficial

    # Fallback: recuperar marca pelo modelo
    if not marca and modelo:
        brand_from_model = _MODEL_TO_BRAND.get(_normalize_token(modelo))
        if brand_from_model:
            marca = brand_from_model

    equipamento = _build_equipamento(marca, modelo)

    # topico SEMPRE do título original — nunca do Claude
    topico = titulo.strip() or "Vídeo"

    tipo = str(raw.get("tipo") or "").strip().lower()
    if tipo not in {"tutorial", "configuração", "manutenção", "diagnóstico", "instalação", "informativo"}:
        tipo = "informativo"

    nivel = str(raw.get("nivel") or "").strip()
    if nivel not in {"Básico", "Intermediário", "Avançado"}:
        nivel = "Básico"

    tags_input = [str(t) for t in (raw.get("tags_lista") or [])]
    if marca:
        tags_input.append(marca)
    if modelo:
        tags_input.append(modelo)
    tags_list, tags = _normalize_tags(tags_input)

    result = {
        "marca": marca,
        "modelo": modelo,
        "familia": familia,
        "equipamento": equipamento,
        "topico": topico,
        "tipo": tipo,
        "nivel": nivel,
        "tags_lista": tags_list,
        "tags": tags,
        "resumo": str(raw.get("resumo") or "").strip(),
    }

    _CATEGORY_CACHE[cache_key] = result
    return result
