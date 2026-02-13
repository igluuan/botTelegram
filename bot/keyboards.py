from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models import Category, Item


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📂 Ver Categorias", callback_data="categorias_1")],
            [
                InlineKeyboardButton("⭐ Favoritos", callback_data="favoritos_1"),
                InlineKeyboardButton("🕘 Recentes", callback_data="recentes_1"),
            ],
        ]
    )


def categories_menu(
    categories_with_counts: list[tuple[Category, int]], page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for cat, count in categories_with_counts:
        rows.append(
            [
                InlineKeyboardButton(
                    f"{cat.emoji} {cat.name} ({count})",
                    callback_data=f"cat_{cat.id}_1",
                )
            ]
        )

    pag_row = []
    if page > 1:
        pag_row.append(
            InlineKeyboardButton("⬅️", callback_data=f"categorias_{page - 1}")
        )
    
    if total_pages > 1:
        pag_row.append(
            InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop")
        )

    if page < total_pages:
        pag_row.append(
            InlineKeyboardButton("➡️", callback_data=f"categorias_{page + 1}")
        )
    
    if pag_row:
        rows.append(pag_row)

    rows.append([InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def items_menu(
    items: list[Item], category_id: int, page: int, total_pages: int, back_data: str
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for it in items:
        prefix = "📎" if it.type == "file" else "🔗"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{prefix} {it.title}", callback_data=f"item_{it.id}"
                )
            ]
        )

    pag_row = []
    if page > 1:
        pag_row.append(
            InlineKeyboardButton(
                "⬅️", callback_data=f"cat_{category_id}_{page - 1}"
            )
        )
    
    if total_pages > 1:
        pag_row.append(
            InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop")
        )

    if page < total_pages:
        pag_row.append(
            InlineKeyboardButton(
                "➡️", callback_data=f"cat_{category_id}_{page + 1}"
            )
        )

    if pag_row:
        rows.append(pag_row)

    rows.append(
        [InlineKeyboardButton("🔍 Buscar nesta categoria", callback_data=f"buscarcat_{category_id}")]
    )
    rows.append([InlineKeyboardButton("⬅️ Voltar", callback_data=back_data)])
    return InlineKeyboardMarkup(rows)


def paginated_items_menu(
    items: list[Item],
    *,
    page: int,
    total_pages: int,
    back_data: str,
    page_callback_prefix: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for it in items:
        prefix = "📎" if it.type == "file" else "🔗"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{prefix} {it.title}", callback_data=f"item_{it.id}"
                )
            ]
        )

    pag_row = []
    if page > 1:
        pag_row.append(
            InlineKeyboardButton("⬅️", callback_data=f"{page_callback_prefix}_{page - 1}")
        )
    if total_pages > 1:
        pag_row.append(
            InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop")
        )
    if page < total_pages:
        pag_row.append(
            InlineKeyboardButton("➡️", callback_data=f"{page_callback_prefix}_{page + 1}")
        )
    if pag_row:
        rows.append(pag_row)

    rows.append([InlineKeyboardButton("⬅️ Voltar", callback_data=back_data)])
    return InlineKeyboardMarkup(rows)


def item_actions_menu(
    *,
    item_id: int,
    is_favorite: bool,
    back_data: str,
    url: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if url:
        rows.append([InlineKeyboardButton("🔗 Abrir Link", url=url)])
    fav_label = "⭐ Remover dos favoritos" if is_favorite else "⭐ Favoritar"
    fav_action = "unfav" if is_favorite else "fav"
    rows.append([InlineKeyboardButton(fav_label, callback_data=f"{fav_action}_{item_id}")])
    rows.append([InlineKeyboardButton("⬅️ Voltar", callback_data=back_data)])
    return InlineKeyboardMarkup(rows)
