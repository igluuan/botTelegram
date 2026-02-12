from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import database
from bot.config import get_settings
from bot.keyboards import categories_menu, items_menu, link_menu, main_menu
from bot.utils import parse_positive_int


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🤖 Bem-vindo!\n\n"
        "Use os botões abaixo para navegar pelas categorias.\n"
        "Para buscar por título: /buscar <termo>"
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
    await update.callback_query.answer()
    try:
        categories = await database.list_categories()
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar as categorias agora."
        )
        return

    if not categories:
        await update.callback_query.edit_message_text(
            "📭 Ainda não há categorias cadastradas.", reply_markup=categories_menu([])
        )
        return
    await update.callback_query.edit_message_text(
        "📂 Selecione uma categoria:", reply_markup=categories_menu(categories)
    )


async def show_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    data = update.callback_query.data or ""
    await update.callback_query.answer()

    try:
        category_id = parse_positive_int(data.split("_")[-1], field_name="categoria_id")
    except ValueError:
        await update.callback_query.edit_message_text("⚠️ Categoria inválida.")
        return

    try:
        category = await database.get_category(category_id=category_id)
        if not category:
            await update.callback_query.edit_message_text("⚠️ Categoria não encontrada.")
            return
        items = await database.list_items_by_category(category_id=category_id)
    except Exception:
        await update.callback_query.edit_message_text(
            "⚠️ Não foi possível carregar os itens agora."
        )
        return

    if not items:
        await update.callback_query.edit_message_text(
            f"📭 Nenhum item na categoria {category.emoji} {category.name}.",
            reply_markup=items_menu([], back_data="back_categories"),
        )
        return

    await update.callback_query.edit_message_text(
        f"📁 {category.emoji} {category.name}\n\nSelecione um item:",
        reply_markup=items_menu(items, back_data="back_categories"),
    )


async def send_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    await update.callback_query.answer()
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

    back_data = f"back_cat_{item.category_id}"
    if item.type == "link":
        description = (item.description or "").strip()
        body = f"🔗 <b>{item.title}</b>"
        if description:
            body += f"\n\n{description}"
        await update.callback_query.edit_message_text(
            body,
            reply_markup=link_menu(url=item.url or "", back_data=back_data),
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



async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    term = " ".join(context.args or []).strip()
    if not term:
        await update.message.reply_text("🔍 Uso: /buscar <termo>")
        return

    try:
        results = await database.search_items(term=term, limit=20)
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível buscar agora.")
        return

    if not results:
        await update.message.reply_text("📭 Nenhum resultado encontrado.")
        return

    lines = [f"🔎 Resultados para: {term}", "", "Toque em um item para abrir:"]
    await update.message.reply_text(
        "\n".join(lines), reply_markup=items_menu(results, back_data="back_main")
    )
