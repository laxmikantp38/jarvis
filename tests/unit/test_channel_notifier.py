"""Delivery, fallback, and the record of what happened."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aos.adapters.notification.channel_notifier import ChannelNotifier
from aos.domain.scheduling.trigger import NotificationClass
from aos.ports.channel import DeliveryResult, OutboundMessage
from aos.ports.notification import NotificationRequest


class FakeChannel:
    def __init__(self, name: str, *, works: bool = True) -> None:
        self._name = name
        self._works = works
        self.sent: list[OutboundMessage] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def reaches_a_real_person(self) -> bool:
        return True

    def send(self, message: OutboundMessage) -> DeliveryResult:
        self.sent.append(message)
        if self._works:
            return DeliveryResult(self._name, delivered=True)
        return DeliveryResult(self._name, delivered=False, detail="network unreachable")

    def start(self, on_message: object) -> None: ...

    def stop(self) -> None: ...


def a_request(key: str = "wake@2026-08-30T00:30:00+00:00") -> NotificationRequest:
    return NotificationRequest(
        dedupe_key=key,
        title="Morning",
        body="Time to get up.",
        notification_class=NotificationClass.CRITICAL,
        due_at=datetime(2026, 8, 30, 0, 30, tzinfo=UTC),
    )


def test_a_notifier_with_no_channel_is_rejected() -> None:
    """Silently delivering nothing is worse than failing to start."""
    with pytest.raises(ValueError, match="deliver nothing"):
        ChannelNotifier([])


def test_the_first_working_channel_wins() -> None:
    primary, fallback = FakeChannel("telegram"), FakeChannel("console")
    ChannelNotifier([primary, fallback]).submit(a_request())

    assert len(primary.sent) == 1
    assert fallback.sent == [], "a working primary must not also hit the fallback"


def test_a_failed_primary_falls_through() -> None:
    primary = FakeChannel("telegram", works=False)
    fallback = FakeChannel("console")
    ChannelNotifier([primary, fallback]).submit(a_request())

    assert len(primary.sent) == 1
    assert len(fallback.sent) == 1


def test_the_same_occurrence_is_delivered_once(caplog: pytest.LogCaptureFixture) -> None:
    """AD-23: two producers raising the same real event reach the user once."""
    channel = FakeChannel("telegram")
    notifier = ChannelNotifier([channel])

    notifier.submit(a_request())
    notifier.submit(a_request())

    assert len(channel.sent) == 1


def test_different_occurrences_both_get_through() -> None:
    channel = FakeChannel("telegram")
    notifier = ChannelNotifier([channel])

    notifier.submit(a_request("wake@2026-08-30T00:30:00+00:00"))
    notifier.submit(a_request("wake@2026-08-31T00:30:00+00:00"))

    assert len(channel.sent) == 2


def test_a_failure_is_recorded_not_swallowed(caplog: pytest.LogCaptureFixture) -> None:
    """A silent failure is indistinguishable from nothing having been due."""
    with caplog.at_level("WARNING"):
        ChannelNotifier([FakeChannel("telegram", works=False)]).submit(a_request())

    assert "network unreachable" in caplog.text
    assert "every channel failed" in caplog.text


def test_a_late_message_says_so() -> None:
    channel = FakeChannel("console")
    request = NotificationRequest(
        dedupe_key="wake@x",
        title="Morning",
        body="Time to get up.",
        notification_class=NotificationClass.CRITICAL,
        due_at=datetime(2026, 8, 30, 0, 30, tzinfo=UTC),
        late=True,
    )
    ChannelNotifier([channel]).submit(request)

    assert "missed while I was off" in channel.sent[0].rendered()
