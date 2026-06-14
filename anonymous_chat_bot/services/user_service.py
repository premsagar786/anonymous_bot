import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, UserSettings
from config import config

logger = logging.getLogger(__name__)


async def get_or_create_user(session: AsyncSession, tg_user) -> User:
    result = await session.execute(select(User).where(User.id == tg_user.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name or "Anonymous",
            is_admin=(tg_user.id in config.ADMIN_IDS),
        )
        session.add(user)
        await session.flush()

        settings = UserSettings(user_id=tg_user.id)
        session.add(settings)
        await session.flush()
        logger.info(f"New user created: {tg_user.id}")
    else:
        user.username = tg_user.username
        user.first_name = tg_user.first_name or user.first_name
        user.last_active = datetime.utcnow()
        if tg_user.id in config.ADMIN_IDS:
            user.is_admin = True

    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_with_settings(session: AsyncSession, user_id: int) -> tuple[User | None, UserSettings | None]:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None, None

    result2 = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result2.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user_id)
        session.add(settings)
        await session.flush()

    return user, settings


async def update_user_field(session: AsyncSession, user_id: int, **kwargs) -> bool:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    for key, val in kwargs.items():
        setattr(user, key, val)
    return True


async def update_settings_field(session: AsyncSession, user_id: int, **kwargs) -> bool:
    result = await session.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user_id)
        session.add(settings)
        await session.flush()
    for key, val in kwargs.items():
        setattr(settings, key, val)
    return True


async def is_user_banned(session: AsyncSession, user_id: int) -> tuple[bool, datetime | None]:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_banned:
        return False, None
    if user.ban_until and user.ban_until < datetime.utcnow():
        user.is_banned = False
        user.ban_until = None
        return False, None
    return True, user.ban_until


async def get_global_stats(session: AsyncSession) -> dict:
    from sqlalchemy import func
    from models import Match

    total_users = await session.execute(select(func.count(User.id)))
    active_today = await session.execute(
        select(func.count(User.id)).where(
            User.last_active >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        )
    )
    total_chats = await session.execute(select(func.count(Match.id)))
    active_chats = await session.execute(
        select(func.count(Match.id)).where(Match.is_active == True)
    )
    in_queue = await session.execute(
        select(func.count(User.id)).where(User.in_queue == True)
    )

    return {
        "total_users": total_users.scalar() or 0,
        "active_today": active_today.scalar() or 0,
        "total_chats": total_chats.scalar() or 0,
        "active_chats": active_chats.scalar() or 0,
        "in_queue": in_queue.scalar() or 0,
    }
