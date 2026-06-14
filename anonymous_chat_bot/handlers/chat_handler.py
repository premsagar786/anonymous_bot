import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_session
from services.user_service import get_user, is_user_banned, get_user_with_settings
from matching import (
    find_match, create_match, end_match, get_partner_id,
    join_queue, leave_queue, increment_match_messages
)
from keyboards import (
    in_queue_keyboard, in_chat_keyboard, main_menu_keyboard,
    confirm_next_keyboard, back_to_main_keyboard
)
from utils.helpers import format_partner_info
from utils.rate_limiter import check_rate_limit
from sqlalchemy import select
from models import User, UserSettings

logger = logging.getLogger(__name__)


async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        banned, ban_until = await is_user_banned(session, user_id)
        if banned:
            from utils.helpers import format_ban_message
            await query.edit_message_text(
                format_ban_message(ban_until),
                parse_mode="Markdown",
                reply_markup=back_to_main_keyboard(),
            )
            return

        user = await get_user(session, user_id)
        if not user:
            await query.edit_message_text("❌ Please use /start first.")
            return

        if user.current_match_id:
            await query.answer("You're already in a chat!", show_alert=True)
            return

        # Try to find a match right away
        match_user_id = await find_match(session, user_id)

        if match_user_id:
            match = await create_match(session, user_id, match_user_id)
            match_id = match.id

    if match_user_id:
        async with get_session() as session:
            _, my_settings = await get_user_with_settings(session, user_id)
            partner, partner_settings = await get_user_with_settings(session, match_user_id)

        partner_info = format_partner_info(partner, partner_settings)

        await query.edit_message_text(
            f"🎉 *Partner found!*\n\n{partner_info}\n\n"
            "Say hello! You're now connected anonymously. 👋\n"
            "_Use the buttons below to manage your chat._",
            parse_mode="Markdown",
            reply_markup=in_chat_keyboard(),
        )

        await context.bot.send_message(
            chat_id=match_user_id,
            text=(
                f"🎉 *Partner found!*\n\n"
                "Say hello! You're now connected anonymously. 👋\n"
                "_Use the buttons below to manage your chat._"
            ),
            parse_mode="Markdown",
            reply_markup=in_chat_keyboard(),
        )
    else:
        async with get_session() as session:
            await join_queue(session, user_id)

        await query.edit_message_text(
            "⏳ *Looking for a partner...*\n\n"
            "You're in the queue. We'll match you as soon as someone is available!\n\n"
            "🌍 Searching globally...",
            parse_mode="Markdown",
            reply_markup=in_queue_keyboard(),
        )


