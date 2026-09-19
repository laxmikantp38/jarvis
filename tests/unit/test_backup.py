"""Backups, and the drill that proves they restore.

These use real SQLite files rather than fakes, because the failure mode being
guarded against is a backup that looks fine until the day it is needed.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aos.app.maintenance.backup import BackupService

NOW = datetime(2026, 9, 19, 3, 0, tzinfo=UTC)


def a_database(path: Path, rows: int = 3) -> Path:
    connection = sqlite3.connect(path)
    with connection:
        connection.execute("create table trigger (key text primary key)")
        connection.execute("create table project (key text primary key)")
        connection.execute("create table task (id text primary key)")
        connection.execute("create table event (id text primary key)")
        connection.execute("create table user_fact (key text primary key)")
        connection.executemany(
            "insert into trigger (key) values (?)", [(f"t{i}",) for i in range(rows)]
        )
    connection.close()
    return path


def service(tmp_path: Path, *, now: datetime = NOW, retain_days: int = 30) -> BackupService:
    return BackupService(
        database=a_database(tmp_path / "aos.db"),
        directory=tmp_path / "backups",
        retain_days=retain_days,
        now=lambda: now,
    )


class TestBackup:
    def test_a_backup_is_written_and_is_not_empty(self, tmp_path: Path) -> None:
        result = service(tmp_path).create()

        assert result.path.exists()
        assert result.bytes_written > 0

    def test_it_is_named_for_the_day_it_was_taken(self, tmp_path: Path) -> None:
        result = service(tmp_path).create()

        assert result.path.name == "aos-2026-09-19.db"

    def test_taking_one_twice_in_a_day_does_not_pile_up_files(self, tmp_path: Path) -> None:
        backup = service(tmp_path)
        backup.create()
        backup.create()

        assert len(list((tmp_path / "backups").glob("aos-*.db"))) == 1

    def test_the_file_is_released_afterwards(self, tmp_path: Path) -> None:
        """sqlite3's context manager commits; it does not close. On Windows a
        leaked handle blocks the file from ever being removed."""
        result = service(tmp_path).create()

        result.path.unlink()  # raises PermissionError if a handle is still open

        assert not result.path.exists()


class TestRetention:
    def _dated_backup(self, directory: Path, stamp: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"aos-{stamp}.db"
        path.write_bytes(b"x")
        return path

    def test_backups_beyond_the_window_are_removed(self, tmp_path: Path) -> None:
        backup = service(tmp_path, retain_days=30)
        old = self._dated_backup(tmp_path / "backups", "2026-01-01")
        recent = self._dated_backup(tmp_path / "backups", "2026-09-18")

        removed = backup.prune()

        assert old in removed
        assert recent.exists()

    def test_an_unrecognised_filename_is_left_alone(self, tmp_path: Path) -> None:
        backup = service(tmp_path)
        stray = tmp_path / "backups"
        stray.mkdir(parents=True, exist_ok=True)
        (stray / "aos-notadate.db").write_bytes(b"x")

        backup.prune()

        assert (stray / "aos-notadate.db").exists()


class TestDrill:
    def test_a_fresh_backup_restores_and_verifies(self, tmp_path: Path) -> None:
        backup = service(tmp_path)
        backup.create()

        result = backup.drill(tmp_path / "scratch.db")

        assert result.passed
        assert result.integrity_ok
        assert result.rows["trigger"] == 3, "the rows actually came back"

    def test_the_drill_leaves_nothing_behind(self, tmp_path: Path) -> None:
        backup = service(tmp_path)
        backup.create()
        scratch = tmp_path / "scratch.db"

        backup.drill(scratch)

        assert not scratch.exists()

    def test_having_no_backup_at_all_is_a_failure_not_a_pass(self, tmp_path: Path) -> None:
        """The dangerous outcome is a green drill that verified nothing."""
        result = service(tmp_path).drill(tmp_path / "scratch.db")

        assert result.passed is False
        assert result.error is not None
        assert "no backup" in result.error

    def test_a_corrupt_backup_fails_the_drill(self, tmp_path: Path) -> None:
        backup = service(tmp_path)
        created = backup.create()
        created.path.write_bytes(b"this is not a database")

        result = backup.drill(tmp_path / "scratch.db")

        assert result.passed is False

    def test_the_result_reads_as_a_sentence(self, tmp_path: Path) -> None:
        backup = service(tmp_path)
        backup.create()

        description = backup.drill(tmp_path / "scratch.db").describe()

        assert "passed" in description
        assert "trigger 3" in description


class TestLatest:
    def test_the_most_recent_backup_is_chosen(self, tmp_path: Path) -> None:
        directory = tmp_path / "backups"
        directory.mkdir(parents=True)
        for stamp in ("2026-09-17", "2026-09-19", "2026-09-18"):
            (directory / f"aos-{stamp}.db").write_bytes(b"x")

        backup = BackupService(
            database=tmp_path / "aos.db",
            directory=directory,
            retain_days=30,
            now=lambda: NOW,
        )

        latest = backup.latest()
        assert latest is not None
        assert latest.name == "aos-2026-09-19.db"

    def test_an_empty_directory_has_no_latest(self, tmp_path: Path) -> None:
        backup = BackupService(
            database=tmp_path / "aos.db",
            directory=tmp_path / "backups",
            retain_days=30,
            now=lambda: NOW,
        )

        assert backup.latest() is None


@pytest.mark.parametrize("retain", [1, 7, 30])
def test_retention_window_is_honoured(tmp_path: Path, retain: int) -> None:
    backup = service(tmp_path, retain_days=retain)
    directory = tmp_path / "backups"
    directory.mkdir(parents=True, exist_ok=True)
    stale = (NOW - timedelta(days=retain + 1)).strftime("%Y-%m-%d")
    (directory / f"aos-{stale}.db").write_bytes(b"x")

    assert len(backup.prune()) == 1
