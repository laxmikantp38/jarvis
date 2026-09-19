"""One inbound path, whatever channel carried the message (AD-6)."""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from aos.app.intake.router import Intake
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


def build(triggers: list[Trigger] | None = None) -> tuple[Intake, list[str]]:
    replies: list[str] = []
    intake = Intake(
        triggers=FakeTriggers(triggers or []),
        zone=KOLKATA,
        agent_name="Friday",
        now=lambda: NOW,
    )
    return intake, replies


def message(text: str, channel: str = "telegram") -> InboundMessage:
    return InboundMessage(
        channel=channel,
        external_id="1",
        sender="42",
        text=text,
        received_at=NOW,
    )


def test_next_lists_what_is_coming() -> None:
    intake, replies = build([a_trigger("wake", 1), a_trigger("gym", 3)])
    intake.handle(message("next"), replies.append)

    assert "Wake" in replies[0]
    assert replies[0].index("Wake") < replies[0].index("Gym"), "soonest first"


def test_next_ignores_disabled_triggers() -> None:
    intake, replies = build([a_trigger("wake", 1, enabled=False)])
    intake.handle(message("next"), replies.append)

    assert "Nothing is scheduled" in replies[0]


def test_status_names_the_configured_assistant() -> None:
    intake, replies = build([a_trigger("wake", 1)])
    intake.handle(message("status"), replies.append)

    assert "Friday" in replies[0], "the name comes from configuration, not code"


def test_an_unknown_command_says_so_rather_than_inventing() -> None:
    intake, replies = build()
    intake.handle(message("book me a flight to Goa"), replies.append)

    assert "don't understand" in replies[0]
    assert "next" in replies[0], "and it says what it can do"


def test_commands_are_case_and_space_insensitive() -> None:
    intake, replies = build([a_trigger("wake", 1)])
    intake.handle(message("  NEXT  "), replies.append)

    assert "Wake" in replies[0]


def test_every_channel_uses_the_same_path() -> None:
    """A capability added once works from every channel."""
    intake, replies = build([a_trigger("wake", 1)])
    for channel in ("telegram", "whatsapp", "relay"):
        intake.handle(message("status", channel=channel), replies.append)

    assert len(replies) == 3
    assert len(set(replies)) == 1, "same question, same answer, whatever carried it"
