from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models import Category, Item


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📂 Categorias", callback_data="marcas")],
            [
                InlineKeyboardButton("⭐ Favoritos", callback_data="favoritos_1"),
                InlineKeyboardButton("🕘 Recentes", callback_data="recentes_1"),
            ],
        ]
    )


def marcas_menu(marcas: list[str]) -> InlineKeyboardMarkup:
    rows = []
    current_row = []
    for m in marcas:
        current_row.append(InlineKeyboardButton(m, callback_data=f"marca_{m}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([InlineKeyboardButton("🔙 Voltar", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def subcategorias_menu(marca: str, subcategorias: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(s, callback_data=f"subcat|{marca}|{s}")]
        for s in subcategorias
    ]
    rows.append([InlineKeyboardButton("🔙 Voltar", callback_data="marcas")])
    return InlineKeyboardMarkup(rows)


def _build_pagination_row(
    page: int, total_pages: int, callback_prefix: str
) -> list[InlineKeyboardButton]:
    row = []
    if page > 1:
        row.append(
            InlineKeyboardButton(
                "⬅️ Anterior", callback_data=f"{callback_prefix}_{page - 1}"
            )
        )

    if total_pages > 1:
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))

    if page < total_pages:
        row.append(
            InlineKeyboardButton(
                "Próxima ➡️", callback_data=f"{callback_prefix}_{page + 1}"
            )
        )
    return row


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

    pag_row = _build_pagination_row(page, total_pages, "categorias")
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

    pag_row = _build_pagination_row(page, total_pages, f"cat_{category_id}")
    if pag_row:
        rows.append(pag_row)

    rows.append(
        [
            InlineKeyboardButton(
                "🔍 Buscar nesta categoria", callback_data=f"buscarcat_{category_id}"
            )
        ]
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

    pag_row = _build_pagination_row(page, total_pages, page_callback_prefix)
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
    fav_label = "⭐ Remover dos favoritos" if is_favorite else "⭐ Salvar nos favoritos"
    fav_action = "unfav" if is_favorite else "fav"
    rows.append([InlineKeyboardButton(fav_label, callback_data=f"{fav_action}_{item_id}")])
    rows.append([InlineKeyboardButton("🔙 Voltar aos resultados", callback_data=back_data)])
    return InlineKeyboardMarkup(rows)
