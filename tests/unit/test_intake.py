"""One inbound path, whatever channel carried the message (AD-6)."""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from aos.app.finance.goals import Goals, seed_goals
from aos.app.finance.ledger import Ledger
from aos.app.intake.money_commands import MoneyCommands
from aos.app.intake.router import Intake
from aos.app.work.capture import TaskCapture
from aos.domain.content.footage import FootageReserve
from aos.domain.scheduling.recurrence import EVERY_DAY, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger
from aos.domain.work.project import Project
from aos.domain.work.task import Task
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


class FakeProjects:
    def __init__(self) -> None:
        self.items = [
            Project(key="railzy", name="Railzy", objective="Live product."),
            Project(key="personal", name="Personal", objective="Everything else."),
        ]

    def all(self) -> list[Project]:
        return list(self.items)

    def get(self, key: str) -> Project | None:
        return next((p for p in self.items if p.key == key), None)

    def add_missing(self, projects: list[Project]) -> list[str]:
        return []


class FakeTasks:
    def __init__(self) -> None:
        self.items: list[Task] = []

    def open_tasks(self, project_key: str | None = None) -> list[Task]:
        return [t for t in self.items if t.is_open]

    def get(self, task_id: str) -> Task | None:
        return next((t for t in self.items if t.id == task_id), None)

    def save(self, task: Task) -> None:
        self.items = [t for t in self.items if t.id != task.id] + [task]


class FakeEvents:
    def __init__(self) -> None:
        self.appended: list[object] = []

    def append(self, event: object) -> None:
        self.appended.append(event)

    def recent(self, limit: int = 50) -> list[object]:
        return list(self.appended)


class _Revenue:
    def __init__(self) -> None:
        self.records: list = []

    def add(self, record: object) -> None:
        self.records.append(record)

    def all(self, certainty: object = None) -> list:
        return list(self.records)

    def since(self, start: object) -> list:
        return list(self.records)


class _Expenses(_Revenue):
    pass


class _Goals:
    def __init__(self) -> None:
        from datetime import date

        self.items = {
            g.key: g for g in seed_goals(None, date(2026, 8, 10), date(2027, 2, 10))
        }

    def all(self) -> list:
        return list(self.items.values())

    def get(self, key: str):
        return self.items.get(key)

    def children_of(self, key: str) -> list:
        return [g for g in self.items.values() if g.parent_key == key]

    def save(self, goal) -> None:
        self.items[goal.key] = goal

    def add_missing(self, goals: list) -> list[str]:
        return []


def _money_commands() -> MoneyCommands:
    revenue = _Revenue()
    ledger = Ledger(
        revenue=revenue,  # type: ignore[arg-type]
        expenses=_Expenses(),  # type: ignore[arg-type]
        events=FakeEvents(),  # type: ignore[arg-type]
        now=lambda: NOW,
    )
    return MoneyCommands(
        ledger=ledger,
        goals=Goals(goals=_Goals(), revenue=revenue, now=lambda: NOW),  # type: ignore[arg-type]
    )


def build(
    triggers: list[Trigger] | None = None, clips: int = 0
) -> tuple[Intake, list[str], FakeFootage]:
    replies: list[str] = []
    footage = FakeFootage(clips)
    projects = FakeProjects()
    tasks = FakeTasks()
    intake = Intake(
        triggers=FakeTriggers(triggers or []),
        footage=footage,
        projects=projects,
        tasks=tasks,
        money=_money_commands(),
        capture=TaskCapture(
            projects=projects,  # type: ignore[arg-type]
            tasks=tasks,  # type: ignore[arg-type]
            events=FakeEvents(),  # type: ignore[arg-type]
            now=lambda: NOW,
        ),
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
    assert "help" in replies[0], "and it points at what it can do"


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


class TestMoneyCommands:
    def test_an_earning_is_logged_from_a_sentence(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("earned 40k from client"), replies.append)

        assert "40,000" in replies[0] or "40.00" in replies[0]
        assert "freelance" in replies[0], "client maps to the freelance stream"

    def test_shorthand_scales_are_understood(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("earned 2 lakh from consulting"), replies.append)

        assert "lakh" in replies[0]

    def test_an_invoice_is_expected_rather_than_banked(self) -> None:
        """Money that has not arrived must not look like money that has."""
        intake, replies, _ = build()
        intake.handle(message("earned 50k expected from consulting"), replies.append)

        assert "Expected" in replies[0]

    def test_an_amountless_message_asks_for_one(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("earned some money"), replies.append)

        assert "How much?" in replies[0]

    def test_an_expense_is_logged_against_a_project(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("spent 2400 on tools for railzy"), replies.append)

        assert "railzy" in replies[0]

    def test_the_position_shows_gross_spent_and_net(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("money"), replies.append)

        assert "Gross" in replies[0]
        assert "Net" in replies[0]

    def test_a_goal_with_no_target_says_so_rather_than_showing_zero(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("goal"), replies.append)

        assert "No target set" in replies[0]

    def test_help_lists_the_money_commands(self) -> None:
        intake, replies, _ = build()
        intake.handle(message("help"), replies.append)

        assert "earned" in replies[0]
        assert "goal" in replies[0]


class TestDispatch:
    def test_task_and_tasks_are_different_commands(self) -> None:
        """A prefix matcher that ignored word boundaries would confuse these."""
        intake, replies, _ = build()
        intake.handle(message("tasks"), replies.append)
        intake.handle(message("task buy milk"), replies.append)

        assert "Nothing open" in replies[0]
        assert "Noted against" in replies[1]
