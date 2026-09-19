"""Answers that cite where they came from.

Nothing here reaches for a model. These are grounded lookups over what the
system actually holds, so an answer is either backed by a record or is an
honest admission that there is none (P-3, FR-43).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from aos.domain.memory.partitions import Partition
from aos.ports.persistence.content import FootageRepository
from aos.ports.persistence.triggers import TriggerRepository
from aos.ports.persistence.work import EventStore, ProjectRepository, TaskRepository

UNKNOWN = "I don't have that."


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    partition: Partition | None = None
    records: int = 0

    @property
    def grounded(self) -> bool:
        return self.partition is not None

    def with_provenance(self) -> str:
        """Every answer says which store it came from and how much it read."""
        if not self.grounded:
            return self.text
        noun = "record" if self.records == 1 else "records"
        return f"{self.text}\n\n— {self.partition} · {self.records} {noun}"


@dataclass(frozen=True)
class Answers:
    triggers: TriggerRepository
    tasks: TaskRepository
    projects: ProjectRepository
    events: EventStore
    footage: FootageRepository
    zone: ZoneInfo
    now: Callable[[], datetime]

    def whats_open(self) -> Answer:
        open_tasks = self.tasks.open_tasks()
        if not open_tasks:
            return Answer("Nothing open.", Partition.STATE, 0)
        lines = [f"{t.title} ({t.project_key})" for t in open_tasks[:8]]
        more = len(open_tasks) - len(lines)
        if more:
            lines.append(f"...and {more} more")
        return Answer("\n".join(lines), Partition.STATE, len(open_tasks))

    def whats_next(self) -> Answer:
        upcoming = sorted(
            (
                (trigger.next_due_at, trigger)
                for trigger in self.triggers.all()
                if trigger.enabled and trigger.next_due_at is not None
            ),
            key=lambda pair: pair[0],
        )
        if not upcoming:
            return Answer("Nothing is scheduled.", Partition.STATE, 0)
        lines = [
            f"{due.astimezone(self.zone):%a %H:%M}  {trigger.title}"
            for due, trigger in upcoming[:3]
        ]
        return Answer("\n".join(lines), Partition.STATE, len(upcoming))

    def what_happened(self, limit: int = 5) -> Answer:
        events = self.events.recent(limit)
        if not events:
            return Answer("Nothing recorded yet.", Partition.EVENTS, 0)
        lines = [f"{e.occurred_at.astimezone(self.zone):%a %H:%M}  {e.type}" for e in events]
        return Answer("\n".join(lines), Partition.EVENTS, len(events))

    def about_a_project(self, key: str) -> Answer:
        project = self.projects.get(key)
        if project is None:
            # Naming what does exist beats a bare refusal.
            known = ", ".join(p.key for p in self.projects.all())
            return Answer(f"{UNKNOWN} I know about: {known}.")
        open_tasks = self.tasks.open_tasks(project.key)
        detail = f"{project.describe()}\n{len(open_tasks)} open."
        return Answer(detail, Partition.STATE, len(open_tasks) + 1)
