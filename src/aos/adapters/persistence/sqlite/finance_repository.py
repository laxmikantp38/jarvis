from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from aos.adapters.persistence.sqlite.models import ExpenseRow, GoalRow, RevenueRow
from aos.domain.finance.money import Money
from aos.domain.finance.records import (
    Certainty,
    ExpenseCategory,
    ExpenseRecord,
    Recurrence,
    RevenueRecord,
    Stream,
)
from aos.domain.goals.goal import Goal, GoalStatus, GoalType, Rollup


def _utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


class SqliteRevenueRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def add(self, record: RevenueRecord) -> None:
        with self._sessions() as session, session.begin():
            session.add(
                RevenueRow(
                    id=record.id,
                    paise=record.amount.paise,
                    currency=record.amount.currency,
                    stream=record.stream.value,
                    certainty=record.certainty.value,
                    probability=record.probability,
                    occurred_on=record.occurred_on,
                    recorded_at=record.recorded_at,
                    note=record.note,
                )
            )

    def all(self, certainty: Certainty | None = None) -> list[RevenueRecord]:
        with self._sessions() as session:
            query = select(RevenueRow)
            if certainty is not None:
                query = query.where(RevenueRow.certainty == certainty.value)
            rows = session.scalars(query.order_by(RevenueRow.occurred_on)).all()
            return [self._to_domain(row) for row in rows]

    def since(self, start: date) -> list[RevenueRecord]:
        return [r for r in self.all() if r.occurred_on >= start]

    @staticmethod
    def _to_domain(row: RevenueRow) -> RevenueRecord:
        return RevenueRecord(
            id=row.id,
            amount=Money(row.paise, row.currency),
            stream=Stream(row.stream),
            occurred_on=row.occurred_on,
            recorded_at=_utc(row.recorded_at),
            certainty=Certainty(row.certainty),
            probability=row.probability,
            note=row.note,
        )


class SqliteExpenseRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def add(self, record: ExpenseRecord) -> None:
        with self._sessions() as session, session.begin():
            session.add(
                ExpenseRow(
                    id=record.id,
                    paise=record.amount.paise,
                    currency=record.amount.currency,
                    category=record.category.value,
                    project_key=record.project_key,
                    recurrence=record.recurrence.value,
                    occurred_on=record.occurred_on,
                    recorded_at=record.recorded_at,
                    note=record.note,
                )
            )

    def all(self) -> list[ExpenseRecord]:
        with self._sessions() as session:
            rows = session.scalars(select(ExpenseRow).order_by(ExpenseRow.occurred_on)).all()
            return [self._to_domain(row) for row in rows]

    def since(self, start: date) -> list[ExpenseRecord]:
        return [e for e in self.all() if e.occurred_on >= start]

    @staticmethod
    def _to_domain(row: ExpenseRow) -> ExpenseRecord:
        return ExpenseRecord(
            id=row.id,
            amount=Money(row.paise, row.currency),
            category=ExpenseCategory(row.category),
            occurred_on=row.occurred_on,
            recorded_at=_utc(row.recorded_at),
            project_key=row.project_key,
            recurrence=Recurrence(row.recurrence),
            note=row.note,
        )


class SqliteGoalRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def all(self) -> list[Goal]:
        with self._sessions() as session:
            rows = session.scalars(select(GoalRow).order_by(GoalRow.key)).all()
            return [self._to_domain(row) for row in rows]

    def get(self, key: str) -> Goal | None:
        with self._sessions() as session:
            row = session.get(GoalRow, key)
            return self._to_domain(row) if row else None

    def children_of(self, key: str) -> list[Goal]:
        return [goal for goal in self.all() if goal.parent_key == key]

    def save(self, goal: Goal) -> None:
        with self._sessions() as session, session.begin():
            row = session.get(GoalRow, goal.key)
            if row is None:
                row = GoalRow(key=goal.key)
                session.add(row)
            row.parent_key = goal.parent_key
            row.name = goal.name
            row.goal_type = goal.goal_type.value
            row.target = goal.target
            row.current = goal.current
            row.unit = goal.unit
            row.start_on = goal.start_on
            row.deadline = goal.deadline
            row.rollup = goal.rollup.value
            row.weight = goal.weight
            row.status = goal.status.value

    def add_missing(self, goals: list[Goal]) -> list[str]:
        """Seeding never overwrites a target the user has set."""
        inserted: list[str] = []
        existing = {goal.key for goal in self.all()}
        for goal in goals:
            if goal.key in existing:
                continue
            self.save(goal)
            inserted.append(goal.key)
        return inserted

    @staticmethod
    def _to_domain(row: GoalRow) -> Goal:
        return Goal(
            key=row.key,
            name=row.name,
            goal_type=GoalType(row.goal_type),
            start_on=row.start_on,
            deadline=row.deadline,
            parent_key=row.parent_key,
            target=row.target,
            unit=row.unit,
            current=row.current,
            rollup=Rollup(row.rollup),
            weight=row.weight,
            status=GoalStatus(row.status),
        )
