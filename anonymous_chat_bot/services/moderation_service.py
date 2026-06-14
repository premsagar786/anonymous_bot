import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Report, Block, Ban
from config import config

logger = logging.getLogger(__name__)


async def create_report(
    session: AsyncSession,
    reporter_id: int,
    reported_id: int,
    match_id: int | None,
    reason: str,
) -> Report:
    report = Report(
        reporter_id=reporter_id,
        reported_id=reported_id,
        match_id=match_id,
        reason=reason,
    )
    session.add(report)

    # Auto-ban if too many reports
    result = await session.execute(
        select(Report).where(
            Report.reported_id == reported_id,
            Report.resolved == False,
        )
    )
    reports = result.scalars().all()

    if len(reports) >= config.MAX_REPORTS_BEFORE_BAN:
        await apply_temp_ban(
            session,
            reported_id,
            admin_id=None,
            reason=f"Auto-ban: {len(reports)} reports received",
            hours=config.BAN_DURATION_HOURS,
        )
        logger.info(f"Auto-banned user {reported_id} after {len(reports)} reports")

    await session.flush()
    return report


async def create_block(session: AsyncSession, blocker_id: int, blocked_id: int) -> Block:
    result = await session.execute(
        select(Block).where(
            Block.blocker_id == blocker_id,
            Block.blocked_id == blocked_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
    session.add(block)
    await session.flush()
    logger.info(f"User {blocker_id} blocked {blocked_id}")
    return block


async def apply_temp_ban(
    session: AsyncSession,
    user_id: int,
    admin_id: int | None,
    reason: str,
    hours: int,
) -> Ban:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_banned = True
        user.ban_until = datetime.utcnow() + timedelta(hours=hours)

    ban = Ban(
        user_id=user_id,
        admin_id=admin_id,
        reason=reason,
        expires_at=datetime.utcnow() + timedelta(hours=hours),
    )
    session.add(ban)
    await session.flush()
    return ban


async def apply_perm_ban(
    session: AsyncSession,
    user_id: int,
    admin_id: int | None,
    reason: str,
) -> Ban:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_banned = True
        user.ban_until = None

    ban = Ban(
        user_id=user_id,
        admin_id=admin_id,
        reason=reason,
        expires_at=None,
    )
    session.add(ban)
    await session.flush()
    return ban


async def resolve_report(
    session: AsyncSession,
    report_id: int,
    admin_id: int,
    action: str,
) -> bool:
    result = await session.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        return False
    report.resolved = True
    report.resolved_by = admin_id
    report.resolved_at = datetime.utcnow()
    report.action_taken = action
    return True


async def get_pending_reports(session: AsyncSession) -> list[Report]:
    result = await session.execute(
        select(Report).where(Report.resolved == False).order_by(Report.created_at.desc()).limit(10)
    )
    return result.scalars().all()


async def get_recent_bans(session: AsyncSession) -> list[Ban]:
    result = await session.execute(
        select(Ban).where(Ban.is_active == True).order_by(Ban.created_at.desc()).limit(10)
    )
    return result.scalars().all()


async def unban_user(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    user.is_banned = False
    user.ban_until = None

    result2 = await session.execute(
        select(Ban).where(Ban.user_id == user_id, Ban.is_active == True)
    )
    for ban in result2.scalars().all():
        ban.is_active = False
    return True
