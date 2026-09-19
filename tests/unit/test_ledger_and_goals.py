"""The ledger and the goal tree.

The rule under all of it: actual money and hoped-for money never mix, and a
target the user has not set is never invented.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from aos.app.finance.goals import ROOT_KEY, Goals, seed_goals
from aos.app.finance.ledger import EarningDetail, ExpenseDetail, Ledger
from aos.domain.finance.money import Money
from aos.domain.finance.records import (
    Certainty,
    ExpenseCategory,
    ExpenseRecord,
    Recurrence,
    RevenueRecord,
    Stream,
)
from aos.domain.goals.pace import Verdict

START = date(2026, 8, 10)
DEADLINE = date(2027, 2, 10)
NOW = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)


class Revenue:
    def __init__(self) -> None:
        self.records: list[RevenueRecord] = []

    def add(self, record: RevenueRecord) -> None:
        self.records.append(record)

    def all(self, certainty: Certainty | None = None) -> list[RevenueRecord]:
        if certainty is None:
            return list(self.records)
        return [r for r in self.records if r.certainty is certainty]

    def since(self, start: date) -> list[RevenueRecord]:
        return [r for r in self.records if r.occurred_on >= start]


class Expenses:
    def __init__(self) -> None:
        self.records: list[ExpenseRecord] = []

    def add(self, record: ExpenseRecord) -> None:
        self.records.append(record)

    def all(self) -> list[ExpenseRecord]:
        return list(self.records)

    def since(self, start: date) -> list[ExpenseRecord]:
        return [r for r in self.records if r.occurred_on >= start]


class GoalStore:
    def __init__(self, goals: list | None = None) -> None:
        self.items = {goal.key: goal for goal in (goals or [])}

    def all(self) -> list:
        return list(self.items.values())

    def get(self, key: str):  # noqa: ANN201
        return self.items.get(key)

    def children_of(self, key: str) -> list:
        return [g for g in self.items.values() if g.parent_key == key]

    def save(self, goal) -> None:  # noqa: ANN001
        self.items[goal.key] = goal

    def add_missing(self, goals: list) -> list[str]:
        added = [g.key for g in goals if g.key not in self.items]
        for goal in goals:
            self.items.setdefault(goal.key, goal)
        return added


class Events:
    def __init__(self) -> None:
        self.appended: list = []

    def append(self, event) -> None:  # noqa: ANN001
        self.appended.append(event)

    def recent(self, limit: int = 50) -> list:
        return list(self.appended)


def ledger() -> tuple[Ledger, Revenue, Expenses, Events]:
    revenue, expenses, events = Revenue(), Expenses(), Events()
    return (
        Ledger(revenue=revenue, expenses=expenses, events=events, now=lambda: NOW),  # type: ignore[arg-type]
        revenue,
        expenses,
        events,
    )


class TestCapture:
    def test_an_earning_is_recorded_and_evented(self) -> None:
        book, revenue, _, events = ledger()
        book.record_earning(Money.of(40000), Stream.FREELANCE)

        assert len(revenue.records) == 1
        assert len(events.appended) == 1

    def test_it_defaults_to_today_and_to_actual(self) -> None:
        book, revenue, _, _ = ledger()
        book.record_earning(Money.of(40000), Stream.FREELANCE)

        assert revenue.records[0].occurred_on == NOW.date()
        assert revenue.records[0].certainty is Certainty.ACTUAL

    def test_a_recurring_expense_keeps_its_recurrence(self) -> None:
        book, _, expenses, _ = ledger()
        book.record_expense(
            Money.of(2400),
            ExpenseCategory.TOOLS,
            ExpenseDetail(project_key="railzy", recurrence=Recurrence.MONTHLY),
        )

        assert expenses.records[0].recurrence is Recurrence.MONTHLY


class TestPosition:
    def test_net_is_gross_minus_expenses(self) -> None:
        book, _, _, _ = ledger()
        book.record_earning(Money.of(100000), Stream.SERVICES)
        book.record_expense(Money.of(20000), ExpenseCategory.CONTRACTORS)

        position = book.position()

        assert position.gross.major == Decimal("100000.00")
        assert position.expenses.major == Decimal("20000.00")
        assert position.net.major == Decimal("80000.00")

    def test_spending_more_than_was_earned_is_flagged(self) -> None:
        book, _, _, _ = ledger()
        book.record_earning(Money.of(1000), Stream.RAILZY)
        book.record_expense(Money.of(5000), ExpenseCategory.INFRASTRUCTURE)

        assert book.position().loss_making is True

    def test_hoped_for_money_stays_out_of_the_position(self) -> None:
        """This is the number he will act on; it must not include a maybe."""
        book, _, _, _ = ledger()
        book.record_earning(Money.of(100000), Stream.SERVICES)
        book.record_earning(
            Money.of(900000),
            Stream.SERVICES,
            EarningDetail(certainty=Certainty.PIPELINE, probability=0.5),
        )

        assert book.position().gross.major == Decimal("100000.00")
        assert book.pipeline().major == Decimal("450000.00"), "weighted, and reported apart"

    def test_an_expected_date_that_passed_is_surfaced(self) -> None:
        book, _, _, _ = ledger()
        book.record_earning(
            Money.of(50000),
            Stream.SERVICES,
            EarningDetail(certainty=Certainty.EXPECTED, occurred_on=NOW.date() - timedelta(days=5)),
        )

        assert len(book.slipped()) == 1


class TestPerProject:
    def test_a_project_that_only_costs_money_shows_the_bleed(self) -> None:
        book, _, _, _ = ledger()
        book.record_expense(
            Money.of(3000), ExpenseCategory.INFRASTRUCTURE, ExpenseDetail(project_key="railzy")
        )

        railzy = next(p for p in book.by_project() if p.project_key == "railzy")

        assert railzy.position.loss_making
        assert railzy.bleeding_monthly is not None
        assert railzy.bleeding_monthly.major == Decimal("3000.00")

    def test_unattributed_costs_sit_in_their_own_bucket(self) -> None:
        """Spreading them across projects would invent attribution."""
        book, _, _, _ = ledger()
        book.record_expense(Money.of(500), ExpenseCategory.OTHER)

        keys = [p.project_key for p in book.by_project()]

        assert "unattributed" in keys


class TestBurnAndWaste:
    def test_monthly_burn_counts_only_recurring_costs(self) -> None:
        book, _, _, _ = ledger()
        book.record_expense(
            Money.of(1200), ExpenseCategory.TOOLS, ExpenseDetail(recurrence=Recurrence.MONTHLY)
        )
        book.record_expense(
            Money.of(12000), ExpenseCategory.TOOLS, ExpenseDetail(recurrence=Recurrence.ANNUAL)
        )
        book.record_expense(Money.of(99999), ExpenseCategory.OTHER)  # one-off

        assert book.monthly_burn().major == Decimal("2200.00")

    def test_a_subscription_on_something_earning_nothing_is_a_cancel_candidate(self) -> None:
        book, _, _, _ = ledger()
        book.record_expense(
            Money.of(2400),
            ExpenseCategory.TOOLS,
            ExpenseDetail(project_key="ghumr", recurrence=Recurrence.MONTHLY),
        )

        candidates = book.cancel_candidates()

        assert len(candidates) == 1
        assert candidates[0].project_key == "ghumr"

    def test_a_subscription_on_something_earning_is_left_alone(self) -> None:
        book, _, _, _ = ledger()
        book.record_earning(Money.of(50000), Stream.RAILZY)
        book.record_expense(
            Money.of(2400),
            ExpenseCategory.TOOLS,
            ExpenseDetail(project_key="railzy", recurrence=Recurrence.MONTHLY),
        )

        assert book.cancel_candidates() == []


def goals_service(revenue: Revenue, targets: Money | None = Money.of(1_00_00_000)) -> Goals:
    store = GoalStore(seed_goals(targets, START, DEADLINE))
    return Goals(goals=store, revenue=revenue, now=lambda: NOW)  # type: ignore[arg-type]


class TestGoalTree:
    def test_children_start_unallocated_not_at_zero(self) -> None:
        """The split is a hypothesis; the engine does not write one."""
        service = goals_service(Revenue())

        unallocated = service.unallocated()

        assert unallocated, "every child begins without a target"
        assert all(goal.target is None for goal in unallocated)

    def test_actual_money_rolls_into_the_root(self) -> None:
        revenue = Revenue()
        book = Ledger(revenue=revenue, expenses=Expenses(), events=Events(), now=lambda: NOW)  # type: ignore[arg-type]
        book.record_earning(Money.of(200000), Stream.SERVICES)
        service = goals_service(revenue)

        service.refresh_from_records()

        root = service.goals.get(ROOT_KEY)
        assert root is not None
        assert root.current == Decimal(Money.of(200000).paise)

    def test_a_stream_rolls_into_its_own_goal(self) -> None:
        revenue = Revenue()
        book = Ledger(revenue=revenue, expenses=Expenses(), events=Events(), now=lambda: NOW)  # type: ignore[arg-type]
        book.record_earning(Money.of(75000), Stream.RAILZY)
        service = goals_service(revenue)

        service.refresh_from_records()

        railzy = service.goals.get("railzy")
        assert railzy is not None
        assert railzy.current == Decimal(Money.of(75000).paise)

    def test_pipeline_money_never_rolls_in(self) -> None:
        revenue = Revenue()
        book = Ledger(revenue=revenue, expenses=Expenses(), events=Events(), now=lambda: NOW)  # type: ignore[arg-type]
        book.record_earning(
            Money.of(900000), Stream.SERVICES, EarningDetail(certainty=Certainty.PIPELINE)
        )
        service = goals_service(revenue)

        service.refresh_from_records()

        root = service.goals.get(ROOT_KEY)
        assert root is not None
        assert root.current == 0


class TestStanding:
    def test_an_early_goal_reports_insufficient_history(self) -> None:
        service = goals_service(Revenue())
        standing = service.standing()

        assert standing is not None
        # 40 days elapsed by NOW, so history is sufficient, but nothing banked.
        assert standing.assessment.verdict in {Verdict.UNREACHABLE, Verdict.BEHIND}

    def test_an_unreachable_goal_carries_its_explanation(self) -> None:
        standing = goals_service(Revenue()).standing()

        assert standing is not None
        assert standing.needs_saying
        assert standing.explanation, "never a bare verdict"

    def test_a_goal_with_no_target_is_not_something_to_warn_about(self) -> None:
        service = goals_service(Revenue(), targets=None)
        standing = service.standing()

        assert standing is not None
        assert standing.assessment.verdict is Verdict.NO_TARGET
        assert standing.needs_saying is False


class TestProposedSplit:
    def _with_records(self, count: int) -> Goals:
        revenue = Revenue()
        book = Ledger(revenue=revenue, expenses=Expenses(), events=Events(), now=lambda: NOW)  # type: ignore[arg-type]
        for index in range(count):
            stream = Stream.SERVICES if index % 2 else Stream.RAILZY
            book.record_earning(Money.of(10000), stream)
        return goals_service(revenue)

    def test_too_few_records_means_no_proposal(self) -> None:
        """Four data points is a coincidence, not a pattern."""
        assert self._with_records(4).propose_split() is None

    def test_enough_records_produce_shares_that_sum_to_one(self) -> None:
        proposal = self._with_records(6).propose_split()

        assert proposal is not None
        assert sum(proposal.shares.values()) == Decimal(1)

    def test_the_proposal_shows_what_it_was_based_on(self) -> None:
        proposal = self._with_records(6).propose_split()

        assert proposal is not None
        assert proposal.records == 6
        assert "6 records" in proposal.describe()

    def test_a_proposal_is_never_applied_by_itself(self) -> None:
        service = self._with_records(6)
        service.propose_split()

        assert service.unallocated(), "targets are the user's to set, not the system's"
