from __future__ import annotations

import asyncio
import logging
from logging.handlers import RotatingFileHandler

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
from bot.db.repository import configure
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
from bot.handlers.user import (
    handle_pending_category_search,
    noop,
    search,
    search_by_category_command,
    search_pagination,
    send_item,
    show_categories,
    show_favorites,
    show_items,
    show_main_menu,
    show_recentes,
    start_category_search,
    toggle_favorite,
    WAITING_SEARCH_TERM,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            "bot.log", maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
        ),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.getLogger(__name__).exception(
        "Unhandled error | update=%s", update, exc_info=context.error
    )
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Ocorreu um erro inesperado. Tente novamente.",
            )
        except Exception:
            return


def build_app(*, settings) -> Application:
    app = Application.builder().token(settings.bot_token).build()

    app.add_handler(CommandHandler("start", show_main_menu))
    app.add_handler(CommandHandler("buscar", search))
    app.add_handler(CommandHandler("buscarcat", search_by_category_command))

    conv_search = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_category_search, pattern=r"^buscarcat_\d+$")
        ],
        states={
            WAITING_SEARCH_TERM: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_pending_category_search
                )
            ]
        },
        fallbacks=[CommandHandler("start", show_main_menu)],
    )
    app.add_handler(conv_search)

    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^back_main$"))
    app.add_handler(
        CallbackQueryHandler(
            show_categories, pattern=r"^(categorias|categorias_\d+|back_categories)$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            show_items, pattern=r"^(cat_\d+|cat_\d+_\d+|back_cat_\d+)$"
        )
    )
    app.add_handler(CallbackQueryHandler(send_item, pattern=r"^item_\d+$"))
    app.add_handler(CallbackQueryHandler(search_pagination, pattern=r"^buscar_\d+$"))
    app.add_handler(CallbackQueryHandler(show_favorites, pattern=r"^favoritos_\d+$"))
    app.add_handler(CallbackQueryHandler(show_recentes, pattern=r"^recentes_\d+$"))
    app.add_handler(CallbackQueryHandler(toggle_favorite, pattern=r"^(fav|unfav)_\d+$"))
    app.add_handler(CallbackQueryHandler(noop, pattern=r"^noop$"))

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
    return app

def main() -> None:
    settings = get_settings(strict=True)
    configure(db_path=settings.database_path)
    asyncio.run(init_db(db_path=settings.database_path))

    app = build_app(settings=settings)

    logging.getLogger(__name__).info("Bot iniciado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
