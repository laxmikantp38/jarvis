"""Money in and money out.

Actual and expected are kept apart everywhere. Trajectory reads actuals only,
because a pipeline that has not landed is a hope, and mixing the two produces
a number that feels reassuring and is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from aos.domain.finance.money import Money


class Stream(StrEnum):
    SALARY = "salary"
    FREELANCE = "freelance"
    SERVICES = "services"
    RAILZY = "railzy"
    GHUMR = "ghumr"
    CONTENT = "content"
    SPONSORSHIP = "sponsorship"
    AFFILIATE = "affiliate"
    NAXOVA = "naxova"
    OTHER = "other"


class Certainty(StrEnum):
    ACTUAL = "actual"
    """Money that has arrived. The only kind trajectory counts."""

    EXPECTED = "expected"
    """Committed but not yet received - an invoice raised, a deal signed."""

    PIPELINE = "pipeline"
    """Plausible but uncommitted. Carries a probability."""

    @property
    def counts_toward_trajectory(self) -> bool:
        return self is Certainty.ACTUAL


class ExpenseCategory(StrEnum):
    INFRASTRUCTURE = "infrastructure"
    TOOLS = "tools"
    CONTENT_PRODUCTION = "content-production"
    LEGAL = "legal"
    CONTRACTORS = "contractors"
    MARKETING = "marketing"
    PERSONAL = "personal"
    OTHER = "other"


class Recurrence(StrEnum):
    ONE_OFF = "one-off"
    MONTHLY = "monthly"
    ANNUAL = "annual"

    @property
    def is_recurring(self) -> bool:
        return self is not Recurrence.ONE_OFF

    def monthly_share(self, amount: Money) -> Money:
        """What this costs per month, however it is billed."""
        if self is Recurrence.MONTHLY:
            return amount
        if self is Recurrence.ANNUAL:
            return amount.divided_over(12)
        return Money.zero(amount.currency)


@dataclass(frozen=True, slots=True)
class RevenueRecord:
    id: str
    amount: Money
    stream: Stream
    occurred_on: date
    recorded_at: datetime
    certainty: Certainty = Certainty.ACTUAL
    probability: float = 1.0
    note: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            msg = f"probability must be between 0 and 1, got {self.probability}"
            raise ValueError(msg)
        if self.certainty is Certainty.ACTUAL and self.probability != 1.0:
            msg = "money that has arrived is certain; it cannot carry a probability"
            raise ValueError(msg)

    @property
    def weighted(self) -> Money:
        """Probability-weighted value, always shown with its probability."""
        return self.amount * self.probability

    def has_slipped(self, today: date) -> bool:
        """An expected date that passed without becoming actual."""
        return self.certainty is not Certainty.ACTUAL and self.occurred_on < today


@dataclass(frozen=True, slots=True)
class ExpenseRecord:
    id: str
    amount: Money
    category: ExpenseCategory
    occurred_on: date
    recorded_at: datetime
    project_key: str | None = None
    recurrence: Recurrence = Recurrence.ONE_OFF
    note: str = ""

    @property
    def attributed(self) -> bool:
        """Unattributed costs sit in their own bucket rather than being spread."""
        return self.project_key is not None
