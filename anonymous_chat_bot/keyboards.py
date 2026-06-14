from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import config


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Find Partner", callback_data="find_partner")],
        [
            InlineKeyboardButton("👤 Profile", callback_data="profile"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ])


def in_queue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Leave Queue", callback_data="leave_queue")],
    ])


def in_chat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏭ Next Partner", callback_data="next_partner"),
            InlineKeyboardButton("🛑 End Chat", callback_data="end_chat"),
        ],
        [
            InlineKeyboardButton("🚨 Report", callback_data="report_user"),
            InlineKeyboardButton("🚫 Block", callback_data="block_user"),
        ],
    ])


def profile_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Edit Age", callback_data="edit_age"),
            InlineKeyboardButton("✏️ Edit Gender", callback_data="edit_gender"),
        ],
        [InlineKeyboardButton("✏️ Edit Country", callback_data="edit_country")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])


def age_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, age in enumerate(config.AGE_RANGES):
        row.append(InlineKeyboardButton(age, callback_data=f"set_age_{age}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="profile")])
    return InlineKeyboardMarkup(buttons)


def gender_selection_keyboard(prefix: str = "set_gender") -> InlineKeyboardMarkup:
    gender_emojis = {"Male": "👨", "Female": "👩", "Other": "🧑", "Prefer not to say": "🤫"}
    buttons = []
    row = []
    for g in config.GENDERS:
        emoji = gender_emojis.get(g, "👤")
        row.append(InlineKeyboardButton(f"{emoji} {g}", callback_data=f"{prefix}_{g}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if prefix == "set_gender_pref":
        buttons.append([InlineKeyboardButton("🌐 Any Gender", callback_data="set_gender_pref_any")])
    back = "profile" if prefix == "set_gender" else "settings"
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=back)])
    return InlineKeyboardMarkup(buttons)


def country_selection_keyboard(prefix: str = "set_country", page: int = 0) -> InlineKeyboardMarkup:
    per_page = 10
    countries = config.COUNTRIES
    start = page * per_page
    end = start + per_page
    page_countries = countries[start:end]

    buttons = []
    row = []
    for i, c in enumerate(page_countries):
        row.append(InlineKeyboardButton(c, callback_data=f"{prefix}_{c}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"country_page_{prefix}_{page - 1}"))
    if end < len(countries):
        nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"country_page_{prefix}_{page + 1}"))
    if nav:
        buttons.append(nav)

    if prefix == "set_country_pref":
        buttons.append([InlineKeyboardButton("🌐 Any Country", callback_data="set_country_pref_any")])
    back = "profile" if prefix == "set_country" else "settings"
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=back)])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(settings) -> InlineKeyboardMarkup:
    notif_text = "🔔 Notifications: ON" if settings.notifications else "🔕 Notifications: OFF"
    hide_g = "✅ Hide Gender" if settings.hide_gender else "❌ Show Gender"
    hide_c = "✅ Hide Country" if settings.hide_country else "❌ Show Country"
    hide_a = "✅ Hide Age" if settings.hide_age else "❌ Show Age"
    gp = settings.gender_pref or "Any"
    cp = settings.country_pref or "Any"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👥 Gender Pref: {gp}", callback_data="pref_gender")],
        [InlineKeyboardButton(f"🌍 Country Pref: {cp}", callback_data="pref_country")],
        [InlineKeyboardButton(notif_text, callback_data="toggle_notifications")],
        [
            InlineKeyboardButton(hide_g, callback_data="toggle_hide_gender"),
            InlineKeyboardButton(hide_c, callback_data="toggle_hide_country"),
        ],
        [InlineKeyboardButton(hide_a, callback_data="toggle_hide_age")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])


def report_reason_keyboard() -> InlineKeyboardMarkup:
    reasons = [
        ("🔞 Inappropriate Content", "inappropriate"),
        ("💬 Spam", "spam"),
        ("😠 Harassment", "harassment"),
        ("🤖 Bot/Scam", "bot_scam"),
        ("⚠️ Other", "other"),
    ]
    buttons = [[InlineKeyboardButton(text, callback_data=f"report_reason_{code}")] for text, code in reasons]
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel_report")])
    return InlineKeyboardMarkup(buttons)


def confirm_block_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Block", callback_data="confirm_block"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_block"),
        ]
    ])


def confirm_next_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Next", callback_data="confirm_next"),
            InlineKeyboardButton("❌ Stay", callback_data="cancel_next"),
        ]
    ])


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 User Stats", callback_data="admin_user_stats")],
        [InlineKeyboardButton("📋 Pending Reports", callback_data="admin_reports")],
        [InlineKeyboardButton("🚫 Recent Bans", callback_data="admin_bans")],
        [InlineKeyboardButton("🔍 Lookup User", callback_data="admin_lookup")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])


def admin_report_action_keyboard(report_id: int, reported_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Resolve (No Action)", callback_data=f"admin_resolve_{report_id}")],
        [InlineKeyboardButton("⏰ Temp Ban (24h)", callback_data=f"admin_tempban_{reported_id}_{report_id}")],
        [InlineKeyboardButton("🚫 Permanent Ban", callback_data=f"admin_permban_{reported_id}_{report_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_reports")],
    ])


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ])
