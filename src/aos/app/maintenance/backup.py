"""Backups, and proof that they restore.

An untested backup is not a backup, so the drill is a first-class operation
rather than a note in a runbook. It restores into a scratch copy, opens it,
checks its integrity and counts what came back.

SQLite's own backup API is used rather than a file copy: in WAL mode a copy
taken while the service is writing can be torn, and a torn backup looks fine
until the day it is needed.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

CHECK_NAME = "backup"
COUNTED_TABLES = ("trigger", "project", "task", "event", "user_fact")


@dataclass(frozen=True, slots=True)
class BackupResult:
    path: Path
    bytes_written: int


@dataclass(frozen=True, slots=True)
class DrillResult:
    source: Path
    integrity_ok: bool
    rows: dict[str, int]
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.integrity_ok and self.error is None

    def describe(self) -> str:
        if not self.passed:
            return f"Restore drill FAILED for {self.source.name}: {self.error or 'integrity check'}"
        counted = ", ".join(f"{table} {count}" for table, count in self.rows.items())
        return f"Restore drill passed for {self.source.name} ({counted})."


@dataclass(frozen=True)
class BackupService:
    database: Path
    directory: Path
    retain_days: int
    now: Callable[[], datetime]

    def create(self) -> BackupResult:
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = self.now().strftime("%Y-%m-%d")
        destination = self.directory / f"aos-{stamp}.db"

        with (
            contextlib.closing(sqlite3.connect(self.database)) as source,
            contextlib.closing(sqlite3.connect(destination)) as target,
        ):
            source.backup(target)

        size = destination.stat().st_size
        log.info("backup written to %s (%d bytes)", destination, size)
        return BackupResult(path=destination, bytes_written=size)

    def prune(self) -> list[Path]:
        """Older than the retention window. Never touches today's."""
        cutoff = self.now() - timedelta(days=self.retain_days)
        removed: list[Path] = []
        for candidate in sorted(self.directory.glob("aos-*.db")):
            stamp = candidate.stem.removeprefix("aos-")
            try:
                taken = datetime.strptime(stamp, "%Y-%m-%d").replace(tzinfo=self.now().tzinfo)
            except ValueError:
                continue
            if taken < cutoff:
                candidate.unlink()
                removed.append(candidate)
        if removed:
            log.info("pruned %d expired backups", len(removed))
        return removed

    def latest(self) -> Path | None:
        backups = sorted(self.directory.glob("aos-*.db"))
        return backups[-1] if backups else None

    def drill(self, scratch: Path) -> DrillResult:
        """Restore the most recent backup somewhere harmless and read it back."""
        source = self.latest()
        if source is None:
            return DrillResult(
                source=self.directory,
                integrity_ok=False,
                rows={},
                error="there is no backup to restore",
            )

        scratch.parent.mkdir(parents=True, exist_ok=True)
        try:
            with (
                contextlib.closing(sqlite3.connect(source)) as origin,
                contextlib.closing(sqlite3.connect(scratch)) as restored,
            ):
                origin.backup(restored)

            with contextlib.closing(sqlite3.connect(scratch)) as restored:
                integrity = restored.execute("PRAGMA integrity_check").fetchone()[0]
                rows = {
                    table: restored.execute(f"select count(*) from {table}").fetchone()[0]  # noqa: S608
                    for table in COUNTED_TABLES
                }
        except sqlite3.Error as exc:
            return DrillResult(source=source, integrity_ok=False, rows={}, error=str(exc))
        finally:
            scratch.unlink(missing_ok=True)

        return DrillResult(source=source, integrity_ok=integrity == "ok", rows=rows)
