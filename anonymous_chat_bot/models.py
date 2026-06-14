from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, Float
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=False, default="")
    age_range = Column(String(10), nullable=True)
    gender = Column(String(30), nullable=True)
    country = Column(String(50), nullable=True)
    chat_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_banned = Column(Boolean, default=False)
    ban_until = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    in_queue = Column(Boolean, default=False)
    queue_joined_at = Column(DateTime, nullable=True)
    current_match_id = Column(BigInteger, nullable=True)
    report_count = Column(Integer, default=0)

    # Settings relationship
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_reports = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    received_reports = relationship("Report", foreign_keys="Report.reported_id", back_populates="reported")
    blocks_made = relationship("Block", foreign_keys="Block.blocker_id", back_populates="blocker")
    bans = relationship("Ban", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    gender_pref = Column(String(30), nullable=True)  # None = any
    country_pref = Column(String(50), nullable=True)  # None = any
    notifications = Column(Boolean, default=True)
    hide_gender = Column(Boolean, default=False)
    hide_country = Column(Boolean, default=False)
    hide_age = Column(Boolean, default=False)

    user = relationship("User", back_populates="settings")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    user2_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    ended_by = Column(BigInteger, nullable=True)
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reported_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    reason = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(BigInteger, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    action_taken = Column(String(100), nullable=True)

    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="sent_reports")
    reported = relationship("User", foreign_keys=[reported_id], back_populates="received_reports")


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blocker_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    blocked_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocks_made")


class Ban(Base):
    __tablename__ = "bans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    admin_id = Column(BigInteger, nullable=True)
    reason = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # None = permanent
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="bans")


class RateLimit(Base):
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    window_start = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    last_message = Column(DateTime, default=datetime.utcnow)
