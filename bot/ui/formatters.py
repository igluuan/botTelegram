from __future__ import annotations

from typing import Any


def truncate_text(text: str, limit: int = 60) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 1, 1)].rstrip() + "…"


def item_line(item: Any) -> str:
    prefix = "📎" if item.type == "file" else "🔗"
    description = (item.description or "").strip()
    if description:
        snippet = truncate_text(description, 60)
        return f"{prefix} {item.title} — {snippet}"
    return f"{prefix} {item.title}"


def items_overview(items: list[Any]) -> list[str]:
    return [item_line(item) for item in items]


def build_item_body(item: Any) -> str:
    prefix = "📎" if item.type == "file" else "🔗"
    description = (item.description or "").strip()
    body = f"{prefix} <b>{item.title}</b>"
    if description:
        body += f"\n\n{description}"
    return body