async def leave_queue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        await leave_queue(session, user_id)

    await query.edit_message_text(
        "✅ *Left the queue.*\n\nYou've been removed from the matching queue.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def end_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user or not user.current_match_id:
            await query.edit_message_text(
                "❌ You're not in a chat.",
                reply_markup=main_menu_keyboard(),
            )
            return
        match_id = user.current_match_id
        partner_id = await get_partner_id(session, user_id)
        u1, u2 = await end_match(session, match_id, user_id)

    await query.edit_message_text(
        "🛑 *Chat ended.*\n\nThe conversation has been closed. Thanks for chatting!\n\n"
        "Start a new conversation anytime.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

    if partner_id:
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text=(
                    "👋 *Your partner has left the chat.*\n\n"
                    "The conversation has ended. Find a new partner below!"
                ),
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            logger.warning(f"Could not notify partner {partner_id}: {e}")


async def next_partner_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user or not user.current_match_id:
            await query.edit_message_text(
                "❌ You're not in a chat.",
                reply_markup=main_menu_keyboard(),
            )
            return

    await query.edit_message_text(
        "⏭ *Find next partner?*\n\nThis will end your current chat.",
        parse_mode="Markdown",
        reply_markup=confirm_next_keyboard(),
    )


async def confirm_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    partner_id = None
    async with get_session() as session:
        user = await get_user(session, user_id)
        if user and user.current_match_id:
            partner_id = await get_partner_id(session, user_id)
            await end_match(session, user.current_match_id, user_id)

    # Notify old partner
    if partner_id:
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text="👋 *Your partner has moved on.*\n\nFind a new partner below!",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            logger.warning(f"Could not notify partner {partner_id}: {e}")

    # Now try to find a new match
    new_match_id = None
    async with get_session() as session:
        new_match_id = await find_match(session, user_id)
        if new_match_id:
            match = await create_match(session, user_id, new_match_id)
            match_obj_id = match.id

    if new_match_id:
        async with get_session() as session:
            partner, partner_settings = await get_user_with_settings(session, new_match_id)

        partner_info = format_partner_info(partner, partner_settings)

        await query.edit_message_text(
            f"🎉 *New partner found!*\n\n{partner_info}\n\n"
            "Say hello! You're now connected anonymously. 👋",
            parse_mode="Markdown",
            reply_markup=in_chat_keyboard(),
        )

        try:
            await context.bot.send_message(
                chat_id=new_match_id,
                text="🎉 *Partner found!*\n\nSay hello! You're now connected anonymously. 👋",
                parse_mode="Markdown",
                reply_markup=in_chat_keyboard(),
            )
        except Exception as e:
            logger.warning(f"Could not notify new partner {new_match_id}: {e}")
    else:
        async with get_session() as session:
            await join_queue(session, user_id)

        await query.edit_message_text(
            "⏳ *Searching for a new partner...*\n\n"
            "You're back in the queue! We'll match you soon.",
            parse_mode="Markdown",
            reply_markup=in_queue_keyboard(),
        )


async def cancel_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Staying in current chat!")
    await query.edit_message_text(
        "✅ *Staying in current chat.*",
        parse_mode="Markdown",
        reply_markup=in_chat_keyboard(),
    )


async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Relay any message type to partner."""
    user_id = update.effective_user.id
    message = update.message

    # Rate limit check
    allowed, reason = check_rate_limit(user_id)
    if not allowed:
        await message.reply_text(f"⚠️ {reason}")
        return

    async with get_session() as session:
        banned, ban_until = await is_user_banned(session, user_id)
        if banned:
            from utils.helpers import format_ban_message
            await message.reply_text(format_ban_message(ban_until), parse_mode="Markdown")
            return

        user = await get_user(session, user_id)
        if not user:
            await message.reply_text("Please use /start first.")
            return

        if user.in_queue:
            await message.reply_text(
                "⏳ *You're in the queue...*\n\nPlease wait for a partner!",
                parse_mode="Markdown",
                reply_markup=in_queue_keyboard(),
            )
            return

        if not user.current_match_id:
            await message.reply_text(
                "❌ *You're not in a chat.*\n\nFind a partner first!",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
            return

        partner_id = await get_partner_id(session, user_id)
        match_id = user.current_match_id

        if not partner_id:
            await message.reply_text(
                "❌ *Chat session expired.*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
            return

        await increment_match_messages(session, match_id)

    # Relay the message based on type
    try:
        if message.text:
            await context.bot.send_message(
                chat_id=partner_id,
                text=message.text,
                reply_markup=in_chat_keyboard(),
            )
        elif message.photo:
            await context.bot.send_photo(
                chat_id=partner_id,
                photo=message.photo[-1].file_id,
                caption=message.caption,
                reply_markup=in_chat_keyboard(),
            )
        elif message.sticker:
            await context.bot.send_sticker(
                chat_id=partner_id,
                sticker=message.sticker.file_id,
            )
            await context.bot.send_message(
                chat_id=partner_id,
                text="⬆️ Sticker received",
                reply_markup=in_chat_keyboard(),
            )
        elif message.voice:
            await context.bot.send_voice(
                chat_id=partner_id,
                voice=message.voice.file_id,
                caption=message.caption,
                reply_markup=in_chat_keyboard(),
            )
        elif message.video:
            await context.bot.send_video(
                chat_id=partner_id,
                video=message.video.file_id,
                caption=message.caption,
                reply_markup=in_chat_keyboard(),
            )
        elif message.document:
            await context.bot.send_document(
                chat_id=partner_id,
                document=message.document.file_id,
                caption=message.caption,
                reply_markup=in_chat_keyboard(),
            )
        elif message.audio:
            await context.bot.send_audio(
                chat_id=partner_id,
                audio=message.audio.file_id,
                caption=message.caption,
                reply_markup=in_chat_keyboard(),
            )
        elif message.video_note:
            await context.bot.send_video_note(
                chat_id=partner_id,
                video_note=message.video_note.file_id,
            )
            await context.bot.send_message(
                chat_id=partner_id,
                text="⬆️ Video message received",
                reply_markup=in_chat_keyboard(),
            )
        elif message.animation:
            await context.bot.send_animation(
                chat_id=partner_id,
                animation=message.animation.file_id,
                caption=message.caption,
                reply_markup=in_chat_keyboard(),
            )
        elif message.location:
            await context.bot.send_location(
                chat_id=partner_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
            )
            await context.bot.send_message(
                chat_id=partner_id,
                text="📍 Location shared",
                reply_markup=in_chat_keyboard(),
            )
        else:
            await message.reply_text("❓ This message type is not supported yet.")
    except Exception as e:
        logger.error(f"Error relaying message from {user_id} to {partner_id}: {e}")
        await message.reply_text(
            "⚠️ Failed to deliver message. Your partner may have left.",
            reply_markup=main_menu_keyboard(),
        )


async def queue_checker(context: ContextTypes.DEFAULT_TYPE):
    """Background task: try to match queued users."""
    from database import get_session as gs
    async with gs() as session:
        from sqlalchemy import select
        from models import User
        result = await session.execute(
            select(User).where(User.in_queue == True, User.is_banned == False)
        )
        queued = result.scalars().all()

    matched = set()
    for user in queued:
        if user.id in matched:
            continue

        async with gs() as session:
            partner_id = await find_match(session, user.id)
            if partner_id and partner_id not in matched:
                match = await create_match(session, user.id, partner_id)
                matched.add(user.id)
                matched.add(partner_id)

        if partner_id and partner_id not in matched:
            matched.add(partner_id)

            async with gs() as session:
                partner, partner_settings = await get_user_with_settings(session, partner_id)
                my_user, my_settings = await get_user_with_settings(session, user.id)

            partner_info = format_partner_info(partner, partner_settings)
            my_info = format_partner_info(my_user, my_settings)

            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=f"🎉 *Partner found!*\n\n{partner_info}\n\nSay hello! 👋",
                    parse_mode="Markdown",
                    reply_markup=in_chat_keyboard(),
                )
            except Exception as e:
                logger.warning(f"Could not notify user {user.id}: {e}")

            try:
                await context.bot.send_message(
                    chat_id=partner_id,
                    text=f"🎉 *Partner found!*\n\n{my_info}\n\nSay hello! 👋",
                    parse_mode="Markdown",
                    reply_markup=in_chat_keyboard(),
                )
            except Exception as e:
                logger.warning(f"Could not notify partner {partner_id}: {e}")
