from __future__ import annotations

import html


def formatar_mensagem_canal(dados: dict, url: str) -> str:
    equipamento = html.escape(str(dados.get("equipamento") or "—"))
    titulo = html.escape(str(dados.get("topico") or "—"))
    marca = html.escape(str(dados.get("marca") or "—"))
    modelo = html.escape(str(dados.get("modelo") or "—"))
    tipo = str(dados.get("tipo") or "informativo").replace("_", " ").strip().title()
    tipo = html.escape(tipo or "Informativo")
    nivel = html.escape(str(dados.get("nivel") or "Básico"))
    safe_url = html.escape(url, quote=True)

    return (
        f"🖨️ <b>{equipamento}</b>\n\n"
        f"📌 <b>Título:</b> {titulo}\n"
        f"🏷️ <b>Marca:</b> {marca}\n"
        f"🔧 <b>Modelo:</b> {modelo}\n"
        f"📂 <b>Tipo:</b> {tipo}\n"
        f"📊 <b>Nível:</b> {nivel}\n\n"
        f"🔗 <a href=\"{safe_url}\">Assistir no YouTube</a>"
    )

