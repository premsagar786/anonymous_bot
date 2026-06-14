import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
from services.user_service import get_or_create_user, is_user_banned
from keyboards import main_menu_keyboard
from utils.helpers import format_ban_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    async with get_session() as session:
        db_user = await get_or_create_user(session, user)
        banned, ban_until = await is_user_banned(session, user.id)

    if banned:
        await update.message.reply_text(
            format_ban_message(ban_until),
            parse_mode="Markdown",
        )
        return

    welcome = (
        f"👋 *Welcome to Anonymous Chat Bot*{',' if db_user.first_name else '!'}\n\n"
        "Connect with random people around the world — completely anonymously! 🌍\n\n"
        "Your identity is always protected. Have fun and be respectful! 🎭\n\n"
        "Use the buttons below to get started:"
    )

    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
