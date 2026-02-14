from __future__ import annotations

import json
import re
import os
from typing import Any

def montar_description(dados: dict) -> str:
    return f"📦 {dados['equipamento']}\n📊 {dados['nivel']}\n🏷️ {dados['tags']}"


def _normalize_tags(tags: list[str]) -> tuple[list[str], str]:
    seen: set[str] = set()
    norm: list[str] = []
    for t in tags:
        v = re.sub(r"\s+", "", str(t).lower())
        if v and v not in seen:
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


def _fallback_categorizar(titulo: str, descricao: str) -> dict:
    text = f"{titulo} {descricao}"
    lowered = text.lower()
    marcas = ["epson", "brother", "hp", "canon"]
    marca = ""
    for m in marcas:
        if m in lowered:
            marca = m.title()
            break
    modelo = None
    m = re.search(r"\b([A-Z]{1,5}-?[A-Z0-9]{2,8})\b", text)
    if m:
        token = m.group(1)
        if token.lower() not in {"youtube", "video", "manual", "printer"}:
            modelo = token
    if marca and modelo:
        equipamento = f"{marca} {modelo}"
    elif marca:
        equipamento = f"{marca} (modelo não identificado)"
    else:
        equipamento = "Desconhecido (modelo não identificado)"
    topico = titulo.strip() or "Vídeo"
    tags_list, tags = _normalize_tags([t for t in [marca, modelo] if t] + topico.split())
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


async def categorizar_video(titulo: str, descricao: str) -> dict:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return _fallback_categorizar(titulo, descricao)
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
    except Exception:
        return _fallback_categorizar(titulo, descricao)
    desc = (descricao or "")[:2000]
    sys = (
        "Você é um assistente que classifica vídeos de manutenção de impressoras. "
        "Responda SOMENTE em JSON minificado com os campos: "
        "marca, modelo, familia, equipamento, topico, tipo, nivel, tags_lista, resumo. "
        "Regras: marca é apenas fabricante; modelo não inclui a marca; "
        "familia é a linha (ex: EcoTank, WorkForce, MFC, LaserJet Pro); "
        "equipamento é 'Marca Modelo' ou 'Marca (modelo não identificado)' se não houver modelo; "
        "se houver múltiplos modelos, escolha o mais citado ou o do título."
    )
    user = (
        f"Título: {titulo}\n\n"
        f"Descrição:\n{desc}\n\n"
        "Exemplo de resposta:\n"
        '{"marca":"Epson","modelo":"WF-C5890","familia":"WorkForce","equipamento":"Epson WF-C5890",'
        '"topico":"Substituição do kit de manutenção","tipo":"troca de peça","nivel":"Intermediario",'
        '"tags_lista":["epson","wfc5890","workforce","kitmanutenção"],"resumo":"..."}'
    )
    try:
        msg = await client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=800,
            temperature=0,
            system=sys,
            messages=[{"role": "user", "content": user}],
        )
    except Exception:
        return _fallback_categorizar(titulo, descricao)
    text = ""
    for part in msg.content:
        if getattr(part, "type", None) == "text":
            text += getattr(part, "text", "")
    raw = _json_from_text(text)
    marca = str(raw.get("marca") or "").strip()
    modelo = str(raw.get("modelo") or "").strip() or None
    familia = str(raw.get("familia") or "").strip() or None
    equipamento = str(raw.get("equipamento") or "").strip()
    topico = str(raw.get("topico") or titulo).strip()
    tipo = str(raw.get("tipo") or "").strip() or "informativo"
    nivel = str(raw.get("nivel") or "").strip() or "Básico"
    tags_list = raw.get("tags_lista") or []
    if not equipamento:
        if marca and modelo:
            equipamento = f"{marca} {modelo}"
        elif marca:
            equipamento = f"{marca} (modelo não identificado)"
        else:
            equipamento = "Desconhecido (modelo não identificado)"
    norm_list, tags = _normalize_tags([*tags_list, marca, modelo or "", familia or ""])
    return {
        "marca": marca,
        "modelo": modelo,
        "familia": familia,
        "equipamento": equipamento,
        "topico": topico,
        "tipo": tipo,
        "nivel": nivel,
        "tags_lista": norm_list,
        "tags": tags,
        "resumo": str(raw.get("resumo") or "").strip(),
    }
