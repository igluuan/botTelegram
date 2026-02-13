from __future__ import annotations

import math
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import database
from bot.config import get_settings
from bot.keyboards import (
    categories_menu,
    items_menu,
    item_actions_menu,
    main_menu,
    paginated_items_menu,
)
from bot.utils import build_item_body, items_overview, parse_positive_int


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🤖 Bem-vindo!\n\n"
        "Use os botões abaixo para navegar pelas categorias.\n"
        "Para buscar por título: /buscar <termo>\n"
        "Para buscar por categoria: /buscarcat <categoria_id> <termo>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=main_menu())
        return
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return

    data = update.callback_query.data or ""
    page = 1
    if "_" in data and not data.startswith("back"):
        try:
            page = int(data.split("_")[-1])
        except ValueError:
            page = 1

    await update.callback_query.answer(text="⏳ Carregando...")

    try:
        limit = 10
        total_count = await database.count_categories()
        total_pages = math.ceil(total_count / limit)
        if page > total_pages and total_pages > 0:
            page = total_pages

        categories_with_counts = await database.list_categories_with_counts_paged(
            page=page, limit=limit
        )
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar as categorias agora."
        )
        return

    if not categories_with_counts and page == 1:
        await update.callback_query.edit_message_text(
            "📭 Ainda não há categorias cadastradas.",
            reply_markup=categories_menu([], page=1, total_pages=1),
        )
        return

    total_pages_display = max(total_pages, 1)
    lines = [f"📚 Categorias (total {total_count})", ""]
    lines.extend(
        [f"{cat.emoji} {cat.name} — {count} item(ns)" for cat, count in categories_with_counts]
    )
    lines.extend(["", "Selecione uma categoria:"])
    await update.callback_query.edit_message_text(
        "\n".join(lines),
        reply_markup=categories_menu(
            categories_with_counts, page=page, total_pages=total_pages_display
        ),
    )


async def show_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    await update.callback_query.answer(text="⏳ Carregando...")

    parts = data.split("_")
    category_id_str = parts[1] if len(parts) > 1 else "0"
    page_str = parts[2] if len(parts) > 2 else "1"

    try:
        category_id = int(category_id_str)
        page = int(page_str)
    except ValueError:
        await update.callback_query.edit_message_text("⚠️ Dados inválidos.")
        return

    try:
        category = await database.get_category(category_id=category_id)
        if not category:
            await update.callback_query.edit_message_text("⚠️ Categoria não encontrada.")
            return

        limit = 10
        total_count = await database.count_items_by_category(category_id=category_id)
        total_pages = math.ceil(total_count / limit)
        if page > total_pages and total_pages > 0:
            page = total_pages

        items = await database.list_items_by_category(
            category_id=category_id, page=page, limit=limit
        )
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar os itens agora."
        )
        return

    if not items and page == 1:
        await update.callback_query.edit_message_text(
            f"📭 Nenhum item na categoria {category.emoji} {category.name}.",
            reply_markup=items_menu([], category_id, 1, 1, back_data="back_categories"),
        )
        return

    total_pages_display = max(total_pages, 1)
    context.user_data["last_back_data"] = f"cat_{category_id}_{page}"
    lines = [f"📁 {category.emoji} {category.name}", f"Itens: {total_count}", ""]
    lines.extend(items_overview(items))
    lines.extend(["", "Selecione um item:"])
    await update.callback_query.edit_message_text(
        "\n".join(lines),
        reply_markup=items_menu(
            items,
            category_id=category_id,
            page=page,
            total_pages=total_pages_display,
            back_data="back_categories",
        ),
    )


async def send_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    await update.callback_query.answer(text="⏳ Carregando...")
    data = update.callback_query.data or ""
    try:
        item_id = parse_positive_int(data.split("_")[-1], field_name="item_id")
    except ValueError:
        await update.callback_query.edit_message_text("⚠️ Item inválido.")
        return

    try:
        item = await database.get_item(item_id=item_id)
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar este item agora."
        )
        return

    if not item:
        await update.callback_query.edit_message_text("⚠️ Item não encontrado.")
        return

    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        await database.add_history_entry(user_id=user_id, item_id=item.id)

    back_data = context.user_data.get("last_back_data") or f"back_cat_{item.category_id}"
    is_favorite = False
    if user_id:
        is_favorite = await database.is_favorite(user_id=user_id, item_id=item.id)

    if item.type == "link":
        body = build_item_body(item)
        await update.callback_query.edit_message_text(
            body,
            reply_markup=item_actions_menu(
                item_id=item.id,
                is_favorite=is_favorite,
                back_data=back_data,
                url=item.url or "",
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    settings = get_settings()
    if not settings.storage_channel_id:
        await update.callback_query.edit_message_text(
            "⚠️ Storage do canal não configurado (STORAGE_CHANNEL_ID)."
        )
        return
    if not item.telegram_message_id:
        await update.callback_query.edit_message_text("⚠️ Arquivo indisponível.")
        return

    try:
        await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=settings.storage_channel_id,
            message_id=item.telegram_message_id,
        )
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível enviar o arquivo agora."
        )
        return

    body = build_item_body(item)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=body,
        reply_markup=item_actions_menu(
            item_id=item.id, is_favorite=is_favorite, back_data=back_data
        ),
        parse_mode=ParseMode.HTML,
    )


