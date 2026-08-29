"""An adapter is compliant only if it satisfies the port identically.

This suite is written against the port. When a Postgres or document adapter
arrives it runs unchanged against that one too (AD-2, AD-3).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine

from aos.adapters.persistence.sqlite.engine import create_sqlite_engine, session_factory
from aos.adapters.persistence.sqlite.models import Base
from aos.adapters.persistence.sqlite.trigger_repository import SqliteTriggerRepository
from aos.domain.scheduling.recurrence import WEEKDAYS, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger
from aos.ports.persistence.triggers import TriggerRepository


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    created = create_sqlite_engine(tmp_path / "test.db")
    Base.metadata.create_all(created)
    yield created
    created.dispose()


@pytest.fixture
def repository(engine: Engine) -> TriggerRepository:
    return SqliteTriggerRepository(session_factory(engine))


def a_trigger(key: str = "standup") -> Trigger:
    return Trigger(
        key=key,
        title="Client standup",
        body="Standup call in a few minutes.",
        recurrence=Recurrence(at=time(19, 50), days=WEEKDAYS),
        notification_class=NotificationClass.IMPORTANT,
    )


def test_a_saved_trigger_comes_back_identical(repository: TriggerRepository) -> None:
    original = a_trigger()
    repository.save(original)
    assert repository.get("standup") == original


def test_timestamps_come_back_timezone_aware(repository: TriggerRepository) -> None:
    """SQLite has no timezone-aware column; a naive datetime must never escape."""
    moment = datetime(2026, 8, 30, 14, 20, tzinfo=UTC)
    repository.save(a_trigger().fired(moment, ZoneInfo("UTC")))

    stored = repository.get("standup")
    assert stored is not None
    assert stored.last_fired_at is not None
    assert stored.last_fired_at.tzinfo is not None
    assert stored.last_fired_at == moment


def test_an_absent_trigger_is_none_not_an_error(repository: TriggerRepository) -> None:
    assert repository.get("nothing-here") is None


def test_saving_twice_updates_rather_than_duplicates(repository: TriggerRepository) -> None:
    repository.save(a_trigger())
    repository.save(a_trigger())
    assert len(repository.all()) == 1


def test_seeding_inserts_only_what_is_missing(repository: TriggerRepository) -> None:
    assert repository.add_missing([a_trigger("a"), a_trigger("b")]) == ["a", "b"]
    assert repository.add_missing([a_trigger("b"), a_trigger("c")]) == ["c"]
    assert len(repository.all()) == 3


def test_seeding_never_overwrites_a_users_change(repository: TriggerRepository) -> None:
    """The routine belongs to the user; a later seed must not undo their edit."""
    repository.save(a_trigger())
    repository.save(replace(a_trigger(), enabled=False))

    repository.add_missing([a_trigger()])

    stored = repository.get("standup")
    assert stored is not None
    assert stored.enabled is False


def test_state_survives_a_new_connection(engine: Engine) -> None:
    """FR-25: schedule state is read from disk, not reconstructed from code."""
    SqliteTriggerRepository(session_factory(engine)).save(a_trigger())

    reopened = SqliteTriggerRepository(session_factory(engine))
    assert reopened.get("standup") is not None
