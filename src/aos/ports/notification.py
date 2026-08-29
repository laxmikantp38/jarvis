"""What the scheduler produces. It never delivers anything itself (AD-11).

Swapping Telegram for a phone call, or lifting the notifier to a server later,
touches an adapter and nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from aos.domain.scheduling.trigger import NotificationClass


@dataclass(frozen=True, slots=True)
class NotificationRequest:
    dedupe_key: str
    """Deterministic: (trigger identity, target occurrence). Two producers raising
    the same real-world event collapse to one delivery (AD-23)."""

    title: str
    body: str
    notification_class: NotificationClass
    due_at: datetime
    late: bool = False
    """Raised after the fact, because the machine was off when it came due."""


class Notifier(Protocol):
    def submit(self, request: NotificationRequest) -> None:
        """Accept a request. Classification, budget, quiet hours and channel
        selection are the notifier's business, not the caller's."""
        ...


def dedupe_key(trigger_key: str, due_at: datetime) -> str:
    return f"{trigger_key}@{due_at.isoformat()}"
