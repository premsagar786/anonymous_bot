from datetime import datetime
from models import User, UserSettings


def format_profile(user: User, settings: UserSettings | None) -> str:
    hide_age = settings.hide_age if settings else False
    hide_gender = settings.hide_gender if settings else False
    hide_country = settings.hide_country if settings else False

    age_str = f"📅 Age: {user.age_range}" if user.age_range and not hide_age else "📅 Age: *hidden*" if hide_age else "📅 Age: *not set*"
    gender_str = f"⚧ Gender: {user.gender}" if user.gender and not hide_gender else "⚧ Gender: *hidden*" if hide_gender else "⚧ Gender: *not set*"
    country_str = f"🌍 Country: {user.country}" if user.country and not hide_country else "🌍 Country: *hidden*" if hide_country else "🌍 Country: *not set*"

    joined = user.joined_at.strftime("%B %d, %Y") if user.joined_at else "Unknown"

    return (
        "👤 *Your Profile*\n\n"
        f"{age_str}\n"
        f"{gender_str}\n"
        f"{country_str}\n\n"
        f"💬 Chats started: *{user.chat_count}*\n"
        f"📆 Joined: *{joined}*"
    )


def format_partner_info(partner: User, partner_settings: UserSettings | None) -> str:
    lines = ["🎭 *Your Anonymous Partner*\n"]
    if partner_settings:
        if not partner_settings.hide_gender and partner.gender:
            lines.append(f"⚧ Gender: {partner.gender}")
        if not partner_settings.hide_age and partner.age_range:
            lines.append(f"📅 Age range: {partner.age_range}")
        if not partner_settings.hide_country and partner.country:
            lines.append(f"🌍 Country: {partner.country}")
    if len(lines) == 1:
        lines.append("_This person prefers to stay fully anonymous_")
    return "\n".join(lines)


def format_ban_message(ban_until: datetime | None) -> str:
    if ban_until:
        until_str = ban_until.strftime("%B %d, %Y at %H:%M UTC")
        return (
            "🚫 *You are temporarily banned*\n\n"
            f"Your ban expires on: *{until_str}*\n\n"
            "If you believe this is a mistake, contact support."
        )
    return (
        "🚫 *You are permanently banned*\n\n"
        "Your account has been permanently banned for violating our community guidelines.\n"
        "Contact support if you believe this is an error."
    )


def format_stats(stats: dict) -> str:
    return (
        "📊 *Global Statistics*\n\n"
        f"👥 Total users: *{stats['total_users']:,}*\n"
        f"🟢 Active today: *{stats['active_today']:,}*\n"
        f"💬 Total chats: *{stats['total_chats']:,}*\n"
        f"🔴 Active chats: *{stats['active_chats']:,}*\n"
        f"⏳ In queue: *{stats['in_queue']:,}*"
    )


def help_text() -> str:
    return (
        "❓ *How to use Anonymous Chat Bot*\n\n"
        "🔍 *Finding a Partner*\n"
        "Tap _Find Partner_ to join the matching queue. "
        "You'll be matched with someone automatically.\n\n"
        "💬 *Chatting*\n"
        "All messages are relayed anonymously. You can send:\n"
        "• Text messages\n"
        "• Photos & videos\n"
        "• Voice messages\n"
        "• Stickers & GIFs\n"
        "• Documents\n\n"
        "⏭ *Next Partner*\n"
        "Skip your current partner and find a new one.\n\n"
        "🛑 *End Chat*\n"
        "End the current conversation.\n\n"
        "🚨 *Safety*\n"
        "Use the Report button to flag inappropriate behavior. "
        "Use Block to prevent someone from matching with you again.\n\n"
        "👤 *Profile*\n"
        "Set your age, gender, and country. You can hide these from partners in Settings.\n\n"
        "⚙️ *Settings*\n"
        "Set partner preferences and privacy options.\n\n"
        "🔞 *Rules*\n"
        "• No NSFW content\n"
        "• Be respectful\n"
        "• No spam or advertising\n"
        "• Violations result in bans"
    )
