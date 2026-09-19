"""The morning look at whether tonight has anything to publish.

Runs once a day, in the morning, because the whole value is finding out while
there is still a day in which to act. Silent when everything is covered.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from aos.domain.content.footage import assess
from aos.domain.scheduling.trigger import NotificationClass
from aos.ports.notification import NotificationRequest, Notifier
from aos.ports.persistence.content import DailyCheckLog, FootageRepository

log = logging.getLogger(__name__)

CHECK_NAME = "footage"


@dataclass(frozen=True)
class FootageWatch:
    footage: FootageRepository
    checks: DailyCheckLog
    notifier: Notifier
    zone: ZoneInfo
    check_at: time
    horizon_days: int

    def run_if_due(self, now: datetime) -> bool:
        """Returns True when the check actually ran."""
        local = now.astimezone(self.zone)
        today = local.date().isoformat()

        if local.time() < self.check_at:
            return False
        if self.checks.last_run(CHECK_NAME) == today:
            return False

        # Marked before notifying: a crash mid-notification must not produce a
        # second warning on restart.
        self.checks.mark_run(CHECK_NAME, today)
        self._assess(local)
        return True

    def _assess(self, local: datetime) -> None:
        shortfall = assess(self.footage.get(), local.date(), self.horizon_days)
        if shortfall is None:
            log.info("footage check: covered for the next %d days", self.horizon_days)
            return

        log.info("footage check: %d days covered", shortfall.days_covered)
        self.notifier.submit(
            NotificationRequest(
                dedupe_key=f"{CHECK_NAME}@{local.date().isoformat()}",
                title="Footage" if not shortfall.tonight else "No footage for tonight",
                body=shortfall.describe(),
                notification_class=(
                    NotificationClass.IMPORTANT if shortfall.tonight else NotificationClass.NORMAL
                ),
                due_at=local,
            )
        )
