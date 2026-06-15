🎭 Anonymous Chat Bot
A production-ready Telegram anonymous chat bot built with Python 3.12, python-telegram-bot v21, SQLAlchemy, and SQLite.

✨ Features
🔍 Random Matchmaking — Intelligent queue with preference-based matching
💬 Anonymous Chat — Text, photos, stickers, voice, video, documents, GIFs
👤 User Profiles — Age, gender, country with privacy controls
⚙️ Settings — Partner preferences, privacy toggles, notification controls
🚨 Safety — Report system, block system, rate limiting, flood protection, auto-ban
🔧 Admin Panel — User stats, report review, ban management, user lookup
📊 Statistics — Global usage stats
🗂 Project Structure
anonymous_chat_bot/
├── bot.py              # Main entrypoint, handler registration
├── config.py           # Configuration from environment
├── database.py         # Async SQLAlchemy engine & session
├── models.py           # ORM models (users, matches, reports, blocks, bans)
├── matching.py         # Queue & matchmaking logic
├── keyboards.py        # All inline keyboard builders
├── handlers/
│   ├── start_handler.py       # /start command
│   ├── menu_handler.py        # Main menu callbacks
│   ├── chat_handler.py        # Find/end/next partner, message relay
│   ├── profile_handler.py     # Profile & settings editing
│   ├── moderation_handler.py  # Report & block flows
│   └── admin_handler.py       # Admin panel
├── services/
│   ├── user_service.py        # User CRUD & stats
│   └── moderation_service.py  # Reports, blocks, bans
├── utils/
│   ├── helpers.py             # Text formatters
│   └── rate_limiter.py        # In-memory rate limiting
├── requirements.txt
├── .env.example
├── Procfile               # Railway/Heroku
├── railway.toml           # Railway config
└── runtime.txt            # Python version
🗄 Database Schema
Table	Purpose
users	User profiles, status, queue state
settings	Per-user preferences and privacy
matches	Chat session records
reports	User reports with resolution tracking
blocks	User block relationships
bans	Ban records with expiry
rate_limits	(Reserved) rate limit tracking
🚀 Quick Start
1. Clone & Install
git clone <your-repo>
cd anonymous_chat_bot
pip install -r requirements.txt
2. Configure
cp .env.example .env
Edit .env:

BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=your_telegram_user_id
Get your Telegram user ID by messaging @userinfobot.

3. Run
python bot.py
☁️ Deploy to Railway
Push this project to GitHub
Go to railway.app → New Project → Deploy from GitHub
Add environment variables in Railway dashboard:
BOT_TOKEN
ADMIN_IDS
Railway will auto-detect Python and deploy
For SQLite persistence on Railway, add a volume:

Mount path: /app
Set DATABASE_URL=sqlite+aiosqlite:////app/anonymous_chat.db
🔧 Environment Variables
Variable	Default	Description
BOT_TOKEN	(required)	Telegram bot token
ADMIN_IDS	(required)	Comma-separated admin user IDs
DATABASE_URL	sqlite+aiosqlite:///./anonymous_chat.db	Database URL
LOG_LEVEL	INFO	Logging level
MAX_REPORTS_BEFORE_BAN	3	Reports before auto-ban
BAN_DURATION_HOURS	24	Default temp ban duration
RATE_LIMIT_MESSAGES	20	Max messages per window
RATE_LIMIT_WINDOW	60	Rate limit window (seconds)
SPAM_THRESHOLD	5	Burst spam threshold
🔧 Admin Commands
/admin — Open admin panel (admin users only)
From the admin panel you can:

View global statistics
Review and action pending reports (resolve, temp ban, perm ban)
View recent bans
Look up any user by ID (view profile, ban, unban)
🛡 Safety Features
Rate limiting — 20 messages/minute per user (configurable)
Flood protection — Burst detection with escalating mute durations
Auto-ban — Triggered after N reports (configurable)
Block system — Prevents re-matching with blocked users
Report system — 5 report reasons, sent to admin review queue
Ban system — Temporary and permanent bans with notifications
💬 Supported Message Types
Type	Supported
Text	✅
Photos	✅
Stickers	✅
Voice messages	✅
Video messages (circles)	✅
Videos	✅
Documents	✅
Audio files	✅
GIF/Animations	✅
Locations	✅
🔐 Privacy
No real names or usernames are ever sent to partners
All relay is anonymous by design
Users can hide age, gender, and country from partners
Partner identity is never revealed, even in reports
📝 License
MIT License — use freely, attribution appreciated.# anonymous_bot