async def _render_search_results_message(
    *,
    edit_message,
    term: str,
    page: int,
    category_id: int | None,
    back_data: str,
) -> None:
    limit = 10
    if category_id is None:
        total_count = await database.count_search_items(term=term)
        total_pages = math.ceil(total_count / limit)
        items = await database.search_items(term=term, page=page, limit=limit)
        title = f"🔎 Busca: {term}"
    else:
        total_count = await database.count_search_items_by_category(
            category_id=category_id, term=term
        )
        total_pages = math.ceil(total_count / limit)
        category = await database.get_category(category_id=category_id)
        name = category.name if category else f"Categoria {category_id}"
        title = f"🔎 Busca em {name}: {term}"
        items = await database.search_items_by_category(
            category_id=category_id, term=term, page=page, limit=limit
        )

    total_pages_display = max(total_pages, 1)
    lines = [f"{title}", f"Resultados: {total_count}"]
    if total_pages_display > 1:
        lines.append(f"Página: {page}/{total_pages_display}")
    lines.append("")
    if items:
        lines.extend(items_overview(items))
        lines.extend(["", "Toque em um item para abrir:"])
    else:
        lines.append("📭 Nenhum resultado encontrado.")

    await edit_message(
        "\n".join(lines),
        reply_markup=paginated_items_menu(
            items,
            page=page,
            total_pages=total_pages_display,
            back_data=back_data,
            page_callback_prefix="buscar",
        ),
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    term = " ".join(context.args or []).strip()
    if not term:
        await update.message.reply_text("🔍 Uso: /buscar <termo>")
        return

    msg = await update.message.reply_text("🔎 Buscando...")
    context.user_data["search_context"] = {"term": term, "category_id": None}
    context.user_data["last_back_data"] = "buscar_1"
    try:
        await _render_search_results_message(
            edit_message=msg.edit_text,
            term=term,
            page=1,
            category_id=None,
            back_data="back_main",
        )
    except Exception:
        await msg.edit_text("⚠️ Não foi possível buscar agora.")


async def search_by_category_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message:
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("🔍 Uso: /buscarcat <categoria_id> <termo>")
        return

    try:
        category_id = parse_positive_int(args[0], field_name="categoria_id")
    except ValueError:
        await update.message.reply_text("⚠️ categoria_id inválido.")
        return

    term = " ".join(args[1:]).strip()
    if not term:
        await update.message.reply_text("🔍 Uso: /buscarcat <categoria_id> <termo>")
        return

    category = await database.get_category(category_id=category_id)
    if not category:
        await update.message.reply_text("⚠️ Categoria não encontrada.")
        return

    msg = await update.message.reply_text("🔎 Buscando...")
    context.user_data["search_context"] = {"term": term, "category_id": category_id}
    context.user_data["last_back_data"] = "buscar_1"
    try:
        await _render_search_results_message(
            edit_message=msg.edit_text,
            term=term,
            page=1,
            category_id=category_id,
            back_data=f"cat_{category_id}_1",
        )
    except Exception:
        await msg.edit_text("⚠️ Não foi possível buscar agora.")


async def search_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    try:
        page = int(data.split("_")[-1])
    except ValueError:
        await update.callback_query.answer()
        return

    search_context = context.user_data.get("search_context")
    if not isinstance(search_context, dict):
        await update.callback_query.answer(text="Busca expirada.")
        return

    term = str(search_context.get("term", "")).strip()
    category_id = search_context.get("category_id")
    if not term:
        await update.callback_query.answer(text="Busca expirada.")
        return

    await update.callback_query.answer(text="⏳ Carregando...")
    try:
        await _render_search_results_message(
            edit_message=update.callback_query.edit_message_text,
            term=term,
            page=page,
            category_id=category_id if isinstance(category_id, int) else None,
            back_data="back_main" if category_id is None else f"cat_{category_id}_1",
        )
        context.user_data["last_back_data"] = f"buscar_{page}"
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar os resultados agora."
        )


async def start_category_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    try:
        category_id = int(data.split("_")[-1])
    except ValueError:
        await update.callback_query.answer()
        return

    category = await database.get_category(category_id=category_id)
    if not category:
        await update.callback_query.answer(text="Categoria inválida.")
        return

    context.user_data["pending_category_search_id"] = category_id
    context.user_data["pending_category_search_name"] = category.name
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        f"🔍 Digite o termo para buscar em {category.name}:"
    )


