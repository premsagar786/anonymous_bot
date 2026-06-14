import logging
import asyncio
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, UserSettings, Match, Block
from config import config

logger = logging.getLogger(__name__)

# In-memory queue lock to prevent race conditions
_match_lock = asyncio.Lock()


async def get_blocked_ids(session: AsyncSession, user_id: int) -> set[int]:
    result = await session.execute(
        select(Block.blocked_id).where(Block.blocker_id == user_id)
    )
    blocked = {row[0] for row in result.fetchall()}

    result2 = await session.execute(
        select(Block.blocker_id).where(Block.blocked_id == user_id)
    )
    blockers = {row[0] for row in result2.fetchall()}

    return blocked | blockers


async def find_match(session: AsyncSession, user_id: int) -> int | None:
    async with _match_lock:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        result_s = await session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        user_settings = result_s.scalar_one_or_none()

        excluded = await get_blocked_ids(session, user_id)
        excluded.add(user_id)

        query = (
            select(User)
            .join(UserSettings, UserSettings.user_id == User.id, isouter=True)
            .where(
                and_(
                    User.in_queue == True,
                    User.id != user_id,
                    User.is_banned == False,
                    User.current_match_id == None,
                    ~User.id.in_(excluded),
                )
            )
            .order_by(User.queue_joined_at.asc())
        )

        result = await session.execute(query)
        candidates = result.scalars().all()

        for candidate in candidates:
            cand_settings_res = await session.execute(
                select(UserSettings).where(UserSettings.user_id == candidate.id)
            )
            cand_settings = cand_settings_res.scalar_one_or_none()

            # Check if user's gender pref matches candidate
            if user_settings and user_settings.gender_pref:
                if candidate.gender and candidate.gender != user_settings.gender_pref:
                    continue

            # Check candidate's gender pref matches user
            if cand_settings and cand_settings.gender_pref:
                if user.gender and user.gender != cand_settings.gender_pref:
                    continue

            # Check country prefs
            if user_settings and user_settings.country_pref:
                if candidate.country and candidate.country != user_settings.country_pref:
                    continue
            if cand_settings and cand_settings.country_pref:
                if user.country and user.country != cand_settings.country_pref:
                    continue

            return candidate.id

        return None


async def create_match(session: AsyncSession, user1_id: int, user2_id: int) -> Match:
    match = Match(user1_id=user1_id, user2_id=user2_id)
    session.add(match)
    await session.flush()

    await session.execute(
        select(User).where(User.id.in_([user1_id, user2_id]))
    )

    result = await session.execute(select(User).where(User.id == user1_id))
    u1 = result.scalar_one()
    result2 = await session.execute(select(User).where(User.id == user2_id))
    u2 = result2.scalar_one()

    u1.in_queue = False
    u1.queue_joined_at = None
    u1.current_match_id = match.id
    u1.chat_count += 1

    u2.in_queue = False
    u2.queue_joined_at = None
    u2.current_match_id = match.id
    u2.chat_count += 1

    logger.info(f"Match created: {user1_id} <-> {user2_id} (match_id={match.id})")
    return match


async def end_match(session: AsyncSession, match_id: int, ended_by: int) -> tuple[int | None, int | None]:
    result = await session.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match or not match.is_active:
        return None, None

    match.is_active = False
    match.ended_at = datetime.utcnow()
    match.ended_by = ended_by

    result1 = await session.execute(select(User).where(User.id == match.user1_id))
    u1 = result1.scalar_one_or_none()
    result2 = await session.execute(select(User).where(User.id == match.user2_id))
    u2 = result2.scalar_one_or_none()

    other_id = None
    if u1:
        u1.current_match_id = None
    if u2:
        u2.current_match_id = None

    if u1 and u2:
        other_id = match.user2_id if ended_by == match.user1_id else match.user1_id

    logger.info(f"Match {match_id} ended by {ended_by}")
    return match.user1_id, match.user2_id


async def get_partner_id(session: AsyncSession, user_id: int) -> int | None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.current_match_id:
        return None

    result2 = await session.execute(select(Match).where(Match.id == user.current_match_id))
    match = result2.scalar_one_or_none()
    if not match or not match.is_active:
        return None

    return match.user2_id if match.user1_id == user_id else match.user1_id


async def increment_match_messages(session: AsyncSession, match_id: int):
    result = await session.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match:
        match.message_count += 1


async def join_queue(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.in_queue = True
        user.queue_joined_at = datetime.utcnow()


async def leave_queue(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.in_queue = False
        user.queue_joined_at = None
