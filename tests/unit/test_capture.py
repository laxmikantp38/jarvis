"""Turning a line of text into tracked work."""

from __future__ import annotations

from datetime import UTC, datetime

from aos.app.work.capture import TaskCapture
from aos.domain.memory.classification import Confidentiality
from aos.domain.work.event import EventType
from aos.domain.work.project import Project
from aos.domain.work.task import Attention, Task

NOW = datetime(2026, 9, 19, 10, 0, tzinfo=UTC)


class FakeProjects:
    def __init__(self) -> None:
        self.items = [
            Project(key="railzy", name="Railzy", objective=""),
            Project(key="freelance", name="Freelance client", objective=""),
            Project(key="personal", name="Personal", objective=""),
        ]

    def all(self) -> list[Project]:
        return list(self.items)

    def get(self, key: str) -> Project | None:
        return next((p for p in self.items if p.key == key), None)

    def add_missing(self, projects: list[Project]) -> list[str]:
        return []


class FakeTasks:
    def __init__(self) -> None:
        self.saved: list[Task] = []

    def open_tasks(self, project_key: str | None = None) -> list[Task]:
        return list(self.saved)

    def get(self, task_id: str) -> Task | None:
        return next((t for t in self.saved if t.id == task_id), None)

    def save(self, task: Task) -> None:
        self.saved.append(task)


class FakeEvents:
    def __init__(self) -> None:
        self.appended: list[object] = []

    def append(self, event: object) -> None:
        self.appended.append(event)

    def recent(self, limit: int = 50) -> list[object]:
        return list(self.appended)


def capture() -> tuple[TaskCapture, FakeTasks, FakeEvents]:
    tasks, events = FakeTasks(), FakeEvents()
    return (
        TaskCapture(
            projects=FakeProjects(),  # type: ignore[arg-type]
            tasks=tasks,  # type: ignore[arg-type]
            events=events,  # type: ignore[arg-type]
            now=lambda: NOW,
        ),
        tasks,
        events,
    )


class TestAttribution:
    def test_an_explicit_prefix_wins(self) -> None:
        engine, _, _ = capture()
        result = engine.capture("railzy: fix the signup handler")

        assert result.task.project_key == "railzy"
        assert result.task.title == "fix the signup handler"
        assert result.guessed_project is False

    def test_a_project_mentioned_in_passing_is_inferred(self) -> None:
        engine, _, _ = capture()
        result = engine.capture("look at the railzy backlog")

        assert result.task.project_key == "railzy"
        assert result.guessed_project is True, "a guess is flagged as a guess"

    def test_anything_unattributable_lands_in_personal(self) -> None:
        engine, _, _ = capture()
        assert engine.capture("book the car service").task.project_key == "personal"

    def test_an_unknown_prefix_is_not_treated_as_a_project(self) -> None:
        engine, _, _ = capture()
        result = engine.capture("note: buy milk")

        assert result.task.project_key == "personal"
        assert result.task.title == "note: buy milk"


class TestConfidentiality:
    def test_client_work_is_classified_without_being_asked(self) -> None:
        """The one class that could cost him a contract."""
        engine, _, _ = capture()
        result = engine.capture("freelance: prepare the standup notes")

        assert result.task.confidentiality is Confidentiality.CLIENT

    def test_ordinary_work_is_personal(self) -> None:
        engine, _, _ = capture()
        result = engine.capture("railzy: fix signup")

        assert result.task.confidentiality is Confidentiality.PERSONAL


class TestAttentionInference:
    def test_a_call_can_be_done_with_hands_busy(self) -> None:
        engine, _, _ = capture()
        assert engine.capture("call the accountant").task.attention is Attention.AUDIO

    def test_building_something_needs_a_screen(self) -> None:
        engine, _, _ = capture()
        assert engine.capture("build the export").task.attention is Attention.DEEP


class TestRecording:
    def test_capturing_appends_an_event(self) -> None:
        engine, tasks, events = capture()
        engine.capture("railzy: fix signup")

        assert len(tasks.saved) == 1
        assert len(events.appended) == 1
        assert events.appended[0].type is EventType.TASK_CREATED  # type: ignore[attr-defined]
