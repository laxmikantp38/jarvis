"""SQLAlchemy tables. Nothing outside this package imports them (AD-2)."""

from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Integer, String, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TriggerRow(Base):
    __tablename__ = "trigger"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(2000))

    at: Mapped[time] = mapped_column(Time)
    days: Mapped[str] = mapped_column(String(16))
    """Weekday numbers as a sorted comma-separated list, e.g. "0,1,2,3,4"."""

    notification_class: Mapped[str] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Stored in UTC (AD-16). SQLite has no native timezone, so the adapter
    # attaches it on the way out rather than trusting the column.
    last_fired_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FootageReserveRow(Base):
    """One row. The reserve is a single running count, not a ledger."""

    __tablename__ = "footage_reserve"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    clips_available: Mapped[int] = mapped_column(Integer, default=0)
    clips_per_publish: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DailyCheckRow(Base):
    __tablename__ = "daily_check"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_local_day: Mapped[str] = mapped_column(String(10))
