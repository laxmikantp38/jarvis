"""One inbound path, whatever channel carried the message (AD-6)."""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from aos.app.intake.router import Intake
from aos.domain.content.footage import FootageReserve
from aos.domain.scheduling.recurrence import EVERY_DAY, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger
from aos.ports.channel import InboundMessage

KOLKATA = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 8, 29, 18, 0, tzinfo=UTC)


class FakeTriggers:
    def __init__(self, triggers: list[Trigger]) -> None:
        self._triggers = triggers

    def all(self) -> list[Trigger]:
        return list(self._triggers)

    def get(self, key: str) -> Trigger | None:
        return next((t for t in self._triggers if t.key == key), None)

    def save(self, trigger: Trigger) -> None: ...

    def add_missing(self, triggers: list[Trigger]) -> list[str]:
        return []


def a_trigger(key: str, hour: int, *, enabled: bool = True) -> Trigger:
    return Trigger(
        key=key,
        title=key.title(),
        body="",
        recurrence=Recurrence(at=time(hour, 0), days=EVERY_DAY),
        notification_class=NotificationClass.NORMAL,
        enabled=enabled,
        next_due_at=datetime(2026, 8, 30, hour, 0, tzinfo=UTC),
    )


class FakeFootage:
    def __init__(self, clips: int = 0) -> None:
        self.reserve = FootageReserve(clips_available=clips)

    def get(self) -> FootageReserve:
        return self.reserve

    def save(self, reserve: FootageReserve) -> None:
        self.reserve = reserve


def build(
    triggers: list[Trigger] | None = None, clips: int = 0
) -> tuple[Intake, list[str], FakeFootage]:
    replies: list[str] = []
    footage = FakeFootage(clips)
    intake = Intake(
        triggers=FakeTriggers(triggers or []),
        footage=footage,
        zone=KOLKATA,
        agent_name="Friday",
        horizon_days=2,
        now=lambda: NOW,
    )
    return intake, replies, footage


def message(text: str, channel: str = "telegram") -> InboundMessage:
    return InboundMessage(
        channel=channel,
        external_id="1",
        sender="42",
        text=text,
        received_at=NOW,
    )


def test_next_lists_what_is_coming() -> None:
    intake, replies, _ = build([a_trigger("wake", 1), a_trigger("gym", 3)])
    intake.handle(message("next"), replies.append)

    assert "Wake" in replies[0]
    assert replies[0].index("Wake") < replies[0].index("Gym"), "soonest first"


def test_next_ignores_disabled_triggers() -> None:
    intake, replies, _ = build([a_trigger("wake", 1, enabled=False)])
    intake.handle(message("next"), replies.append)

    assert "Nothing is scheduled" in replies[0]


def test_status_names_the_configured_assistant() -> None:
    intake, replies, _ = build([a_trigger("wake", 1)])
    intake.handle(message("status"), replies.append)

    assert "Friday" in replies[0], "the name comes from configuration, not code"


def test_an_unknown_command_says_so_rather_than_inventing() -> None:
    intake, replies, _ = build()
    intake.handle(message("book me a flight to Goa"), replies.append)

    assert "don't understand" in replies[0]
    assert "next" in replies[0], "and it says what it can do"


def test_commands_are_case_and_space_insensitive() -> None:
    intake, replies, _ = build([a_trigger("wake", 1)])
    intake.handle(message("  NEXT  "), replies.append)

    assert "Wake" in replies[0]


def test_every_channel_uses_the_same_path() -> None:
    """A capability added once works from every channel."""
    intake, replies, _ = build([a_trigger("wake", 1)])
    for channel in ("telegram", "whatsapp", "relay"):
        intake.handle(message("status", channel=channel), replies.append)

    assert len(replies) == 3
    assert len(set(replies)) == 1, "same question, same answer, whatever carried it"


class TestFootageCommands:
    def test_asking_reports_the_reserve(self) -> None:
        intake, replies, _ = build(clips=5)
        intake.handle(message("footage"), replies.append)

        assert "5 days of footage" in replies[0]

    def test_an_empty_reserve_warns_about_tonight(self) -> None:
        intake, replies, _ = build(clips=0)
        intake.handle(message("footage"), replies.append)

        assert "Tonight" in replies[0]

    def test_a_number_sets_the_reserve(self) -> None:
        intake, replies, footage = build(clips=0)
        intake.handle(message("footage 4"), replies.append)

        assert footage.reserve.clips_available == 4

    def test_a_plus_adds_to_it(self) -> None:
        intake, replies, footage = build(clips=2)
        intake.handle(message("footage +3"), replies.append)

        assert footage.reserve.clips_available == 5

    def test_a_minus_spends_from_it(self) -> None:
        intake, replies, footage = build(clips=5)
        intake.handle(message("footage -2"), replies.append)

        assert footage.reserve.clips_available == 3

    def test_nonsense_is_refused_without_changing_anything(self) -> None:
        intake, replies, footage = build(clips=3)
        intake.handle(message("footage lots"), replies.append)

        assert footage.reserve.clips_available == 3
        assert "Tell me a number" in replies[0]
