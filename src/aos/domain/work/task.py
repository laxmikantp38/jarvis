"""A unit of the user's work.

Every task belongs to exactly one project, so nothing floats free of the thing
it is supposed to advance.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from aos.domain.memory.classification import Confidentiality


class TaskStatus(StrEnum):
    OPEN = "open"
    DONE = "done"
    DROPPED = "dropped"


class Attention(StrEnum):
    """What the work needs from him, which decides when it can be scheduled."""

    DEEP = "deep"
    SHALLOW = "shallow"
    AUDIO = "audio"
    """Doable with hands and eyes busy - the commute and the gym."""


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    project_key: str
    title: str
    created_at: datetime
    status: TaskStatus = TaskStatus.OPEN
    attention: Attention = Attention.SHALLOW
    confidentiality: Confidentiality = Confidentiality.PERSONAL
    notes: str = ""
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            msg = "a task with no title is not a task"
            raise ValueError(msg)
        if not self.project_key:
            msg = "every task belongs to exactly one project"
            raise ValueError(msg)

    @property
    def is_open(self) -> bool:
        return self.status is TaskStatus.OPEN

    def completed(self, moment: datetime) -> Task:
        return replace(self, status=TaskStatus.DONE, completed_at=moment)

    def dropped(self, moment: datetime) -> Task:
        return replace(self, status=TaskStatus.DROPPED, completed_at=moment)
