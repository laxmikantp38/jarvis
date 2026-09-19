"""SQLAlchemy tables. Nothing outside this package imports them (AD-2)."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
)
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


class ProjectRow(Base):
    __tablename__ = "project"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    objective: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20))


class TaskRow(Base):
    __tablename__ = "task"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_key: Mapped[str] = mapped_column(String(32), ForeignKey("project.key"))
    title: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16))
    attention: Mapped[str] = mapped_column(String(16))
    # Not nullable by design: a permissive default is a leak waiting to happen.
    confidentiality: Mapped[str] = mapped_column(String(24))
    notes: Mapped[str] = mapped_column(String(4000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EventRow(Base):
    """Append-only, enforced by database triggers (AD-8)."""

    __tablename__ = "event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(40))
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    payload: Mapped[dict[str, str]] = mapped_column(JSON)
    project_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class UserFactRow(Base):
    __tablename__ = "user_fact"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(4000))
    confidentiality: Mapped[str] = mapped_column(String(24))
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class RevenueRow(Base):
    __tablename__ = "revenue_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paise: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    stream: Mapped[str] = mapped_column(String(24))
    certainty: Mapped[str] = mapped_column(String(16))
    probability: Mapped[float] = mapped_column(Float, default=1.0)
    occurred_on: Mapped[date] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    note: Mapped[str] = mapped_column(String(500), default="")


class ExpenseRow(Base):
    __tablename__ = "expense_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paise: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    category: Mapped[str] = mapped_column(String(24))
    project_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recurrence: Mapped[str] = mapped_column(String(16))
    occurred_on: Mapped[date] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    note: Mapped[str] = mapped_column(String(500), default="")


class GoalRow(Base):
    __tablename__ = "goal"

    key: Mapped[str] = mapped_column(String(48), primary_key=True)
    parent_key: Mapped[str | None] = mapped_column(String(48), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    goal_type: Mapped[str] = mapped_column(String(20))
    # Null is unallocated, reported as such and never as zero.
    target: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    current: Mapped[Decimal] = mapped_column(Numeric, default=0)
    unit: Mapped[str] = mapped_column(String(32), default="")
    start_on: Mapped[date] = mapped_column(Date)
    deadline: Mapped[date] = mapped_column(Date)
    rollup: Mapped[str] = mapped_column(String(16))
    weight: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16))
