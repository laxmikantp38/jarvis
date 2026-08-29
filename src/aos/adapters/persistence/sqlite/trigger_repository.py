"""Translation between stored rows and domain triggers.

SQLite has no timezone-aware column, so UTC is attached on the way out rather
than assumed. A naive datetime never escapes this module.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from aos.adapters.persistence.sqlite.models import TriggerRow
from aos.domain.scheduling.recurrence import Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger


def _as_utc(moment: datetime | None) -> datetime | None:
    if moment is None:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _to_domain(row: TriggerRow) -> Trigger:
    return Trigger(
        key=row.key,
        title=row.title,
        body=row.body,
        recurrence=Recurrence(
            at=row.at,
            days=frozenset(int(d) for d in row.days.split(",") if d),
        ),
        notification_class=NotificationClass(row.notification_class),
        enabled=row.enabled,
        last_fired_at=_as_utc(row.last_fired_at),
        next_due_at=_as_utc(row.next_due_at),
    )


def _apply(row: TriggerRow, trigger: Trigger) -> None:
    row.title = trigger.title
    row.body = trigger.body
    row.at = trigger.recurrence.at
    row.days = ",".join(str(d) for d in sorted(trigger.recurrence.days))
    row.notification_class = trigger.notification_class.value
    row.enabled = trigger.enabled
    row.last_fired_at = trigger.last_fired_at
    row.next_due_at = trigger.next_due_at


class SqliteTriggerRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def all(self) -> list[Trigger]:
        with self._sessions() as session:
            rows = session.scalars(select(TriggerRow).order_by(TriggerRow.key)).all()
            return [_to_domain(row) for row in rows]

    def get(self, key: str) -> Trigger | None:
        with self._sessions() as session:
            row = session.get(TriggerRow, key)
            return _to_domain(row) if row else None

    def save(self, trigger: Trigger) -> None:
        with self._sessions() as session, session.begin():
            row = session.get(TriggerRow, trigger.key)
            if row is None:
                row = TriggerRow(key=trigger.key)
                session.add(row)
            _apply(row, trigger)

    def add_missing(self, triggers: list[Trigger]) -> list[str]:
        inserted: list[str] = []
        with self._sessions() as session, session.begin():
            existing = set(session.scalars(select(TriggerRow.key)).all())
            for trigger in triggers:
                if trigger.key in existing:
                    continue
                row = TriggerRow(key=trigger.key)
                _apply(row, trigger)
                session.add(row)
                inserted.append(trigger.key)
        return inserted
