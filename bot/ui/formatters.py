from __future__ import annotations

from typing import Any


def truncate_text(text: str, limit: int = 60) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 1, 1)].rstrip() + "…"


def item_line(item: Any) -> str:
    prefix = "📎" if item.type == "file" else "🔗"
    marca = (getattr(item, "marca", "") or "").strip()
    modelo = (getattr(item, "modelo", "") or "").strip()
    badge = f"{marca} {modelo}".strip()
    if badge:
        return f"{prefix} {badge} · {item.title}"
    return f"{prefix} {item.title}"


def items_overview(items: list[Any]) -> list[str]:
    lines = []
    for item in items:
        lines.append(item_line(item))
    return lines


def build_item_body(item: Any) -> str:
    prefix = "▶️" if item.type == "file" else "🔗"
    marca = (getattr(item, "marca", "") or "").strip()
    modelo = (getattr(item, "modelo", "") or "").strip()
    tipo = (getattr(item, "tipo", "") or "").strip().capitalize()
    
    badges = " · ".join(filter(None, [marca, modelo, tipo]))
    body = f"{prefix} <b>{item.title}</b>"
    if badges:
        body += f"\n\n🏷️ {badges}"
    
    description = (item.description or "").strip()
    if description:
        body += f"\n{'─' * 20}\n{description}"
    return body
