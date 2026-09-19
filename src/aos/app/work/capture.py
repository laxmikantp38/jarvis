"""Turning a message into a tracked task.

The point is that it costs him nothing: type a line while walking to the car
and it is captured, attributed and recorded. Anything requiring a form would
simply not get used.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from aos.domain.memory.classification import Confidentiality
from aos.domain.work.event import Event, EventType
from aos.domain.work.project import Project
from aos.domain.work.task import Attention, Task
from aos.ports.persistence.work import EventStore, ProjectRepository, TaskRepository

log = logging.getLogger(__name__)

DEFAULT_PROJECT = "personal"


@dataclass(frozen=True)
class CaptureResult:
    task: Task
    project: Project | None
    guessed_project: bool


@dataclass(frozen=True)
class TaskCapture:
    projects: ProjectRepository
    tasks: TaskRepository
    events: EventStore
    now: Callable[[], datetime]

    def capture(self, text: str) -> CaptureResult:
        project_key, title, guessed = self._attribute(text)
        moment = self.now()

        task = Task(
            id=str(uuid.uuid4()),
            project_key=project_key,
            title=title,
            created_at=moment,
            attention=_infer_attention(title),
            # Client work is the one class that could cost him a contract, so
            # attribution to the freelance project sets it without being asked.
            confidentiality=(
                Confidentiality.CLIENT if project_key == "freelance" else Confidentiality.PERSONAL
            ),
        )
        self.tasks.save(task)
        self.events.append(
            Event(
                id=str(uuid.uuid4()),
                type=EventType.TASK_CREATED,
                occurred_at=moment,
                recorded_at=moment,
                payload={"title": title},
                project_key=project_key,
                task_id=task.id,
            )
        )
        log.info("captured task %s against %s", task.id, project_key)
        return CaptureResult(
            task=task, project=self.projects.get(project_key), guessed_project=guessed
        )

    def _attribute(self, text: str) -> tuple[str, str, bool]:
        """`railzy: fix signup` is explicit; otherwise the project is inferred."""
        if ":" in text:
            head, tail = text.split(":", 1)
            candidate = head.strip().lower()
            if self.projects.get(candidate) and tail.strip():
                return candidate, tail.strip(), False

        title = text.strip()
        for project in self.projects.all():
            if project.key in title.lower() or project.name.lower() in title.lower():
                return project.key, title, True
        return DEFAULT_PROJECT, title, True


AUDIO_HINTS = ("call", "ring", "listen", "think about", "decide")
DEEP_HINTS = ("fix", "build", "write", "debug", "design", "refactor")


def _infer_attention(title: str) -> Attention:
    lowered = title.lower()
    if any(hint in lowered for hint in AUDIO_HINTS):
        return Attention.AUDIO
    if any(hint in lowered for hint in DEEP_HINTS):
        return Attention.DEEP
    return Attention.SHALLOW
