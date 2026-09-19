"""Required pace, actual pace, trajectory, gap, and reachability.

Computed in code, never by a model (AD-1, CP-7). The LLM may explain these
numbers; it must never be the thing that produces them.

Two rules run through all of it. Pace is always against what remains, not what
was originally planned - a month lost makes the rest steeper, and saying
otherwise is flattering. And below a minimum history there is no projection at
all: `insufficient_history` is a real answer, a zero is a lie.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from aos.domain.goals.goal import Goal

MINIMUM_HISTORY_DAYS = 14
DAYS_PER_WEEK = 7
DAYS_PER_MONTH = Decimal("30.44")

# Above this multiple of the observed rate, the plan is not behind - it is a
# different plan. The threshold is configuration; this is the default.
DEFAULT_IMPLAUSIBLE_MULTIPLE = Decimal(5)

# A quarter of observation before a projection is trustworthy; a month
# before it is worth more than a shrug.
HIGH_CONFIDENCE_DAYS = 90
MEDIUM_CONFIDENCE_DAYS = 30


class Verdict(StrEnum):
    NO_TARGET = "no-target"
    INSUFFICIENT_HISTORY = "insufficient-history"
    AHEAD = "ahead"
    ON_TRACK = "on-track"
    BEHIND = "behind"
    UNREACHABLE = "unreachable-under-current-assumptions"

    @property
    def is_a_projection(self) -> bool:
        return self in {Verdict.AHEAD, Verdict.ON_TRACK, Verdict.BEHIND, Verdict.UNREACHABLE}


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class Pace:
    per_day: Decimal
    per_week: Decimal
    per_month: Decimal

    @classmethod
    def from_daily(cls, per_day: Decimal) -> Pace:
        return cls(
            per_day=per_day,
            per_week=per_day * DAYS_PER_WEEK,
            per_month=per_day * DAYS_PER_MONTH,
        )

    @classmethod
    def nothing(cls) -> Pace:
        return cls(Decimal(0), Decimal(0), Decimal(0))


@dataclass(frozen=True, slots=True)
class Assessment:
    verdict: Verdict
    required: Pace
    actual: Pace
    projected: Decimal | None
    gap: Decimal | None
    """Projected minus target. Negative means short."""
    days_remaining: int
    days_of_history: int
    confidence: Confidence
    limiting_factor: str = ""
    acceleration_needed: Decimal | None = None

    @property
    def projects(self) -> bool:
        return self.verdict.is_a_projection

    @property
    def short_by(self) -> Decimal | None:
        if self.gap is None or self.gap >= 0:
            return None
        return -self.gap


def required_pace(goal: Goal, today: date) -> Pace:
    """What is needed from here, over what is left."""
    remaining_amount = goal.remaining
    days = goal.days_remaining(today)
    if remaining_amount is None or days <= 0:
        return Pace.nothing()
    return Pace.from_daily(remaining_amount / days)


def actual_pace(goal: Goal, today: date) -> Pace:
    """What has actually been happening, over the time it happened in."""
    elapsed = goal.days_elapsed(today)
    if elapsed <= 0:
        return Pace.nothing()
    return Pace.from_daily(goal.current / elapsed)


def assess(
    goal: Goal,
    today: date,
    *,
    implausible_multiple: Decimal = DEFAULT_IMPLAUSIBLE_MULTIPLE,
) -> Assessment:
    required = required_pace(goal, today)
    actual = actual_pace(goal, today)
    elapsed = goal.days_elapsed(today)
    remaining = goal.days_remaining(today)

    if not goal.allocated:
        return Assessment(
            verdict=Verdict.NO_TARGET,
            required=required,
            actual=actual,
            projected=None,
            gap=None,
            days_remaining=remaining,
            days_of_history=elapsed,
            confidence=Confidence.LOW,
            limiting_factor="no target has been set for this goal",
        )

    if elapsed < MINIMUM_HISTORY_DAYS:
        return Assessment(
            verdict=Verdict.INSUFFICIENT_HISTORY,
            required=required,
            actual=actual,
            projected=None,
            gap=None,
            days_remaining=remaining,
            days_of_history=elapsed,
            confidence=Confidence.LOW,
            limiting_factor=(
                f"{MINIMUM_HISTORY_DAYS - elapsed} more days of records "
                f"before a projection means anything"
            ),
        )

    projected = goal.current + (actual.per_day * remaining)
    target = goal.target or Decimal(0)
    gap = projected - target
    acceleration = _acceleration(required.per_day, actual.per_day)

    return Assessment(
        verdict=_verdict(gap, target, acceleration, implausible_multiple),
        required=required,
        actual=actual,
        projected=projected,
        gap=gap,
        days_remaining=remaining,
        days_of_history=elapsed,
        confidence=_confidence(elapsed),
        acceleration_needed=acceleration,
    )


def _acceleration(required_daily: Decimal, actual_daily: Decimal) -> Decimal | None:
    if actual_daily <= 0:
        return None if required_daily <= 0 else Decimal("Infinity")
    return required_daily / actual_daily


def _verdict(
    gap: Decimal,
    target: Decimal,
    acceleration: Decimal | None,
    implausible_multiple: Decimal,
) -> Verdict:
    if acceleration is not None and acceleration >= implausible_multiple:
        return Verdict.UNREACHABLE
    if gap >= 0:
        # Within a few percent of the line is on track, not ahead.
        return Verdict.ON_TRACK if gap < target * Decimal("0.05") else Verdict.AHEAD
    return Verdict.BEHIND


def _confidence(days_of_history: int) -> Confidence:
    if days_of_history >= HIGH_CONFIDENCE_DAYS:
        return Confidence.HIGH
    if days_of_history >= MEDIUM_CONFIDENCE_DAYS:
        return Confidence.MEDIUM
    return Confidence.LOW


def what_would_have_to_change(goal: Goal, assessment: Assessment) -> str:
    """Never a bare verdict.

    Saying a goal is unreachable without saying what would change it is a
    complaint, not information.
    """
    if assessment.verdict is not Verdict.UNREACHABLE:
        return ""

    required = assessment.required
    actual = assessment.actual
    multiple = assessment.acceleration_needed

    if actual.per_day <= 0:
        return (
            f"Nothing has been recorded against this yet, so "
            f"{goal.describe_value(required.per_month)} a month has to come from somewhere "
            f"that does not currently exist."
        )

    scale = "an unbounded" if multiple is None else f"a {multiple:.1f}x"
    return (
        f"Reaching it needs {goal.describe_value(required.per_month)} a month against "
        f"{goal.describe_value(actual.per_month)} actually arriving - {scale} increase. "
        f"Either the target moves, the deadline moves, or the money comes from a "
        f"different source."
    )
