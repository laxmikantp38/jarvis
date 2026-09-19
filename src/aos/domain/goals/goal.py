"""Strategic goals, of any kind.

No target, currency or threshold appears in source (AD-12). The engine treats a
revenue target, a subscriber count and a company formation identically, and
deleting every configured goal must leave a system that still starts and runs.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import StrEnum

from aos.domain.finance.money import Money


class GoalType(StrEnum):
    MONETARY = "monetary"
    COUNT = "count"
    """Users, subscribers, views."""
    MILESTONE = "milestone"
    """Binary: done or not. A company is formed or it is not."""
    RATIO = "ratio"
    DURATION = "duration"
    """Hours of practice, for a learning goal."""

    @property
    def is_measurable_progressively(self) -> bool:
        return self is not GoalType.MILESTONE


class GoalStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    AT_RISK = "at-risk"
    ACHIEVED = "achieved"
    MISSED = "missed"
    ABANDONED = "abandoned"


class Rollup(StrEnum):
    SUM = "sum"
    MAX = "max"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class Goal:
    key: str
    name: str
    goal_type: GoalType
    start_on: date
    deadline: date
    parent_key: str | None = None
    target: Decimal | None = None
    """None means unallocated. Reported as such, never as zero.

    For a monetary goal this is in **paise**, matching Money, so that no
    conversion happens implicitly anywhere. Use Goal.monetary() and never
    write the number by hand.
    """
    unit: str = ""
    current: Decimal = Decimal(0)
    rollup: Rollup = Rollup.SUM
    weight: int = 1
    status: GoalStatus = GoalStatus.ACTIVE

    @classmethod
    def monetary(
        cls,
        key: str,
        name: str,
        target: Money | None,
        start_on: date,
        deadline: date,
        **rest: object,
    ) -> Goal:
        """The only sanctioned way to state a money target.

        Whether the number meant rupees or paise was ambiguous, and an
        ambiguity in the one field the whole system reasons about is a defect
        waiting to happen. Pass Money and it cannot be got wrong.
        """
        return cls(
            key=key,
            name=name,
            goal_type=GoalType.MONETARY,
            start_on=start_on,
            deadline=deadline,
            target=Decimal(target.paise) if target else None,
            **rest,  # type: ignore[arg-type]
        )

    def __post_init__(self) -> None:
        if self.deadline <= self.start_on:
            msg = "a goal must end after it starts"
            raise ValueError(msg)
        if self.target is not None and self.target <= 0:
            msg = "a target of zero or less is not a target"
            raise ValueError(msg)

    @property
    def allocated(self) -> bool:
        return self.target is not None

    @property
    def target_or_zero(self) -> Decimal:
        """For display only.

        `target or 0` kept producing Decimal | int at call sites; this keeps
        the type honest and the intent obvious. Logic that must distinguish
        "no target" from "zero" uses `allocated`, never this.
        """
        return self.target if self.target is not None else Decimal(0)

    @property
    def remaining(self) -> Decimal | None:
        if self.target is None:
            return None
        return max(Decimal(0), self.target - self.current)

    @property
    def achieved(self) -> bool:
        return self.target is not None and self.current >= self.target

    def progress(self) -> Decimal | None:
        """Fraction complete, or None when there is nothing to measure against."""
        if self.target is None or self.target == 0:
            return None
        return min(Decimal(1), self.current / self.target)

    def days_remaining(self, today: date) -> int:
        return max(0, (self.deadline - today).days)

    def days_elapsed(self, today: date) -> int:
        return max(0, (min(today, self.deadline) - self.start_on).days)

    def with_current(self, value: Decimal) -> Goal:
        return replace(self, current=value)

    def as_money(self, value: Decimal) -> Money | None:
        """Monetary goals render as money; others render as bare numbers."""
        if self.goal_type is not GoalType.MONETARY:
            return None
        return Money(int(value))

    def describe_value(self, value: Decimal) -> str:
        money = self.as_money(value)
        if money is not None:
            return money.format()
        rendered = f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"
        return f"{rendered} {self.unit}".strip()
