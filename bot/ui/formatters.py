from __future__ import annotations

from typing import Any


def truncate_text(text: str, limit: int = 60) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 1, 1)].rstrip() + "…"


def item_line(item: Any) -> str:
    prefix = "📎" if item.type == "file" else "🔗"
    line = f"{prefix} {item.title}"
    if item.description and item.description.strip():
        # Normaliza espaços na descrição
        desc = " ".join(item.description.strip().split())
        line += f" — {desc}"
    return line


def items_overview(items: list[Any]) -> list[str]:
    return []  

def build_item_body(item: Any) -> str:
    prefix = "📎" if item.type == "file" else "🔗"
    description = (item.description or "").strip()
    body = f"{prefix} <b>{item.title}</b>"
    if description:
        body += f"\n\n{description}"
    return body
