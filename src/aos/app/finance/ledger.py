"""Gross, expenses, net, and what each venture actually costs.

Showing gross alone is how a project that loses money every month passes for a
success. Net is computed alongside it, always, and never instead of it.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from aos.domain.finance.money import Money
from aos.domain.finance.records import (
    Certainty,
    ExpenseCategory,
    ExpenseRecord,
    Recurrence,
    RevenueRecord,
    Stream,
)
from aos.domain.work.event import Event, EventType
from aos.ports.persistence.finance import ExpenseRepository, RevenueRepository
from aos.ports.persistence.work import EventStore

log = logging.getLogger(__name__)

UNATTRIBUTED = "unattributed"
STALE_SUBSCRIPTION_DAYS = 60


@dataclass(frozen=True, slots=True)
class EarningDetail:
    """Everything optional about an earning, so the call stays within AD-20."""

    certainty: Certainty = Certainty.ACTUAL
    occurred_on: date | None = None
    probability: float = 1.0
    note: str = ""


@dataclass(frozen=True, slots=True)
class ExpenseDetail:
    project_key: str | None = None
    recurrence: Recurrence = Recurrence.ONE_OFF
    occurred_on: date | None = None
    note: str = ""


@dataclass(frozen=True, slots=True)
class Position:
    gross: Money
    expenses: Money
    net: Money

    @property
    def loss_making(self) -> bool:
        return self.net.paise < 0


@dataclass(frozen=True, slots=True)
class ProjectPosition:
    project_key: str
    position: Position

    @property
    def bleeding_monthly(self) -> Money | None:
        """What it costs to keep a loss-making project alive."""
        if not self.position.loss_making:
            return None
        return Money(-self.position.net.paise, self.position.net.currency)


@dataclass(frozen=True, slots=True)
class CancelCandidate:
    project_key: str
    monthly_cost: Money
    reason: str


@dataclass(frozen=True)
class Ledger:
    revenue: RevenueRepository
    expenses: ExpenseRepository
    events: EventStore
    now: Callable[[], datetime]

    # --- capture ---------------------------------------------------------

    def record_earning(
        self, amount: Money, stream: Stream, detail: EarningDetail | None = None
    ) -> RevenueRecord:
        detail = detail or EarningDetail()
        moment = self.now()
        record = RevenueRecord(
            id=str(uuid.uuid4()),
            amount=amount,
            stream=stream,
            occurred_on=detail.occurred_on or moment.date(),
            recorded_at=moment,
            certainty=detail.certainty,
            probability=detail.probability,
            note=detail.note,
        )
        self.revenue.add(record)
        self._record_event(EventType.REVENUE_RECORDED, moment, amount, stream.value)
        log.info("recorded %s from %s (%s)", amount.format(), stream, detail.certainty)
        return record

    def record_expense(
        self, amount: Money, category: ExpenseCategory, detail: ExpenseDetail | None = None
    ) -> ExpenseRecord:
        detail = detail or ExpenseDetail()
        moment = self.now()
        record = ExpenseRecord(
            id=str(uuid.uuid4()),
            amount=amount,
            category=category,
            occurred_on=detail.occurred_on or moment.date(),
            recorded_at=moment,
            project_key=detail.project_key,
            recurrence=detail.recurrence,
            note=detail.note,
        )
        self.expenses.add(record)
        self._record_event(EventType.EXPENSE_RECORDED, moment, amount, category.value)
        log.info("recorded expense %s (%s)", amount.format(), category)
        return record

    def _record_event(
        self, event_type: EventType, moment: datetime, amount: Money, detail: str
    ) -> None:
        self.events.append(
            Event(
                id=str(uuid.uuid4()),
                type=event_type,
                occurred_at=moment,
                recorded_at=moment,
                payload={"amount": amount.format(), "detail": detail},
            )
        )

    # --- position --------------------------------------------------------

    def position(self, since: date | None = None) -> Position:
        """Actual money only. Expected and pipeline are reported separately."""
        earned = [
            record
            for record in self.revenue.all(Certainty.ACTUAL)
            if since is None or record.occurred_on >= since
        ]
        spent = [
            record for record in self.expenses.all() if since is None or record.occurred_on >= since
        ]
        gross = _total(record.amount for record in earned)
        outgoing = _total(record.amount for record in spent)
        return Position(gross=gross, expenses=outgoing, net=gross - outgoing)

    def pipeline(self) -> Money:
        """Probability-weighted, and never folded into the position."""
        return _total(
            record.weighted
            for record in self.revenue.all()
            if record.certainty is not Certainty.ACTUAL
        )

    def slipped(self) -> list[RevenueRecord]:
        today = self.now().date()
        return [record for record in self.revenue.all() if record.has_slipped(today)]

    def by_project(self) -> list[ProjectPosition]:
        """Revenue is attributed by stream name where it matches a project."""
        keys = {record.project_key or UNATTRIBUTED for record in self.expenses.all()}
        keys |= {record.stream.value for record in self.revenue.all(Certainty.ACTUAL)}

        positions = []
        for key in sorted(keys):
            gross = _total(
                record.amount
                for record in self.revenue.all(Certainty.ACTUAL)
                if record.stream.value == key
            )
            spent = _total(
                record.amount
                for record in self.expenses.all()
                if (record.project_key or UNATTRIBUTED) == key
            )
            positions.append(
                ProjectPosition(
                    project_key=key,
                    position=Position(gross=gross, expenses=spent, net=gross - spent),
                )
            )
        return positions

    def monthly_burn(self) -> Money:
        """Recurring commitments, at their monthly share."""
        return _total(
            record.recurrence.monthly_share(record.amount)
            for record in self.expenses.all()
            if record.recurrence.is_recurring
        )

    def cancel_candidates(self) -> list[CancelCandidate]:
        """A subscription attached to something that has earned nothing."""
        today = self.now().date()
        cutoff = today - timedelta(days=STALE_SUBSCRIPTION_DAYS)
        earning_keys = {
            record.stream.value
            for record in self.revenue.all(Certainty.ACTUAL)
            if record.occurred_on >= cutoff
        }

        candidates = []
        for record in self.expenses.all():
            if not record.recurrence.is_recurring or record.project_key is None:
                continue
            if record.project_key in earning_keys:
                continue
            candidates.append(
                CancelCandidate(
                    project_key=record.project_key,
                    monthly_cost=record.recurrence.monthly_share(record.amount),
                    reason=f"no revenue in {STALE_SUBSCRIPTION_DAYS} days",
                )
            )
        return candidates


def _total(amounts: Iterable[Money]) -> Money:
    total = Money.zero()
    for amount in amounts:
        total = total + amount
    return total
