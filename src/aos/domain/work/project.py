"""The ventures competing for the same evenings.

A project is not a folder for tasks. It carries an objective and a status,
because the point of the system is deciding between them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    NOT_YET_FORMED = "not-yet-formed"
    """A venture that does not legally or practically exist yet."""
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Project:
    key: str
    name: str
    objective: str
    status: ProjectStatus = ProjectStatus.ACTIVE

    @property
    def exists_yet(self) -> bool:
        return self.status is not ProjectStatus.NOT_YET_FORMED

    def describe(self) -> str:
        if not self.exists_yet:
            return f"{self.name} (not formed yet) - {self.objective}"
        return f"{self.name} - {self.objective}"
