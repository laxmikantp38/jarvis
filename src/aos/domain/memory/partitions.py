"""The separated stores (AD-14).

One undifferentiated memory would destroy retention rules, confidentiality
routing and targeted retrieval, so the partitions are structural rather than
a tag on a shared table. A write addressed to the wrong one is a schema error.
"""

from __future__ import annotations

from enum import StrEnum


class Partition(StrEnum):
    USER = "user"
    """Stable facts about the person: preferences, routine, working style."""

    KNOWLEDGE = "knowledge"
    """Documents and reference material."""

    STATE = "state"
    """Current operational state: tasks, schedule, live values."""

    DECISIONS = "decisions"
    """Strategic choices and the reasoning behind them."""

    EVENTS = "events"
    """What happened. Immutable."""

    GOALS = "goals"
    """Objectives, targets and progress."""

    @property
    def append_only(self) -> bool:
        return self is Partition.EVENTS

    @property
    def retained_indefinitely(self) -> bool:
        return self is not Partition.STATE
