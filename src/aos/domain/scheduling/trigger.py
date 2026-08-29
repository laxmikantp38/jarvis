"""A scheduled trigger: the routine, held as data rather than code.

Every trigger is individually editable and disableable, because a routine is
the user's, not the program's.

`next_due_at` is persisted rather than recomputed by whoever happens to ask.
It has exactly one writer, the scheduler, and carries the schedule it was
derived from (AD-22). That is also what makes a double fire impossible across
a restart: the next due instant is a fact on disk, not an inference.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from aos.domain.scheduling.recurrence import Recurrence, next_occurrence


class NotificationClass(StrEnum):
    """Determines channel, timing, and whether it may interrupt."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    NORMAL = "normal"
    INFORMATIONAL = "informational"

    @property
    def may_interrupt(self) -> bool:
        return self is NotificationClass.CRITICAL

    @property
    def survives_downtime(self) -> bool:
        """Whether an occurrence missed while down is worth re-raising."""
        return self in {NotificationClass.CRITICAL, NotificationClass.IMPORTANT}


@dataclass(frozen=True, slots=True)
class Trigger:
    key: str
    """Stable identifier, and the basis of the notification dedupe key (AD-23)."""

    title: str
    body: str
    recurrence: Recurrence
    notification_class: NotificationClass = NotificationClass.NORMAL
    enabled: bool = True
    last_fired_at: datetime | None = None
    next_due_at: datetime | None = None

    def scheduled_from(self, now: datetime, zone: ZoneInfo) -> Trigger:
        """Give an unscheduled trigger its first due instant.

        A trigger created at 14:00 does not fire this morning's 06:00.
        """
        if self.next_due_at is not None:
            return self
        return replace(self, next_due_at=next_occurrence(now, self.recurrence, zone))

    def is_due(self, now: datetime) -> bool:
        return self.enabled and self.next_due_at is not None and self.next_due_at <= now

    def fired(self, now: datetime, zone: ZoneInfo) -> Trigger:
        """Record the fire and advance past it, so the same instant cannot repeat."""
        return replace(
            self,
            last_fired_at=now,
            next_due_at=next_occurrence(now, self.recurrence, zone),
        )

    def rescheduled(self, now: datetime, zone: ZoneInfo) -> Trigger:
        """Advance without firing - used for occurrences missed while the machine was off."""
        return replace(self, next_due_at=next_occurrence(now, self.recurrence, zone))
