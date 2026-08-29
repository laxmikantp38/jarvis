"""The default routine, seeded once on first run.

These are starting values, not a fixed schedule. Each is editable and
disableable, and seeding never overwrites one the user has already changed.
"""

from __future__ import annotations

from datetime import time

from aos.domain.scheduling.recurrence import EVERY_DAY, WEEKDAYS, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger


def default_routine() -> list[Trigger]:
    return [
        Trigger(
            key="wake",
            title="Morning",
            body="Time to get up.",
            recurrence=Recurrence(at=time(6, 0), days=EVERY_DAY),
            # Critical: this one is allowed to interrupt, and is re-raised if
            # the machine was off when it came due.
            notification_class=NotificationClass.CRITICAL,
        ),
        Trigger(
            key="gym-leave",
            title="Gym",
            body="Head out now to stay on schedule.",
            recurrence=Recurrence(at=time(7, 30), days=EVERY_DAY),
            notification_class=NotificationClass.IMPORTANT,
        ),
        Trigger(
            key="gym-return",
            title="Wrap up at the gym",
            body="Leave now to be ready for the day.",
            recurrence=Recurrence(at=time(9, 10), days=EVERY_DAY),
            notification_class=NotificationClass.NORMAL,
        ),
        Trigger(
            key="client-standup",
            title="Client standup",
            body="Standup call in a few minutes.",
            recurrence=Recurrence(at=time(19, 50), days=WEEKDAYS),
            notification_class=NotificationClass.IMPORTANT,
        ),
    ]
