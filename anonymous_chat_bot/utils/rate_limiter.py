import logging
from collections import defaultdict
from datetime import datetime, timedelta
from config import config

logger = logging.getLogger(__name__)

# In-memory rate limiting (fast, no DB overhead for message relay)
_user_messages: dict[int, list[datetime]] = defaultdict(list)
_user_spam_score: dict[int, int] = defaultdict(int)
_user_flood_until: dict[int, datetime] = {}


def check_rate_limit(user_id: int) -> tuple[bool, str]:
    """Returns (allowed, reason). True = allowed."""
    now = datetime.utcnow()

    # Check flood protection
    if user_id in _user_flood_until:
        if now < _user_flood_until[user_id]:
            remaining = int((_user_flood_until[user_id] - now).total_seconds())
            return False, f"⏳ Slow down! You're sending too fast. Wait {remaining}s."
        else:
            del _user_flood_until[user_id]
            _user_spam_score[user_id] = 0

    # Sliding window rate limit
    window_start = now - timedelta(seconds=config.RATE_LIMIT_WINDOW)
    _user_messages[user_id] = [
        t for t in _user_messages[user_id] if t > window_start
    ]
    _user_messages[user_id].append(now)

    count = len(_user_messages[user_id])

    if count > config.RATE_LIMIT_MESSAGES:
        _user_spam_score[user_id] += 1
        flood_duration = min(30 * _user_spam_score[user_id], 300)
        _user_flood_until[user_id] = now + timedelta(seconds=flood_duration)
        logger.warning(f"Rate limit exceeded for user {user_id}. Flood for {flood_duration}s")
        return False, f"🚫 Message limit exceeded. You're muted for {flood_duration}s."

    # Spam burst detection (5 messages in 3 seconds)
    burst_window = now - timedelta(seconds=3)
    burst_count = sum(1 for t in _user_messages[user_id] if t > burst_window)
    if burst_count >= config.SPAM_THRESHOLD:
        _user_spam_score[user_id] += 1
        _user_flood_until[user_id] = now + timedelta(seconds=10)
        return False, "⚡ Sending too fast! Slow down a bit."

    return True, ""


def reset_rate_limit(user_id: int):
    _user_messages.pop(user_id, None)
    _user_spam_score.pop(user_id, None)
    _user_flood_until.pop(user_id, None)
