"""The local interface.

Every section exists so the navigation does not lie, and the ones with no data
yet say so rather than rendering a zero (NFR-18).
"""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from aos.adapters.notification.channel_notifier import ChannelNotifier
from aos.adapters.system.settings import Settings
from aos.domain.content.footage import FootageReserve
from aos.domain.notification.policy import NotificationPolicy
from aos.domain.scheduling.recurrence import EVERY_DAY, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger
from aos.domain.work.event import Event, EventType
from aos.domain.work.project import Project, ProjectStatus
from aos.domain.work.task import Task
from aos.entrypoints.api.app import create_app
from aos.entrypoints.api.render import SECTIONS

KOLKATA = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 9, 19, 10, 0, tzinfo=UTC)


class Repo:
    """One stand-in covering every repository the pages read."""

    def __init__(
        self,
        triggers: list[Trigger] | None = None,
        tasks: list[Task] | None = None,
        projects: list[Project] | None = None,
        events: list[Event] | None = None,
        clips: int = 0,
    ) -> None:
        self._triggers = triggers or []
        self._tasks = tasks or []
        self._projects = projects or []
        self._events = events or []
        self._reserve = FootageReserve(clips_available=clips)
        self.facts_store: dict[str, str] = {}

    def all(self) -> list:  # triggers / projects share this name
        return self._triggers or self._projects

    def open_tasks(self, project_key: str | None = None) -> list[Task]:
        return list(self._tasks)

    def recent(self, limit: int = 50) -> list[Event]:
        return list(self._events)

    def get(self) -> FootageReserve:
        return self._reserve


class Triggers(Repo):
    def all(self) -> list[Trigger]:
        return list(self._triggers)


class Projects(Repo):
    def all(self) -> list[Project]:
        return list(self._projects)


class Facts:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self._values = values or {}

    def all(self) -> dict[str, str]:
        return dict(self._values)


class Channel:
    def __init__(self, name: str, *, real: bool) -> None:
        self._name, self._real = name, real

    @property
    def name(self) -> str:
        return self._name

    @property
    def reaches_a_real_person(self) -> bool:
        return self._real

    def send(self, message: object) -> object:
        raise NotImplementedError

    def start(self, on_message: object) -> None: ...

    def stop(self) -> None: ...


class Runtime:
    """Only the attributes the pages touch."""

    def __init__(self, repo: Repo, **overrides: object) -> None:
        self.settings = Settings(environment="dev", timezone="Asia/Kolkata")
        self.zone = KOLKATA
        self.triggers = overrides.get("triggers", Triggers())
        self.tasks = repo
        self.projects = overrides.get("projects", Projects())
        self.events = repo
        self.footage = repo
        self.facts = overrides.get("facts", Facts())
        self.channels = overrides.get("channels", [Channel("console", real=False)])
        self.notifier = ChannelNotifier(
            channels=[Channel("console", real=False)],  # type: ignore[list-item]
            policy=NotificationPolicy(daily_budget=12),
            zone=KOLKATA,
            now=lambda: NOW,
        )


def client(runtime: Runtime) -> TestClient:
    return TestClient(create_app(runtime))  # type: ignore[arg-type]


def a_trigger() -> Trigger:
    return Trigger(
        key="wake",
        title="Morning",
        body="Time to get up.",
        recurrence=Recurrence(at=time(6, 0), days=EVERY_DAY),
        notification_class=NotificationClass.CRITICAL,
        next_due_at=datetime(2026, 9, 20, 0, 30, tzinfo=UTC),
    )


class TestEverySectionExists:
    @pytest.mark.parametrize("path", [path for path, _ in SECTIONS])
    def test_the_navigation_does_not_lie(self, path: str) -> None:
        response = client(Runtime(Repo())).get(path)

        assert response.status_code == 200
        assert "<html" in response.text

    def test_sections_without_a_feature_yet_say_which_epic_brings_them(self) -> None:
        body = client(Runtime(Repo())).get("/goals").text

        assert "Nothing here yet" in body
        assert "epic 3" in body


class TestHonestEmptyStates:
    def test_no_tasks_explains_how_to_capture_one(self) -> None:
        body = client(Runtime(Repo())).get("/tasks").text

        assert "Nothing open" in body
        assert "task railzy: fix the signup handler" in body

    def test_no_events_says_so_rather_than_showing_an_empty_table(self) -> None:
        body = client(Runtime(Repo())).get("/audit").text

        assert "No events yet" in body

    def test_an_empty_footage_reserve_is_marked_critical_not_shown_as_fine(self) -> None:
        body = client(Runtime(Repo(clips=0))).get("/").text

        assert "none left" in body
        assert "stripe crit" in body


class TestRealData:
    def test_the_dashboard_shows_the_next_trigger(self) -> None:
        runtime = Runtime(Repo(), triggers=Triggers(triggers=[a_trigger()]))
        body = client(runtime).get("/").text

        assert "Morning" in body

    def test_a_project_that_does_not_exist_yet_is_labelled(self) -> None:
        projects = Projects(
            projects=[
                Project(
                    key="naxova",
                    name="Naxova",
                    objective="Form the company.",
                    status=ProjectStatus.NOT_YET_FORMED,
                )
            ]
        )
        body = client(Runtime(Repo(), projects=projects)).get("/projects").text

        assert "not formed yet" in body

    def test_tasks_are_listed_with_the_attention_they_need(self) -> None:
        task = Task(id="t1", project_key="railzy", title="Fix signup", created_at=NOW)
        body = client(Runtime(Repo(tasks=[task]))).get("/tasks").text

        assert "Fix signup" in body
        assert "railzy" in body

    def test_events_appear_in_the_audit_log(self) -> None:
        event = Event(
            id="e1",
            type=EventType.TASK_CREATED,
            occurred_at=NOW,
            recorded_at=NOW,
            payload={"title": "Fix signup"},
        )
        body = client(Runtime(Repo(events=[event]))).get("/audit").text

        assert "task.created" in body

    def test_integrations_shows_which_channel_can_actually_reach_him(self) -> None:
        runtime = Runtime(
            Repo(),
            channels=[Channel("telegram", real=True), Channel("console", real=False)],
        )
        body = client(runtime).get("/integrations").text

        assert "reaches you" in body
        assert "local only" in body


class TestSafety:
    def test_the_configured_name_is_rendered_not_hardcoded(self) -> None:
        body = client(Runtime(Repo())).get("/settings").text
        expected = Settings(environment="dev", timezone="Asia/Kolkata").agent_name

        assert expected in body

    def test_user_content_is_escaped(self) -> None:
        """A task title is user input and reaches the page."""
        task = Task(
            id="t1",
            project_key="railzy",
            title="<script>alert(1)</script>",
            created_at=NOW,
        )
        body = client(Runtime(Repo(tasks=[task]))).get("/tasks").text

        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;" in body
