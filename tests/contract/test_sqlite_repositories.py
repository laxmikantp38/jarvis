"""Adapters against a real database, built by the real migrations.

The spine says an adapter is compliant only when it satisfies its port
identically, so nothing here is faked: this is SQLite, migrated by alembic.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, time
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker

from aos.adapters.persistence.sqlite.content_repository import SqliteFootageRepository
from aos.adapters.persistence.sqlite.engine import create_sqlite_engine, session_factory
from aos.adapters.persistence.sqlite.trigger_repository import SqliteTriggerRepository
from aos.adapters.persistence.sqlite.work_repository import (
    SqliteEventStore,
    SqliteProjectRepository,
    SqliteTaskRepository,
    SqliteUserFactRepository,
)
from aos.domain.content.footage import FootageReserve
from aos.domain.memory.classification import Confidentiality
from aos.domain.scheduling.recurrence import WEEKDAYS, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger
from aos.domain.work.event import Event, EventType
from aos.domain.work.project import Project, ProjectStatus
from aos.domain.work.task import Task

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 19, 10, 0, tzinfo=UTC)

Sessions = sessionmaker[Session]


@pytest.fixture
def sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Sessions]:
    database = tmp_path / "aos.db"
    monkeypatch.setenv("AOS_DATABASE_OVERRIDE", str(database))

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(config, "head")

    yield session_factory(create_sqlite_engine(database))


class TestTriggers:
    def test_a_trigger_survives_a_restart(self, sessions: Sessions) -> None:
        """Schedule state is read from disk, not reconstructed from code."""
        original = Trigger(
            key="wake",
            title="Morning",
            body="Time to get up.",
            recurrence=Recurrence(at=time(6, 0), days=WEEKDAYS),
            notification_class=NotificationClass.CRITICAL,
            next_due_at=datetime(2026, 9, 20, 0, 30, tzinfo=UTC),
        )
        SqliteTriggerRepository(sessions).save(original)

        reloaded = SqliteTriggerRepository(sessions).get("wake")

        assert reloaded == original

    def test_timestamps_come_back_as_utc_not_naive(self, sessions: Sessions) -> None:
        """SQLite has no timezone-aware column; the adapter must attach it."""
        repository = SqliteTriggerRepository(sessions)
        repository.save(
            Trigger(
                key="gym",
                title="Gym",
                body="",
                recurrence=Recurrence(at=time(7, 30)),
                next_due_at=datetime(2026, 9, 20, 2, 0, tzinfo=UTC),
            )
        )
        reloaded = repository.get("gym")

        assert reloaded is not None
        assert reloaded.next_due_at is not None
        assert reloaded.next_due_at.tzinfo is not None

    def test_seeding_never_overwrites_an_edited_trigger(self, sessions: Sessions) -> None:
        repository = SqliteTriggerRepository(sessions)
        repository.save(
            Trigger(
                key="wake",
                title="My own wording",
                body="",
                recurrence=Recurrence(at=time(5, 30)),
                enabled=False,
            )
        )

        inserted = repository.add_missing(
            [
                Trigger(key="wake", title="Morning", body="", recurrence=Recurrence(at=time(6, 0))),
                Trigger(key="gym", title="Gym", body="", recurrence=Recurrence(at=time(7, 30))),
            ]
        )

        assert inserted == ["gym"]
        kept = repository.get("wake")
        assert kept is not None
        assert kept.title == "My own wording"
        assert kept.enabled is False


class TestWork:
    def test_a_task_round_trips_with_its_classification(self, sessions: Sessions) -> None:
        SqliteProjectRepository(sessions).add_missing(
            [Project(key="freelance", name="Freelance", objective="")]
        )
        task = Task(
            id=str(uuid.uuid4()),
            project_key="freelance",
            title="Prepare the standup notes",
            created_at=NOW,
            confidentiality=Confidentiality.CLIENT,
        )
        repository = SqliteTaskRepository(sessions)
        repository.save(task)

        reloaded = repository.get(task.id)

        assert reloaded is not None
        assert reloaded.confidentiality is Confidentiality.CLIENT

    def test_completing_a_task_removes_it_from_the_open_list(self, sessions: Sessions) -> None:
        SqliteProjectRepository(sessions).add_missing(
            [Project(key="railzy", name="Railzy", objective="")]
        )
        repository = SqliteTaskRepository(sessions)
        task = Task(id="t1", project_key="railzy", title="Fix signup", created_at=NOW)
        repository.save(task)
        assert len(repository.open_tasks()) == 1

        repository.save(task.completed(NOW))

        assert repository.open_tasks() == []

    def test_a_project_that_does_not_exist_yet_says_so(self, sessions: Sessions) -> None:
        repository = SqliteProjectRepository(sessions)
        repository.add_missing(
            [
                Project(
                    key="naxova",
                    name="Naxova",
                    objective="Form the company.",
                    status=ProjectStatus.NOT_YET_FORMED,
                )
            ]
        )
        naxova = repository.get("naxova")

        assert naxova is not None
        assert naxova.exists_yet is False
        assert "not formed yet" in naxova.describe()


class TestAppendOnly:
    """AD-8: enforced at the storage layer, not by application discipline."""

    def _an_event(self) -> Event:
        return Event(
            id="e1",
            type=EventType.TASK_CREATED,
            occurred_at=NOW,
            recorded_at=NOW,
            payload={"title": "Fix signup"},
        )

    def test_events_can_be_appended_and_read_back(self, sessions: Sessions) -> None:
        store = SqliteEventStore(sessions)
        store.append(self._an_event())

        recent = store.recent()

        assert len(recent) == 1
        assert recent[0].type is EventType.TASK_CREATED

    def test_the_database_itself_refuses_an_update(self, sessions: Sessions) -> None:
        SqliteEventStore(sessions).append(self._an_event())

        with pytest.raises(DatabaseError, match="append-only"), sessions() as session:
            session.execute(text("update event set type = :t"), {"t": "tampered"})
            session.commit()

    def test_the_database_itself_refuses_a_delete(self, sessions: Sessions) -> None:
        SqliteEventStore(sessions).append(self._an_event())

        with pytest.raises(DatabaseError, match="append-only"), sessions() as session:
            session.execute(text("delete from event"))
            session.commit()


class TestFootageAndFacts:
    def test_the_reserve_starts_empty_rather_than_absent(self, sessions: Sessions) -> None:
        assert SqliteFootageRepository(sessions).get().clips_available == 0

    def test_the_reserve_round_trips(self, sessions: Sessions) -> None:
        repository = SqliteFootageRepository(sessions)
        repository.save(FootageReserve(clips_available=4, clips_per_publish=2))

        reloaded = repository.get()

        assert reloaded.clips_available == 4
        assert reloaded.days_covered == 2

    def test_a_user_fact_keeps_its_classification(self, sessions: Sessions) -> None:
        repository = SqliteUserFactRepository(sessions)
        repository.set("client.name", "Acme", Confidentiality.CLIENT)

        stored = repository.get("client.name")

        assert stored == ("Acme", Confidentiality.CLIENT)
