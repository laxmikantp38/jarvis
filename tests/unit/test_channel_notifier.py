"""Delivery, fallback, and the record of what happened."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from aos.adapters.notification.channel_notifier import ChannelNotifier
from aos.domain.notification.policy import NotificationPolicy, TimeWindow
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


KOLKATA = ZoneInfo("Asia/Kolkata")
MIDDAY = datetime(2026, 9, 19, 12, 0, tzinfo=KOLKATA).astimezone(UTC)


def notifier(
    channels: list[FakeChannel],
    *,
    budget: int = 12,
    now: datetime = MIDDAY,
    quiet: str = "",
) -> ChannelNotifier:
    return ChannelNotifier(
        channels=channels,  # type: ignore[arg-type]
        policy=NotificationPolicy(
            daily_budget=budget,
            quiet_hours=TimeWindow.parse(quiet) if quiet else None,
        ),
        zone=KOLKATA,
        now=lambda: now,
    )


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
        notifier([])


def test_the_first_working_channel_wins() -> None:
    primary, fallback = FakeChannel("telegram"), FakeChannel("console")
    notifier([primary, fallback]).submit(a_request())

    assert len(primary.sent) == 1
    assert fallback.sent == [], "a working primary must not also hit the fallback"


def test_a_failed_primary_falls_through() -> None:
    primary = FakeChannel("telegram", works=False)
    fallback = FakeChannel("console")
    notifier([primary, fallback]).submit(a_request())

    assert len(primary.sent) == 1
    assert len(fallback.sent) == 1


def test_the_same_occurrence_is_delivered_once(caplog: pytest.LogCaptureFixture) -> None:
    """AD-23: two producers raising the same real event reach the user once."""
    channel = FakeChannel("telegram")
    sender = notifier([channel])

    sender.submit(a_request())
    sender.submit(a_request())

    assert len(channel.sent) == 1


def test_different_occurrences_both_get_through() -> None:
    channel = FakeChannel("telegram")
    sender = notifier([channel])

    sender.submit(a_request("wake@2026-08-30T00:30:00+00:00"))
    sender.submit(a_request("wake@2026-08-31T00:30:00+00:00"))

    assert len(channel.sent) == 2


def test_a_failure_is_recorded_not_swallowed(caplog: pytest.LogCaptureFixture) -> None:
    """A silent failure is indistinguishable from nothing having been due."""
    with caplog.at_level("WARNING"):
        notifier([FakeChannel("telegram", works=False)]).submit(a_request())

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
    notifier([channel]).submit(request)

    assert "missed while I was off" in channel.sent[0].rendered()


class TestHolding:
    """Quiet hours hold a nudge; they do not drop it."""

    def test_an_ordinary_nudge_at_night_is_not_sent(self) -> None:
        channel = FakeChannel("telegram")
        two_am = datetime(2026, 9, 19, 2, 0, tzinfo=KOLKATA).astimezone(UTC)
        sender = notifier([channel], now=two_am, quiet="23:45-05:45")

        sender.submit(
            NotificationRequest(
                dedupe_key="gym@1",
                title="Gym",
                body="",
                notification_class=NotificationClass.NORMAL,
                due_at=two_am,
            )
        )

        assert channel.sent == []
        assert sender.pending == 1
        assert sender.tally.deferred == 1

    def test_it_goes_out_once_the_window_closes(self) -> None:
        channel = FakeChannel("telegram")
        two_am = datetime(2026, 9, 19, 2, 0, tzinfo=KOLKATA).astimezone(UTC)
        clock = {"now": two_am}
        sender = ChannelNotifier(
            channels=[channel],  # type: ignore[list-item]
            policy=NotificationPolicy(daily_budget=12, quiet_hours=TimeWindow.parse("23:45-05:45")),
            zone=KOLKATA,
            now=lambda: clock["now"],
        )
        sender.submit(
            NotificationRequest(
                dedupe_key="gym@1",
                title="Gym",
                body="",
                notification_class=NotificationClass.NORMAL,
                due_at=two_am,
            )
        )
        assert channel.sent == []

        clock["now"] = datetime(2026, 9, 19, 6, 0, tzinfo=KOLKATA).astimezone(UTC)
        assert sender.release_due() == 1
        assert len(channel.sent) == 1
        assert sender.pending == 0

    def test_critical_is_never_held(self) -> None:
        channel = FakeChannel("telegram")
        two_am = datetime(2026, 9, 19, 2, 0, tzinfo=KOLKATA).astimezone(UTC)
        sender = notifier([channel], now=two_am, quiet="23:45-05:45")

        sender.submit(
            NotificationRequest(
                dedupe_key="wake@1",
                title="Morning",
                body="",
                notification_class=NotificationClass.CRITICAL,
                due_at=two_am,
            )
        )

        assert len(channel.sent) == 1


class TestBudget:
    def _ordinary(self, index: int) -> NotificationRequest:
        return NotificationRequest(
            dedupe_key=f"note@{index}",
            title=f"Note {index}",
            body="",
            notification_class=NotificationClass.NORMAL,
            due_at=MIDDAY,
        )

    def test_beyond_the_budget_the_rest_is_folded_up(self) -> None:
        channel = FakeChannel("telegram")
        sender = notifier([channel], budget=2)

        for index in range(5):
            sender.submit(self._ordinary(index))

        assert len(channel.sent) == 2, "the budget is a cap on interruptions"
        assert sender.tally.batched == 3

    def test_the_folded_ones_can_be_collected_for_a_briefing(self) -> None:
        sender = notifier([FakeChannel("telegram")], budget=1)
        for index in range(3):
            sender.submit(self._ordinary(index))

        batched = sender.drain_batched()

        assert len(batched) == 2
        assert sender.drain_batched() == [], "draining empties the queue"

    def test_the_tally_records_what_the_day_cost(self) -> None:
        channel = FakeChannel("telegram")
        sender = notifier([channel], budget=1)
        sender.submit(self._ordinary(0))
        sender.submit(self._ordinary(1))
        sender.submit(self._ordinary(0))  # duplicate

        assert sender.tally.delivered == 1
        assert sender.tally.batched == 1
        assert sender.tally.suppressed_duplicate == 1
