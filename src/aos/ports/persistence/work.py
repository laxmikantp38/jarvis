from typing import Protocol

from aos.domain.memory.classification import Confidentiality
from aos.domain.work.event import Event
from aos.domain.work.project import Project
from aos.domain.work.task import Task


class ProjectRepository(Protocol):
    def all(self) -> list[Project]: ...

    def get(self, key: str) -> Project | None: ...

    def add_missing(self, projects: list[Project]) -> list[str]:
        """Seed without overwriting anything the user has edited."""
        ...


class TaskRepository(Protocol):
    def open_tasks(self, project_key: str | None = None) -> list[Task]: ...

    def get(self, task_id: str) -> Task | None: ...

    def save(self, task: Task) -> None: ...


class EventStore(Protocol):
    """Append-only. There is no update and no delete, here or in the database."""

    def append(self, event: Event) -> None: ...

    def recent(self, limit: int = 50) -> list[Event]: ...


class UserFactRepository(Protocol):
    def get(self, key: str) -> tuple[str, Confidentiality] | None: ...

    def set(self, key: str, value: str, confidentiality: Confidentiality) -> None: ...

    def all(self) -> dict[str, str]: ...
