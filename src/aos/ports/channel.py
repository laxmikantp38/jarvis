"""A channel carries messages both ways (AD-6).

Send-only would have to be rebuilt the moment a reply needs to do something,
so receive is part of the contract from the start. Inbound messages from every
channel converge on one intake path; no channel gets a private route into the
system.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from aos.domain.scheduling.trigger import NotificationClass


@dataclass(frozen=True, slots=True)
class OutboundMessage:
    dedupe_key: str
    title: str
    body: str
    notification_class: NotificationClass
    late: bool = False

    def rendered(self) -> str:
        prefix = "(missed while I was off) " if self.late else ""
        return f"{prefix}{self.title}\n{self.body}".strip()


@dataclass(frozen=True, slots=True)
class InboundMessage:
    channel: str
    external_id: str
    """The channel's own message id, used to discard duplicates on reconnect."""

    sender: str
    text: str
    received_at: datetime


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    channel: str
    delivered: bool
    detail: str | None = None


MessageHandler = Callable[[InboundMessage], None]


class Channel(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def reaches_a_real_person(self) -> bool:
        """False for stubs. A development run must never message anyone."""
        ...

    def send(self, message: OutboundMessage) -> DeliveryResult: ...

    def start(self, on_message: MessageHandler) -> None:
        """Begin receiving. Outbound-only connection: no inbound port (AD-5)."""
        ...

    def stop(self) -> None: ...
