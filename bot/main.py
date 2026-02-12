from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import get_settings
from bot.database import init_db
from bot.handlers.admin import (
    ADD_FILE_WAITING,
    add_category,
    add_file_step1,
    add_file_step2,
    add_link,
    admin_panel,
    delete_category,
    delete_item,
    list_all,
)
from bot.handlers.user import search, send_item, show_categories, show_items, show_main_menu


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.getLogger(__name__).exception("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Ocorreu um erro inesperado. Tente novamente.",
            )
        except Exception:
            return


async def main() -> None:
    settings = get_settings(strict=True)
    await init_db(db_path=settings.database_path)

    app = Application.builder().token(settings.bot_token).build()

    app.add_handler(CommandHandler("start", show_main_menu))
    app.add_handler(CommandHandler("buscar", search))

    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^back_main$"))
    app.add_handler(
        CallbackQueryHandler(show_categories, pattern="^(categorias|back_categories)$")
    )
    app.add_handler(
        CallbackQueryHandler(show_items, pattern=r"^(cat_|back_cat_)\d+$")
    )
    app.add_handler(CallbackQueryHandler(send_item, pattern=r"^item_\d+$"))

    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("addcategoria", add_category))
    app.add_handler(CommandHandler("addlink", add_link))
    app.add_handler(CommandHandler("listar", list_all))
    app.add_handler(CommandHandler("deletar", delete_item))
    app.add_handler(CommandHandler("deletarcategoria", delete_category))

    conv = ConversationHandler(
        entry_points=[CommandHandler("addfile", add_file_step1)],
        states={
            ADD_FILE_WAITING: [
                MessageHandler(filters.Document.ALL | filters.PHOTO, add_file_step2)
            ]
        },
        fallbacks=[],
    )
    app.add_handler(conv)

    app.add_error_handler(on_error)

    logging.getLogger(__name__).info("Bot iniciado")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())

