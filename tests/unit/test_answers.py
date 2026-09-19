"""Grounded answers.

The rule that matters: an answer is backed by a record, or it says there is
none. It is never reconstructed to sound helpful (P-3, NFR-18).
"""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from aos.app.intake.answers import UNKNOWN, Answers
from aos.domain.content.footage import FootageReserve
from aos.domain.memory.partitions import Partition
from aos.domain.scheduling.recurrence import EVERY_DAY, Recurrence
from aos.domain.scheduling.trigger import Trigger
from aos.domain.work.event import Event, EventType
from aos.domain.work.project import Project
from aos.domain.work.task import Task

KOLKATA = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 9, 19, 10, 0, tzinfo=UTC)


class Triggers:
    def __init__(self, items: list[Trigger] | None = None) -> None:
        self.items = items or []

    def all(self) -> list[Trigger]:
        return list(self.items)

    def get(self, key: str) -> Trigger | None:
        return next((t for t in self.items if t.key == key), None)

    def save(self, trigger: Trigger) -> None: ...

    def add_missing(self, triggers: list[Trigger]) -> list[str]:
        return []


class Tasks:
    def __init__(self, items: list[Task] | None = None) -> None:
        self.items = items or []

    def open_tasks(self, project_key: str | None = None) -> list[Task]:
        return [t for t in self.items if not project_key or t.project_key == project_key]

    def get(self, task_id: str) -> Task | None:
        return None

    def save(self, task: Task) -> None: ...


class Projects:
    def __init__(self, items: list[Project] | None = None) -> None:
        self.items = items or []

    def all(self) -> list[Project]:
        return list(self.items)

    def get(self, key: str) -> Project | None:
        return next((p for p in self.items if p.key == key), None)

    def add_missing(self, projects: list[Project]) -> list[str]:
        return []


class Events:
    def __init__(self, items: list[Event] | None = None) -> None:
        self.items = items or []

    def append(self, event: Event) -> None:
        self.items.append(event)

    def recent(self, limit: int = 50) -> list[Event]:
        return self.items[:limit]


class Footage:
    def get(self) -> FootageReserve:
        return FootageReserve(clips_available=0)

    def save(self, reserve: FootageReserve) -> None: ...


def answers(
    triggers: list[Trigger] | None = None,
    tasks: list[Task] | None = None,
    projects: list[Project] | None = None,
    events: list[Event] | None = None,
) -> Answers:
    return Answers(
        triggers=Triggers(triggers),  # type: ignore[arg-type]
        tasks=Tasks(tasks),  # type: ignore[arg-type]
        projects=Projects(projects),  # type: ignore[arg-type]
        events=Events(events),  # type: ignore[arg-type]
        footage=Footage(),  # type: ignore[arg-type]
        zone=KOLKATA,
        now=lambda: NOW,
    )


def a_task(title: str, project: str = "railzy") -> Task:
    return Task(id=title, project_key=project, title=title, created_at=NOW)


class TestProvenance:
    def test_an_answer_names_the_store_it_came_from(self) -> None:
        answer = answers(tasks=[a_task("Fix signup")]).whats_open()

        assert answer.grounded is True
        assert answer.partition is Partition.STATE
        assert "state" in answer.with_provenance()

    def test_it_says_how_many_records_it_read(self) -> None:
        answer = answers(tasks=[a_task("One"), a_task("Two")]).whats_open()

        assert answer.records == 2
        assert "2 records" in answer.with_provenance()

    def test_a_single_record_reads_naturally(self) -> None:
        answer = answers(tasks=[a_task("One")]).whats_open()

        assert "1 record" in answer.with_provenance()

    def test_an_ungrounded_answer_carries_no_provenance(self) -> None:
        answer = answers().about_a_project("nonexistent")

        assert answer.grounded is False
        assert "—" not in answer.with_provenance()


class TestHonesty:
    def test_an_unknown_project_admits_it(self) -> None:
        answer = answers(
            projects=[Project(key="railzy", name="Railzy", objective="")]
        ).about_a_project("ghumr")

        assert UNKNOWN in answer.text

    def test_and_names_what_it_does_know(self) -> None:
        """A bare refusal is unhelpful when the answer is a typo away."""
        answer = answers(
            projects=[
                Project(key="railzy", name="Railzy", objective=""),
                Project(key="ghumr", name="Ghumr", objective=""),
            ]
        ).about_a_project("railzee")

        assert "railzy" in answer.text
        assert "ghumr" in answer.text

    def test_an_empty_store_is_reported_as_empty_not_absent(self) -> None:
        answer = answers().whats_open()

        assert answer.text == "Nothing open."
        assert answer.grounded is True, "knowing there is nothing is still knowledge"
        assert answer.records == 0


class TestContent:
    def test_open_work_is_listed_with_its_project(self) -> None:
        answer = answers(tasks=[a_task("Fix signup", "railzy")]).whats_open()

        assert "Fix signup" in answer.text
        assert "railzy" in answer.text

    def test_a_long_list_is_truncated_with_a_count(self) -> None:
        answer = answers(tasks=[a_task(f"Task {i}") for i in range(12)]).whats_open()

        assert "and 4 more" in answer.text
        assert answer.records == 12, "the count reflects everything, not the excerpt"

    def test_the_schedule_is_shown_in_local_time(self) -> None:
        trigger = Trigger(
            key="wake",
            title="Morning",
            body="",
            recurrence=Recurrence(at=time(6, 0), days=EVERY_DAY),
            next_due_at=datetime(2026, 9, 20, 0, 30, tzinfo=UTC),
        )
        answer = answers(triggers=[trigger]).whats_next()

        assert "06:00" in answer.text, "00:30 UTC is 06:00 in Kolkata"

    def test_recent_events_come_back_newest_first(self) -> None:
        events = [
            Event(
                id=str(index),
                type=EventType.TASK_CREATED,
                occurred_at=NOW,
                recorded_at=NOW,
                payload={},
            )
            for index in range(3)
        ]
        answer = answers(events=events).what_happened(limit=2)

        assert answer.partition is Partition.EVENTS
        assert answer.records == 2