async def handle_pending_category_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message:
        return
    category_id = context.user_data.pop("pending_category_search_id", None)
    category_name = context.user_data.pop("pending_category_search_name", None)
    if not isinstance(category_id, int):
        return

    term = (update.message.text or "").strip()
    if not term:
        await update.message.reply_text("🔍 Digite um termo válido para buscar.")
        return

    msg = await update.message.reply_text("🔎 Buscando...")
    context.user_data["search_context"] = {"term": term, "category_id": category_id}
    context.user_data["last_back_data"] = "buscar_1"
    name = category_name or f"Categoria {category_id}"
    try:
        await _render_search_results_message(
            edit_message=msg.edit_text,
            term=term,
            page=1,
            category_id=category_id,
            back_data=f"cat_{category_id}_1",
        )
    except Exception:
        await msg.edit_text(f"⚠️ Não foi possível buscar em {name}.")


async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    try:
        page = int(data.split("_")[-1])
    except ValueError:
        page = 1

    await update.callback_query.answer(text="⏳ Carregando...")
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await update.callback_query.edit_message_text("⚠️ Usuário inválido.")
        return

    try:
        limit = 10
        total_count = await database.count_favorites(user_id=user_id)
        total_pages = math.ceil(total_count / limit)
        if page > total_pages and total_pages > 0:
            page = total_pages
        items = await database.list_favorites(user_id=user_id, page=page, limit=limit)
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar seus favoritos agora."
        )
        return

    total_pages_display = max(total_pages, 1)
    context.user_data["last_back_data"] = f"favoritos_{page}"
    lines = [f"⭐ Favoritos (total {total_count})"]
    if total_pages_display > 1:
        lines.append(f"Página: {page}/{total_pages_display}")
    lines.append("")
    if items:
        lines.extend(items_overview(items))
        lines.extend(["", "Toque em um item para abrir:"])
    else:
        lines.append("📭 Você ainda não tem favoritos.")

    await update.callback_query.edit_message_text(
        "\n".join(lines),
        reply_markup=paginated_items_menu(
            items,
            page=page,
            total_pages=total_pages_display,
            back_data="back_main",
            page_callback_prefix="favoritos",
        ),
    )


async def show_recentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    try:
        page = int(data.split("_")[-1])
    except ValueError:
        page = 1

    await update.callback_query.answer(text="⏳ Carregando...")
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await update.callback_query.edit_message_text("⚠️ Usuário inválido.")
        return

    try:
        limit = 10
        total_count = await database.count_history(user_id=user_id)
        total_pages = math.ceil(total_count / limit)
        if page > total_pages and total_pages > 0:
            page = total_pages
        items = await database.list_history(user_id=user_id, page=page, limit=limit)
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar seus recentes agora."
        )
        return

    total_pages_display = max(total_pages, 1)
    context.user_data["last_back_data"] = f"recentes_{page}"
    lines = [f"🕘 Recentes (total {total_count})"]
    if total_pages_display > 1:
        lines.append(f"Página: {page}/{total_pages_display}")
    lines.append("")
    if items:
        lines.extend(items_overview(items))
        lines.extend(["", "Toque em um item para abrir:"])
    else:
        lines.append("📭 Você ainda não abriu nenhum item.")

    await update.callback_query.edit_message_text(
        "\n".join(lines),
        reply_markup=paginated_items_menu(
            items,
            page=page,
            total_pages=total_pages_display,
            back_data="back_main",
            page_callback_prefix="recentes",
        ),
    )


async def toggle_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    parts = data.split("_")
    if len(parts) != 2:
        await update.callback_query.answer()
        return
    action, item_id_str = parts
    try:
        item_id = int(item_id_str)
    except ValueError:
        await update.callback_query.answer()
        return

    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await update.callback_query.answer()
        return

    try:
        if action == "fav":
            await database.add_favorite(user_id=user_id, item_id=item_id)
            await update.callback_query.answer(text="Adicionado aos favoritos.")
        else:
            await database.remove_favorite(user_id=user_id, item_id=item_id)
            await update.callback_query.answer(text="Removido dos favoritos.")
    except Exception:
        await update.callback_query.answer(text="Não foi possível atualizar.")
        return

    item = await database.get_item(item_id=item_id)
    if not item:
        return
    is_favorite = await database.is_favorite(user_id=user_id, item_id=item_id)
    back_data = context.user_data.get("last_back_data") or f"back_cat_{item.category_id}"
    body = build_item_body(item)
    await update.callback_query.edit_message_text(
        body,
        reply_markup=item_actions_menu(
            item_id=item.id,
            is_favorite=is_favorite,
            back_data=back_data,
            url=item.url or "",
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
