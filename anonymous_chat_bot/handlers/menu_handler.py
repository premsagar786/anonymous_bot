import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
from services.user_service import get_user_with_settings, get_global_stats
from keyboards import (
    main_menu_keyboard, profile_keyboard, settings_keyboard, back_to_main_keyboard
)
from utils.helpers import format_profile, format_stats, help_text

logger = logging.getLogger(__name__)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 *Main Menu*\n\nWhat would you like to do?",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        user, settings = await get_user_with_settings(session, user_id)

    if not user:
        await query.edit_message_text("❌ User not found.", reply_markup=back_to_main_keyboard())
        return

    text = format_profile(user, settings)
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=profile_keyboard(user_id),
    )


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        user, settings = await get_user_with_settings(session, user_id)

    if not settings:
        await query.edit_message_text("❌ Settings not found.", reply_markup=back_to_main_keyboard())
        return

    await query.edit_message_text(
        "⚙️ *Settings*\n\nCustomize your experience:",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings),
    )


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with get_session() as session:
        stats = await get_global_stats(session)

    await query.edit_message_text(
        format_stats(stats),
        parse_mode="Markdown",
        reply_markup=back_to_main_keyboard(),
    )


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        help_text(),
        parse_mode="Markdown",
        reply_markup=back_to_main_keyboard(),
    )
