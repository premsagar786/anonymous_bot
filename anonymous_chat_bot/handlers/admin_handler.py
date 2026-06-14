import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
from services.user_service import get_global_stats, get_user
from services.moderation_service import (
    get_pending_reports, get_recent_bans, apply_temp_ban,
    apply_perm_ban, resolve_report, unban_user
)
from keyboards import (
    admin_panel_keyboard, admin_report_action_keyboard, back_to_main_keyboard
)
from config import config

logger = logging.getLogger(__name__)


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in config.ADMIN_IDS:
            if update.callback_query:
                await update.callback_query.answer("❌ Admin only!", show_alert=True)
            else:
                await update.message.reply_text("❌ You don't have permission to do this.")
            return
        return await func(update, context)
    return wrapper


@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 *Admin Panel*\n\nWelcome, Admin!",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )


@admin_only
async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔧 *Admin Panel*\n\nWelcome, Admin!",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )


@admin_only
async def admin_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with get_session() as session:
        stats = await get_global_stats(session)

    from utils.helpers import format_stats
    await query.edit_message_text(
        "📊 *System Statistics*\n\n" + format_stats(stats).replace("📊 *Global Statistics*\n\n", ""),
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )


@admin_only
async def admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with get_session() as session:
        reports = await get_pending_reports(session)

    if not reports:
        await query.edit_message_text(
            "✅ *No pending reports.*\n\nAll reports have been resolved!",
            parse_mode="Markdown",
            reply_markup=admin_panel_keyboard(),
        )
        return

    report = reports[0]
    text = (
        f"📋 *Pending Reports: {len(reports)}*\n\n"
        f"Report #{report.id}\n"
        f"Reporter: `{report.reporter_id}`\n"
        f"Reported: `{report.reported_id}`\n"
        f"Reason: *{report.reason}*\n"
        f"Date: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "_Showing oldest unresolved report_"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_report_action_keyboard(report.id, report.reported_id),
    )


@admin_only
async def admin_resolve_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    report_id = int(query.data.split("_")[-1])

    async with get_session() as session:
        success = await resolve_report(session, report_id, admin_id, "No action taken")

    await query.edit_message_text(
        f"✅ *Report #{report_id} resolved.*\n\nNo action was taken against the user.",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )


@admin_only
async def admin_tempban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    parts = query.data.split("_")
    # admin_tempban_{user_id}_{report_id}
    user_id = int(parts[2])
    report_id = int(parts[3])

    async with get_session() as session:
        await apply_temp_ban(
            session, user_id, admin_id,
            "Banned by admin following report",
            config.BAN_DURATION_HOURS,
        )
        await resolve_report(session, report_id, admin_id, f"Temp ban {config.BAN_DURATION_HOURS}h applied")

    await query.edit_message_text(
        f"⏰ *User `{user_id}` temp-banned for {config.BAN_DURATION_HOURS} hours.*",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"⚠️ *You have been temporarily banned.*\n\n"
                f"Duration: *{config.BAN_DURATION_HOURS} hours*\n"
                "Reason: Violation of community guidelines."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass


@admin_only
async def admin_permban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    parts = query.data.split("_")
    user_id = int(parts[2])
    report_id = int(parts[3])

    async with get_session() as session:
        await apply_perm_ban(
            session, user_id, admin_id,
            "Permanent ban by admin following report",
        )
        await resolve_report(session, report_id, admin_id, "Permanent ban applied")

    await query.edit_message_text(
        f"🚫 *User `{user_id}` permanently banned.*",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🚫 *You have been permanently banned.*\n\n"
                "Your account has been banned for violating community guidelines.\n"
                "Contact support if you believe this is an error."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass


@admin_only
async def admin_bans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with get_session() as session:
        bans = await get_recent_bans(session)

    if not bans:
        await query.edit_message_text(
            "✅ *No active bans.*",
            parse_mode="Markdown",
            reply_markup=admin_panel_keyboard(),
        )
        return

    lines = ["🚫 *Recent Active Bans*\n"]
    for ban in bans:
        exp = ban.expires_at.strftime("%m/%d %H:%M") if ban.expires_at else "Permanent"
        lines.append(f"• `{ban.user_id}` — {ban.reason[:30]} (expires: {exp})")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )


@admin_only
async def admin_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_lookup"] = True
    await query.edit_message_text(
        "🔍 *User Lookup*\n\nPlease send the Telegram user ID to look up:",
        parse_mode="Markdown",
        reply_markup=back_to_main_keyboard(),
    )


async def handle_admin_lookup_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_lookup"):
        return False

    user_id = update.effective_user.id
    if user_id not in config.ADMIN_IDS:
        return False

    context.user_data.pop("awaiting_lookup", None)
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ Invalid user ID.")
        return True

    target_id = int(text)
    async with get_session() as session:
        from sqlalchemy import select
        from models import User, Report, Ban
        result = await session.execute(select(User).where(User.id == target_id))
        user = result.scalar_one_or_none()

        if not user:
            await update.message.reply_text(f"❌ User `{target_id}` not found.", parse_mode="Markdown")
            return True

        report_count = await session.execute(
            select(Report).where(Report.reported_id == target_id)
        )
        reports = report_count.scalars().all()

    ban_status = "🚫 BANNED" if user.is_banned else "✅ Active"
    if user.ban_until:
        ban_status += f" (until {user.ban_until.strftime('%m/%d %H:%M')})"

    info = (
        f"👤 *User `{target_id}`*\n\n"
        f"Name: {user.first_name}\n"
        f"Username: @{user.username or 'none'}\n"
        f"Status: {ban_status}\n"
        f"Gender: {user.gender or 'not set'}\n"
        f"Age: {user.age_range or 'not set'}\n"
        f"Country: {user.country or 'not set'}\n"
        f"Chats: {user.chat_count}\n"
        f"Reports received: {len(reports)}\n"
        f"Joined: {user.joined_at.strftime('%Y-%m-%d')}\n"
        f"Last active: {user.last_active.strftime('%Y-%m-%d %H:%M')}"
    )

    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏰ Temp Ban", callback_data=f"admin_lookup_tempban_{target_id}")],
        [InlineKeyboardButton(f"🚫 Perm Ban", callback_data=f"admin_lookup_permban_{target_id}")],
        [InlineKeyboardButton(f"✅ Unban", callback_data=f"admin_lookup_unban_{target_id}")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
    ])

    await update.message.reply_text(info, parse_mode="Markdown", reply_markup=keyboard)
    return True


@admin_only
async def admin_lookup_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    parts = query.data.split("_")
    action = parts[3]
    target_id = int(parts[4])

    async with get_session() as session:
        if action == "tempban":
            await apply_temp_ban(session, target_id, admin_id, "Admin temp ban", config.BAN_DURATION_HOURS)
            msg = f"⏰ User `{target_id}` temp-banned for {config.BAN_DURATION_HOURS}h"
        elif action == "permban":
            await apply_perm_ban(session, target_id, admin_id, "Admin permanent ban")
            msg = f"🚫 User `{target_id}` permanently banned"
        elif action == "unban":
            await unban_user(session, target_id)
            msg = f"✅ User `{target_id}` unbanned"
        else:
            msg = "❓ Unknown action"

    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=admin_panel_keyboard())
