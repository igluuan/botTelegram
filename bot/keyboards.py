from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models import Category, Item


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📂 Ver Categorias", callback_data="categorias")]]
    )


def categories_menu(categories: list[Category]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for cat in categories:
        rows.append(
            [
                InlineKeyboardButton(
                    f"{cat.emoji} {cat.name}", callback_data=f"cat_{cat.id}"
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def items_menu(items: list[Item], *, back_data: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for it in items:
        prefix = "📎" if it.type == "file" else "🔗"
        rows.append(
            [InlineKeyboardButton(f"{prefix} {it.title}", callback_data=f"item_{it.id}")]
        )
    rows.append(
        [InlineKeyboardButton("⬅️ Voltar", callback_data=back_data)]
    )
    return InlineKeyboardMarkup(rows)


def link_menu(*, url: str, back_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔗 Abrir Link", url=url)],
            [InlineKeyboardButton("⬅️ Voltar", callback_data=back_data)],
        ]
    )
