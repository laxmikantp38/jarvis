"""Keeping the goal tree in step with what actually arrived.

The engine is goal-type agnostic; this is the piece that knows a monetary goal
is fed by revenue records. Nothing here invents a target, and a goal with none
stays unallocated rather than quietly becoming zero.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal

from aos.domain.finance.money import Money
from aos.domain.finance.records import Certainty, Stream
from aos.domain.goals.goal import Goal, GoalType
from aos.domain.goals.pace import Assessment, Verdict, assess, what_would_have_to_change
from aos.ports.persistence.finance import GoalRepository, RevenueRepository

log = logging.getLogger(__name__)

ROOT_KEY = "root"


@dataclass(frozen=True, slots=True)
class Standing:
    goal: Goal
    assessment: Assessment
    explanation: str

    @property
    def needs_saying(self) -> bool:
        """Whether this is worth interrupting someone about."""
        return self.assessment.verdict in {Verdict.UNREACHABLE, Verdict.BEHIND}


@dataclass(frozen=True, slots=True)
class ProposedSplit:
    """Derived from where money actually arrived, never applied automatically."""

    shares: dict[str, Decimal]
    based_on: Money
    records: int

    def describe(self) -> str:
        lines = [
            f"{stream}: {share:.0%}"
            for stream, share in sorted(self.shares.items(), key=lambda kv: -kv[1])
        ]
        return f"Based on {self.based_on.format()} across {self.records} records:\n" + "\n".join(
            lines
        )


@dataclass(frozen=True)
class Goals:
    goals: GoalRepository
    revenue: RevenueRepository
    now: Callable[[], datetime]
    minimum_records_for_a_split: int = 5

    def sync_root_target(self, target: Money | None) -> bool:
        """The headline target is configuration, so configuration wins for it.

        Children are never touched: the split is the user's to set, and a seed
        that overwrote it would erase a decision. Only the root follows the
        config file, because that is where AD-12 says it lives.
        """
        root = self.goals.get(ROOT_KEY)
        if root is None:
            return False
        wanted = Decimal(target.paise) if target else None
        if root.target == wanted:
            return False
        self.goals.save(replace(root, target=wanted))
        log.info("root target updated from configuration")
        return True

    def refresh_from_records(self) -> None:
        """Roll actual money into every monetary goal, then up the tree."""
        actuals = self.revenue.all(Certainty.ACTUAL)

        for goal in self.goals.all():
            if goal.goal_type is not GoalType.MONETARY:
                continue
            banked = self._banked_for(goal, actuals)
            if banked != goal.current:
                self.goals.save(goal.with_current(banked))

    def _banked_for(self, goal: Goal, actuals: list) -> Decimal:  # type: ignore[type-arg]
        """A leaf sums its own stream; the root sums everything beneath it."""
        if goal.key == ROOT_KEY:
            return Decimal(sum(record.amount.paise for record in actuals))
        matching = [record for record in actuals if record.stream.value == goal.key]
        return Decimal(sum(record.amount.paise for record in matching))

    def standing(self, key: str = ROOT_KEY) -> Standing | None:
        goal = self.goals.get(key)
        if goal is None:
            return None
        today = self.now().date()
        assessment = assess(goal, today)
        return Standing(
            goal=goal,
            assessment=assessment,
            explanation=what_would_have_to_change(goal, assessment),
        )

    def unallocated(self) -> list[Goal]:
        """Children with no target. Reported, never filled in with a guess."""
        return [goal for goal in self.goals.children_of(ROOT_KEY) if not goal.allocated]

    def propose_split(self) -> ProposedSplit | None:
        """Derive a split from where money actually arrived.

        A proposal only. Applying it is the user's act, because a target is a
        statement of intent and the system does not get to write one.
        """
        actuals = self.revenue.all(Certainty.ACTUAL)
        if len(actuals) < self.minimum_records_for_a_split:
            return None

        total = sum(record.amount.paise for record in actuals)
        if total <= 0:
            return None

        by_stream: dict[str, int] = {}
        for record in actuals:
            by_stream[record.stream.value] = (
                by_stream.get(record.stream.value, 0) + record.amount.paise
            )

        return ProposedSplit(
            shares={stream: Decimal(paise) / Decimal(total) for stream, paise in by_stream.items()},
            based_on=Money(total),
            records=len(actuals),
        )


def seed_goals(root_target: Money | None, start_on: date, deadline: date) -> list[Goal]:
    """The starting tree.

    Children begin unallocated on purpose: the split is a hypothesis, and the
    engine proposes one from evidence once there is any (FR-100).
    """
    root = Goal.monetary(
        key=ROOT_KEY,
        name="Earnings target",
        target=root_target,
        start_on=start_on,
        deadline=deadline,
    )
    children = [
        Goal.monetary(
            key=stream.value,
            name=stream.value.title(),
            target=None,
            start_on=start_on,
            deadline=deadline,
            parent_key=ROOT_KEY,
        )
        for stream in (
            Stream.SERVICES,
            Stream.FREELANCE,
            Stream.RAILZY,
            Stream.GHUMR,
            Stream.CONTENT,
            Stream.SPONSORSHIP,
            Stream.SALARY,
        )
    ]
    return [root, *children]
