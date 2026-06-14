import asyncio
import logging
import sys
# pyrefly: ignore [missing-import]
from telegram import Update
# pyrefly: ignore [missing-import]
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters,
)
from config import config
from database import init_db, close_db
from handlers.start_handler import start_command
from handlers.menu_handler import (
    show_main_menu, show_profile, show_settings, show_stats, show_help
)
from handlers.chat_handler import (
    find_partner, leave_queue_handler, end_chat_handler,
    next_partner_handler, confirm_next_handler, cancel_next_handler,
    relay_message, queue_checker,
)
from handlers.profile_handler import (
    edit_age, set_age, edit_gender, set_gender, edit_country,
    set_country, country_page, pref_gender, set_gender_pref,
    pref_country, set_country_pref, toggle_notifications,
    toggle_hide_gender, toggle_hide_country, toggle_hide_age,
)
from handlers.moderation_handler import (
    report_user_handler, report_reason_handler, cancel_report_handler,
    block_user_handler, confirm_block_handler, cancel_block_handler,
)
from handlers.admin_handler import (
    admin_command, admin_panel_callback, admin_user_stats,
    admin_reports, admin_resolve_report, admin_tempban, admin_permban,
    admin_bans, admin_lookup, handle_admin_lookup_input, admin_lookup_action,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log"),
    ],
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context):
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    if isinstance(update, Update):
        try:
            if update.callback_query:
                await update.callback_query.answer("⚠️ Something went wrong. Please try again.", show_alert=True)
            elif update.message:
                await update.message.reply_text("⚠️ An error occurred. Please try again later.")
        except Exception:
            pass


async def post_init(app: Application):
    await init_db()
    logger.info("Bot initialized successfully")


async def post_shutdown(app: Application):
    await close_db()
    logger.info("Bot shut down cleanly")


def main():
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set! Please configure your .env file.")
        sys.exit(1)

    # Ensure there is an event loop set for python 3.14+ compatibility
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # === Core Commands ===
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))

    # === Main Menu ===
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(show_profile, pattern="^profile$"))
    app.add_handler(CallbackQueryHandler(show_settings, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))

    # === Chat Flow ===
    app.add_handler(CallbackQueryHandler(find_partner, pattern="^find_partner$"))
    app.add_handler(CallbackQueryHandler(leave_queue_handler, pattern="^leave_queue$"))
    app.add_handler(CallbackQueryHandler(end_chat_handler, pattern="^end_chat$"))
    app.add_handler(CallbackQueryHandler(next_partner_handler, pattern="^next_partner$"))
    app.add_handler(CallbackQueryHandler(confirm_next_handler, pattern="^confirm_next$"))
    app.add_handler(CallbackQueryHandler(cancel_next_handler, pattern="^cancel_next$"))

    # === Profile Editing ===
    app.add_handler(CallbackQueryHandler(edit_age, pattern="^edit_age$"))
    app.add_handler(CallbackQueryHandler(set_age, pattern="^set_age_"))
    app.add_handler(CallbackQueryHandler(edit_gender, pattern="^edit_gender$"))
    app.add_handler(CallbackQueryHandler(set_gender, pattern="^set_gender_(?!pref)"))
    app.add_handler(CallbackQueryHandler(edit_country, pattern="^edit_country$"))
    app.add_handler(CallbackQueryHandler(set_country, pattern="^set_country_(?!pref)"))
    app.add_handler(CallbackQueryHandler(country_page, pattern="^country_page_"))

    # === Settings ===
    app.add_handler(CallbackQueryHandler(pref_gender, pattern="^pref_gender$"))
    app.add_handler(CallbackQueryHandler(set_gender_pref, pattern="^set_gender_pref_"))
    app.add_handler(CallbackQueryHandler(pref_country, pattern="^pref_country$"))
    app.add_handler(CallbackQueryHandler(set_country_pref, pattern="^set_country_pref_"))
    app.add_handler(CallbackQueryHandler(toggle_notifications, pattern="^toggle_notifications$"))
    app.add_handler(CallbackQueryHandler(toggle_hide_gender, pattern="^toggle_hide_gender$"))
    app.add_handler(CallbackQueryHandler(toggle_hide_country, pattern="^toggle_hide_country$"))
    app.add_handler(CallbackQueryHandler(toggle_hide_age, pattern="^toggle_hide_age$"))

    # === Moderation ===
    app.add_handler(CallbackQueryHandler(report_user_handler, pattern="^report_user$"))
    app.add_handler(CallbackQueryHandler(report_reason_handler, pattern="^report_reason_"))
    app.add_handler(CallbackQueryHandler(cancel_report_handler, pattern="^cancel_report$"))
    app.add_handler(CallbackQueryHandler(block_user_handler, pattern="^block_user$"))
    app.add_handler(CallbackQueryHandler(confirm_block_handler, pattern="^confirm_block$"))
    app.add_handler(CallbackQueryHandler(cancel_block_handler, pattern="^cancel_block$"))

    # === Admin Panel ===
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_user_stats, pattern="^admin_user_stats$"))
    app.add_handler(CallbackQueryHandler(admin_reports, pattern="^admin_reports$"))
    app.add_handler(CallbackQueryHandler(admin_resolve_report, pattern="^admin_resolve_"))
    app.add_handler(CallbackQueryHandler(admin_tempban, pattern="^admin_tempban_"))
    app.add_handler(CallbackQueryHandler(admin_permban, pattern="^admin_permban_"))
    app.add_handler(CallbackQueryHandler(admin_bans, pattern="^admin_bans$"))
    app.add_handler(CallbackQueryHandler(admin_lookup, pattern="^admin_lookup$"))
    app.add_handler(CallbackQueryHandler(admin_lookup_action, pattern="^admin_lookup_(tempban|permban|unban)_"))

    # === Message Relay (must be last) ===
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            relay_message,
        )
    )

    # === Background Jobs ===
    job_queue = app.job_queue
    job_queue.run_repeating(queue_checker, interval=5, first=10)

    # === Error Handler ===
    app.add_error_handler(error_handler)

    logger.info("Starting Anonymous Chat Bot...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
