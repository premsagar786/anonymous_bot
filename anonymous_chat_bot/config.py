import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = [
        int(x.strip())
        for x in os.getenv("ADMIN_IDS", "").split(",")
        if x.strip().isdigit()
    ]
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./anonymous_chat.db"
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Safety
    MAX_REPORTS_BEFORE_BAN: int = int(os.getenv("MAX_REPORTS_BEFORE_BAN", "3"))
    BAN_DURATION_HOURS: int = int(os.getenv("BAN_DURATION_HOURS", "24"))
    RATE_LIMIT_MESSAGES: int = int(os.getenv("RATE_LIMIT_MESSAGES", "20"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    SPAM_THRESHOLD: int = int(os.getenv("SPAM_THRESHOLD", "5"))

    # Matching
    QUEUE_TIMEOUT_SECONDS: int = 300

    # Genders
    GENDERS = ["Male", "Female", "Other", "Prefer not to say"]

    # Countries (top used)
    COUNTRIES = [
        "🇺🇸 USA", "🇬🇧 UK", "🇮🇳 India", "🇩🇪 Germany", "🇫🇷 France",
        "🇧🇷 Brazil", "🇨🇦 Canada", "🇦🇺 Australia", "🇷🇺 Russia", "🇯🇵 Japan",
        "🇰🇷 South Korea", "🇲🇽 Mexico", "🇮🇩 Indonesia", "🇹🇷 Turkey", "🇸🇦 Saudi Arabia",
        "🇳🇬 Nigeria", "🇵🇰 Pakistan", "🇧🇩 Bangladesh", "🇵🇭 Philippines", "🇻🇳 Vietnam",
        "🇪🇬 Egypt", "🇦🇷 Argentina", "🇨🇴 Colombia", "🇿🇦 South Africa", "🇮🇷 Iran",
        "🌍 Other",
    ]

    # Age ranges
    AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55+"]


config = Config()
