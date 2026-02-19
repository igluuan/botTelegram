from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot import database
from bot.config import get_settings
from bot.utils import (
    is_valid_http_url,
    looks_like_emoji,
    parse_positive_int,
    split_command_args,
)


ADD_FILE_WAITING = 1


def _is_admin(user_id: int | None) -> bool:
    settings = get_settings()
    if not settings.admin_id:
        return False
    return bool(user_id) and user_id == settings.admin_id


async def _reject_if_not_admin(update: Update) -> bool:
    if _is_admin(update.effective_user.id if update.effective_user else None):
        return False
    if update.message:
        await update.message.reply_text("⛔ Você não tem permissão para usar este comando.")
    return True


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    text = (
        "🛠️ Painel Admin\n\n"
        "Comandos:\n"
        "- /addcategoria <emoji> <nome>\n"
        "- /addlink <categoria_id> <título> <url> [descrição]\n"
        "- /addfile <categoria_id> <título> [descrição]\n"
        "- /listar\n"
        "- /deletar <item_id>\n"
        "- /deletarcategoria <categoria_id>"
    )
    if update.message:
        await update.message.reply_text(text)


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    if not update.message:
        return

    args = split_command_args(update.message.text or "")
    if not args:
        await update.message.reply_text("📁 Uso: /addcategoria <emoji> <nome>")
        return

    emoji = "📁"
    name_parts = args
    if len(args) >= 2 and looks_like_emoji(args[0]):
        emoji = args[0]
        name_parts = args[1:]
    name = " ".join(name_parts).strip()
    if not name:
        await update.message.reply_text("📁 Uso: /addcategoria <emoji> <nome>")
        return

    try:
        cat_id = await database.create_category(name=name, emoji=emoji)
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível criar a categoria.")
        return

    await update.message.reply_text(f"✅ Categoria criada! ID: {cat_id}")


async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    if not update.message:
        return

    args = split_command_args(update.message.text or "")
    if len(args) < 3:
        await update.message.reply_text(
            "🔗 Uso: /addlink <categoria_id> <título> <url> [descrição]"
        )
        return

    try:
        category_id = parse_positive_int(args[0], field_name="categoria_id")
    except ValueError:
        await update.message.reply_text("⚠️ categoria_id inválido.")
        return

    title = args[1].strip()
    url = args[2].strip()
    description = " ".join(args[3:]).strip() if len(args) > 3 else None

    if not title:
        await update.message.reply_text("⚠️ Título inválido.")
        return
    if not is_valid_http_url(url):
        await update.message.reply_text("⚠️ URL inválida. Use http/https.")
        return

    try:
        cat = await database.get_category(category_id=category_id)
        if not cat:
            await update.message.reply_text("⚠️ Categoria não encontrada.")
            return
        item_id = await database.create_link_item(
            category_id=category_id, title=title, url=url, description=description
        )
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível cadastrar o link.")
        return

    await update.message.reply_text(f"✅ Link cadastrado com sucesso! ID: {item_id}")


async def add_file_step1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await _reject_if_not_admin(update):
        return ConversationHandler.END
    if not update.message:
        return ConversationHandler.END
    args = split_command_args(update.message.text or "")
    if len(args) < 2:
        await update.message.reply_text(
            "📎 Uso: /addfile <categoria_id> <título> [descrição]"
        )
        return ConversationHandler.END

    try:
        category_id = parse_positive_int(args[0], field_name="categoria_id")
    except ValueError:
        await update.message.reply_text("⚠️ categoria_id inválido.")
        return ConversationHandler.END

    title = args[1].strip()
    description = " ".join(args[2:]).strip() if len(args) > 2 else None

    if not title:
        await update.message.reply_text("⚠️ Título inválido.")
        return ConversationHandler.END

    try:
        cat = await database.get_category(category_id=category_id)
        if not cat:
            await update.message.reply_text("⚠️ Categoria não encontrada.")
            return ConversationHandler.END
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível validar a categoria.")
        return ConversationHandler.END

    context.user_data["pending_file"] = {
        "category_id": category_id,
        "title": title,
        "description": description,
    }
    await update.message.reply_text("✅ Agora envie o arquivo que deseja cadastrar.")
    return ADD_FILE_WAITING


async def add_file_step2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await _reject_if_not_admin(update):
        return ConversationHandler.END
    if not update.message:
        return ConversationHandler.END
    pending = context.user_data.get("pending_file")
    if not isinstance(pending, dict):
        await update.message.reply_text("⚠️ Nenhum cadastro de arquivo em andamento.")
        return ConversationHandler.END

    settings = get_settings()
    if not settings.storage_channel_id:
        await update.message.reply_text(
            "⚠️ STORAGE_CHANNEL_ID não configurado."
        )
        return ConversationHandler.END

    try:
        stored = await context.bot.forward_message(
            chat_id=settings.storage_channel_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )
        telegram_message_id = int(stored.message_id)
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível armazenar o arquivo.")
        return ConversationHandler.END

    try:
        item_id = await database.create_file_item(
            category_id=int(pending["category_id"]),
            title=str(pending["title"]),
            telegram_message_id=telegram_message_id,
            description=pending.get("description"),
        )
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível salvar no banco.")
        return ConversationHandler.END
    finally:
        context.user_data.pop("pending_file", None)

    await update.message.reply_text(f"✅ Arquivo cadastrado com sucesso! ID: {item_id}")
    return ConversationHandler.END


async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    if not update.message:
        return

    try:
        cats = await database.list_categories_with_counts()
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível listar agora.")
        return
    await update.message.reply_text(database.format_categories_list(cats))


async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    if not update.message:
        return

    args = split_command_args(update.message.text or "")
    if len(args) != 1:
        await update.message.reply_text("🗑️ Uso: /deletar <item_id>")
        return
    try:
        item_id = parse_positive_int(args[0], field_name="item_id")
    except ValueError:
        await update.message.reply_text("⚠️ item_id inválido.")
        return

    try:
        removed = await database.delete_item(item_id=item_id)
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível deletar agora.")
        return

    await update.message.reply_text(
        "✅ Item removido." if removed else "⚠️ Item não encontrado."
    )


async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _reject_if_not_admin(update):
        return
    if not update.message:
        return

    args = split_command_args(update.message.text or "")
    if len(args) != 1:
        await update.message.reply_text("🗑️ Uso: /deletarcategoria <categoria_id>")
        return
    try:
        category_id = parse_positive_int(args[0], field_name="categoria_id")
    except ValueError:
        await update.message.reply_text("⚠️ categoria_id inválido.")
        return

    try:
        removed = await database.delete_category(category_id=category_id)
    except Exception:
        await update.message.reply_text("⚠️ Não foi possível deletar agora.")
        return

    await update.message.reply_text(
        "✅ Categoria removida." if removed else "⚠️ Categoria não encontrada."
    )
