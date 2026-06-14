import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
from services.user_service import get_user
from services.moderation_service import create_report, create_block, resolve_report
from matching import get_partner_id, end_match
from keyboards import (
    report_reason_keyboard, confirm_block_keyboard,
    in_chat_keyboard, main_menu_keyboard, back_to_main_keyboard
)

logger = logging.getLogger(__name__)


async def report_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user or not user.current_match_id:
            await query.answer("❌ You're not in a chat!", show_alert=True)
            return

    await query.edit_message_text(
        "🚨 *Report Partner*\n\nPlease select the reason for your report:",
        parse_mode="Markdown",
        reply_markup=report_reason_keyboard(),
    )


async def report_reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    reason = query.data.replace("report_reason_", "")

    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user or not user.current_match_id:
            await query.edit_message_text(
                "❌ Could not submit report — you're no longer in a chat.",
                reply_markup=main_menu_keyboard(),
            )
            return

        partner_id = await get_partner_id(session, user_id)
        if not partner_id:
            await query.edit_message_text(
                "❌ Could not identify your partner.",
                reply_markup=main_menu_keyboard(),
            )
            return

        match_id = user.current_match_id
        await create_report(session, user_id, partner_id, match_id, reason)

        # End the chat after report
        await end_match(session, match_id, user_id)

    await query.edit_message_text(
        "✅ *Report submitted.*\n\n"
        "Thank you for helping keep this community safe. "
        "Our moderation team will review your report.\n\n"
        "The chat has been ended for your safety.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

    if partner_id:
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text="👋 *Your partner has left the chat.*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            logger.warning(f"Could not notify partner {partner_id}: {e}")


async def cancel_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Report cancelled")
    await query.edit_message_text(
        "✅ Report cancelled.",
        reply_markup=in_chat_keyboard(),
    )


async def block_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user or not user.current_match_id:
            await query.answer("❌ You're not in a chat!", show_alert=True)
            return

    await query.edit_message_text(
        "🚫 *Block Partner?*\n\n"
        "They will no longer be able to match with you.\n\n"
        "Are you sure?",
        parse_mode="Markdown",
        reply_markup=confirm_block_keyboard(),
    )


async def confirm_block_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    partner_id = None
    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user or not user.current_match_id:
            await query.edit_message_text("❌ Not in a chat.", reply_markup=main_menu_keyboard())
            return

        partner_id = await get_partner_id(session, user_id)
        if partner_id:
            await create_block(session, user_id, partner_id)
            await end_match(session, user.current_match_id, user_id)

    await query.edit_message_text(
        "🚫 *User blocked.*\n\n"
        "You'll no longer be matched with this person. The chat has ended.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

    if partner_id:
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text="👋 *Your partner has left the chat.*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            logger.warning(f"Could not notify partner {partner_id}: {e}")


async def cancel_block_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Block cancelled")
    await query.edit_message_text(
        "✅ Block cancelled.",
        reply_markup=in_chat_keyboard(),
    )
