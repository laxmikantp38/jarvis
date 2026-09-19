"""What happened. Immutable, append-only (AD-8).

Two timestamps, not one: `occurred_at` is when the thing happened in the world,
`recorded_at` is when this system learned of it. A task confirmed retrospectively
sits correctly in history without pretending it was known at the time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

# Below this, the difference is clock jitter rather than a retrospective entry.
RECORDED_LATE_AFTER_SECONDS = 60


class EventType(StrEnum):
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_DROPPED = "task.dropped"
    PROJECT_CREATED = "project.created"
    TRIGGER_FIRED = "trigger.fired"
    FOOTAGE_ADJUSTED = "footage.adjusted"
    REVENUE_RECORDED = "revenue.recorded"
    EXPENSE_RECORDED = "expense.recorded"
    GOAL_PROGRESSED = "goal.progressed"
    SYSTEM_STARTED = "system.started"


@dataclass(frozen=True, slots=True)
class Event:
    id: str
    type: EventType
    occurred_at: datetime
    recorded_at: datetime
    payload: dict[str, str]
    project_key: str | None = None
    task_id: str | None = None

    @property
    def recorded_late(self) -> bool:
        """True when the system learned of this after the fact."""
        delay = (self.recorded_at - self.occurred_at).total_seconds()
        return delay > RECORDED_LATE_AFTER_SECONDS
