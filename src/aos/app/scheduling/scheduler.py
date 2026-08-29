"""The tick: find what is due, hand it to the notifier, advance past it.

Knows nothing about channels (AD-11) and calls no model (AD-1), so its whole
behaviour is reproducible from a clock and a repository.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from aos.domain.scheduling.trigger import Trigger
from aos.ports.notification import NotificationRequest, Notifier, dedupe_key
from aos.ports.persistence.triggers import TriggerRepository

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MissedOccurrence:
    key: str
    title: str
    due_at: datetime
    reraised: bool


class Scheduler:
    def __init__(
        self,
        triggers: TriggerRepository,
        notifier: Notifier,
        zone: ZoneInfo,
    ) -> None:
        self._triggers = triggers
        self._notifier = notifier
        self._zone = zone

    def prepare(self, now: datetime) -> None:
        """Give any unscheduled trigger its first due instant."""
        for trigger in self._triggers.all():
            scheduled = trigger.scheduled_from(now, self._zone)
            if scheduled is not trigger:
                self._triggers.save(scheduled)

    def catch_up(self, now: datetime) -> list[MissedOccurrence]:
        """Handle occurrences that came due while the machine was off (FR-28).

        Anything important is re-raised as late; the merely informational is
        discarded rather than dumped on the user in a heap at breakfast.
        """
        missed: list[MissedOccurrence] = []
        for trigger in self._triggers.all():
            if not trigger.enabled or trigger.next_due_at is None:
                continue
            if trigger.next_due_at > now:
                continue
            reraise = trigger.notification_class.survives_downtime
            if reraise:
                self._submit(trigger, trigger.next_due_at, late=True)
            missed.append(
                MissedOccurrence(
                    key=trigger.key,
                    title=trigger.title,
                    due_at=trigger.next_due_at,
                    reraised=reraise,
                )
            )
            advanced = (
                trigger.fired(now, self._zone) if reraise else trigger.rescheduled(now, self._zone)
            )
            self._triggers.save(advanced)
        return missed

    def tick(self, now: datetime) -> int:
        """Fire everything due at this instant. Returns how many fired."""
        fired = 0
        for trigger in self._triggers.all():
            if not trigger.is_due(now):
                continue
            assert trigger.next_due_at is not None  # noqa: S101 - guarded by is_due
            self._submit(trigger, trigger.next_due_at, late=False)
            self._triggers.save(trigger.fired(now, self._zone))
            fired += 1
        return fired

    def _submit(self, trigger: Trigger, due_at: datetime, *, late: bool) -> None:
        self._notifier.submit(
            NotificationRequest(
                dedupe_key=dedupe_key(trigger.key, due_at),
                title=trigger.title,
                body=trigger.body,
                notification_class=trigger.notification_class,
                due_at=due_at,
                late=late,
            )
        )
        log.info(
            "trigger %s due at %s%s",
            trigger.key,
            due_at.isoformat(),
            " (late)" if late else "",
        )
