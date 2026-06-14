import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
from services.user_service import update_user_field, update_settings_field, get_user_with_settings
from keyboards import (
    age_selection_keyboard, gender_selection_keyboard, country_selection_keyboard,
    profile_keyboard, settings_keyboard,
)
from config import config

logger = logging.getLogger(__name__)


async def edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📅 *Select your age range:*",
        parse_mode="Markdown",
        reply_markup=age_selection_keyboard(),
    )


async def set_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    age_range = query.data.replace("set_age_", "")
    user_id = update.effective_user.id

    async with get_session() as session:
        await update_user_field(session, user_id, age_range=age_range)
        user, settings = await get_user_with_settings(session, user_id)

    if user:
        from utils.helpers import format_profile
        await query.edit_message_text(
            f"✅ Age range set to *{age_range}*\n\n" + format_profile(user, settings),
            parse_mode="Markdown",
            reply_markup=profile_keyboard(user_id),
        )


async def edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⚧ *Select your gender:*",
        parse_mode="Markdown",
        reply_markup=gender_selection_keyboard("set_gender"),
    )


async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = query.data.replace("set_gender_", "")
    user_id = update.effective_user.id

    async with get_session() as session:
        await update_user_field(session, user_id, gender=gender)
        user, settings = await get_user_with_settings(session, user_id)

    if user:
        from utils.helpers import format_profile
        await query.edit_message_text(
            f"✅ Gender set to *{gender}*\n\n" + format_profile(user, settings),
            parse_mode="Markdown",
            reply_markup=profile_keyboard(user_id),
        )


async def edit_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌍 *Select your country:*",
        parse_mode="Markdown",
        reply_markup=country_selection_keyboard("set_country", 0),
    )


async def set_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country = query.data.replace("set_country_", "")
    user_id = update.effective_user.id

    async with get_session() as session:
        await update_user_field(session, user_id, country=country)
        user, settings = await get_user_with_settings(session, user_id)

    if user:
        from utils.helpers import format_profile
        await query.edit_message_text(
            f"✅ Country set to *{country}*\n\n" + format_profile(user, settings),
            parse_mode="Markdown",
            reply_markup=profile_keyboard(user_id),
        )


async def country_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # data format: country_page_{prefix}_{page}
    parts = query.data.split("_")
    # country_page_set_country_0 or country_page_set_country_pref_0
    page = int(parts[-1])
    prefix = "_".join(parts[2:-1])

    title = "🌍 *Select your country:*" if "pref" not in prefix else "🌍 *Select preferred country:*"
    await query.edit_message_text(
        title,
        parse_mode="Markdown",
        reply_markup=country_selection_keyboard(prefix, page),
    )


async def pref_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👥 *Select preferred gender to chat with:*",
        parse_mode="Markdown",
        reply_markup=gender_selection_keyboard("set_gender_pref"),
    )


async def set_gender_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    raw = query.data.replace("set_gender_pref_", "")
    pref = None if raw == "any" else raw

    async with get_session() as session:
        await update_settings_field(session, user_id, gender_pref=pref)
        _, settings = await get_user_with_settings(session, user_id)

    pref_str = pref or "Any"
    await query.edit_message_text(
        f"✅ Gender preference set to *{pref_str}*",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings) if settings else None,
    )


async def pref_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌍 *Select preferred country to chat with:*",
        parse_mode="Markdown",
        reply_markup=country_selection_keyboard("set_country_pref", 0),
    )


async def set_country_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    raw = query.data.replace("set_country_pref_", "")
    pref = None if raw == "any" else raw

    async with get_session() as session:
        await update_settings_field(session, user_id, country_pref=pref)
        _, settings = await get_user_with_settings(session, user_id)

    pref_str = pref or "Any"
    await query.edit_message_text(
        f"✅ Country preference set to *{pref_str}*",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings) if settings else None,
    )


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        _, settings = await get_user_with_settings(session, user_id)
        new_val = not settings.notifications
        await update_settings_field(session, user_id, notifications=new_val)
        _, settings = await get_user_with_settings(session, user_id)

    status = "ON 🔔" if new_val else "OFF 🔕"
    await query.answer(f"Notifications turned {status}", show_alert=False)
    await query.edit_message_text(
        "⚙️ *Settings*\n\nCustomize your experience:",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings),
    )


async def toggle_hide_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        _, settings = await get_user_with_settings(session, user_id)
        await update_settings_field(session, user_id, hide_gender=not settings.hide_gender)
        _, settings = await get_user_with_settings(session, user_id)

    await query.edit_message_text(
        "⚙️ *Settings*\n\nCustomize your experience:",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings),
    )


async def toggle_hide_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        _, settings = await get_user_with_settings(session, user_id)
        await update_settings_field(session, user_id, hide_country=not settings.hide_country)
        _, settings = await get_user_with_settings(session, user_id)

    await query.edit_message_text(
        "⚙️ *Settings*\n\nCustomize your experience:",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings),
    )


async def toggle_hide_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        _, settings = await get_user_with_settings(session, user_id)
        await update_settings_field(session, user_id, hide_age=not settings.hide_age)
        _, settings = await get_user_with_settings(session, user_id)

    await query.edit_message_text(
        "⚙️ *Settings*\n\nCustomize your experience:",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(settings),
    )
