"""Money and the arithmetic of a goal.

Deterministic, no clock, no model. If any of this is wrong the system will
confidently mislead him about whether he is on track, which is worse than
saying nothing.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from aos.domain.finance.money import CRORE, LAKH, Money
from aos.domain.finance.records import (
    Certainty,
    ExpenseCategory,
    ExpenseRecord,
    Recurrence,
    RevenueRecord,
    Stream,
)
from aos.domain.goals.goal import Goal
from aos.domain.goals.pace import (
    MINIMUM_HISTORY_DAYS,
    Confidence,
    Verdict,
    assess,
    what_would_have_to_change,
)

START = date(2026, 8, 10)
DEADLINE = date(2027, 2, 10)


class TestMoney:
    def test_paise_are_exact(self) -> None:
        """Floats lose paise, and this system cannot be approximately right."""
        assert Money.of("0.1").paise + Money.of("0.2").paise == Money.of("0.3").paise

    def test_rounding_is_half_up_not_bankers(self) -> None:
        assert Money.of("0.005").paise == 1

    def test_arithmetic_holds(self) -> None:
        assert (Money.of(100) + Money.of(50)).major == Decimal("150.00")
        assert (Money.of(100) - Money.of(150)).paise == -5000

    def test_currencies_do_not_silently_mix(self) -> None:
        with pytest.raises(ValueError, match="cannot combine"):
            Money.of(1, "INR") + Money.of(1, "USD")

    def test_dividing_over_nothing_is_refused(self) -> None:
        with pytest.raises(ValueError, match="non-positive"):
            Money.of(100).divided_over(0)

    def test_a_ratio_against_nothing_is_infinite_not_a_crash(self) -> None:
        assert Money.of(100).ratio_to(Money.zero()) == float("inf")
        assert Money.zero().ratio_to(Money.zero()) == 0.0

    @pytest.mark.parametrize(
        ("paise", "expected"),
        [
            (CRORE, "Rs 1.00 crore"),
            (LAKH * 16, "Rs 16.00 lakh"),
            (Money.of(54945).paise, "Rs 54,945"),
            (Money.of(1234567).paise, "Rs 12.35 lakh"),
            (-CRORE, "-Rs 1.00 crore"),
        ],
    )
    def test_indian_grouping_and_scale(self, paise: int, expected: str) -> None:
        assert Money(paise).format() == expected


class TestRecords:
    def test_money_that_arrived_cannot_carry_a_probability(self) -> None:
        with pytest.raises(ValueError, match="cannot carry a probability"):
            RevenueRecord(
                id="r1",
                amount=Money.of(1000),
                stream=Stream.SERVICES,
                occurred_on=START,
                recorded_at=None,  # type: ignore[arg-type]
                certainty=Certainty.ACTUAL,
                probability=0.5,
            )

    def test_only_actual_money_counts_toward_trajectory(self) -> None:
        assert Certainty.ACTUAL.counts_toward_trajectory
        assert not Certainty.EXPECTED.counts_toward_trajectory
        assert not Certainty.PIPELINE.counts_toward_trajectory

    def test_a_pipeline_entry_is_weighted_by_its_probability(self) -> None:
        record = RevenueRecord(
            id="r1",
            amount=Money.of(100000),
            stream=Stream.SERVICES,
            occurred_on=START,
            recorded_at=None,  # type: ignore[arg-type]
            certainty=Certainty.PIPELINE,
            probability=0.25,
        )
        assert record.weighted.major == Decimal("25000.00")

    def test_an_expected_date_that_passed_has_slipped(self) -> None:
        record = RevenueRecord(
            id="r1",
            amount=Money.of(1000),
            stream=Stream.SERVICES,
            occurred_on=date(2026, 9, 1),
            recorded_at=None,  # type: ignore[arg-type]
            certainty=Certainty.EXPECTED,
        )
        assert record.has_slipped(date(2026, 9, 19))
        assert not record.has_slipped(date(2026, 8, 30))

    def test_an_annual_cost_is_spread_across_the_months(self) -> None:
        assert Recurrence.ANNUAL.monthly_share(Money.of(12000)).major == Decimal("1000.00")

    def test_a_one_off_has_no_monthly_share(self) -> None:
        assert Recurrence.ONE_OFF.monthly_share(Money.of(12000)).paise == 0

    def test_an_unattributed_expense_says_so(self) -> None:
        expense = ExpenseRecord(
            id="e1",
            amount=Money.of(500),
            category=ExpenseCategory.TOOLS,
            occurred_on=START,
            recorded_at=None,  # type: ignore[arg-type]
        )
        assert expense.attributed is False


def a_goal(target_rupees: int | None = 1_00_00_000, banked_rupees: int = 0) -> Goal:
    """The worked example: a crore over six months."""
    return Goal.monetary(
        key="root",
        name="The target",
        target=Money.of(target_rupees) if target_rupees else None,
        start_on=START,
        deadline=DEADLINE,
        current=Decimal(Money.of(banked_rupees).paise),
    )


class TestPace:
    def test_required_pace_is_against_what_remains_not_the_original_plan(self) -> None:
        """A month lost makes the rest steeper. Saying otherwise flatters."""
        early = assess(a_goal(banked_rupees=0), START + timedelta(days=30))
        later = assess(a_goal(banked_rupees=0), START + timedelta(days=120))

        assert later.required.per_day > early.required.per_day

    def test_progress_reduces_the_pace_required(self) -> None:
        behind = assess(a_goal(banked_rupees=0), START + timedelta(days=60))
        ahead = assess(a_goal(banked_rupees=50_00_000), START + timedelta(days=60))

        assert ahead.required.per_day < behind.required.per_day

    def test_weekly_and_monthly_pace_derive_from_daily(self) -> None:
        pace = assess(a_goal(), START + timedelta(days=30)).required

        assert pace.per_week == pace.per_day * 7
        assert pace.per_month == pace.per_day * Decimal("30.44")


class TestHonesty:
    def test_a_goal_with_no_target_is_unallocated_not_zero(self) -> None:
        result = assess(a_goal(target_rupees=None), START + timedelta(days=60))

        assert result.verdict is Verdict.NO_TARGET
        assert result.projected is None
        assert result.projects is False

    def test_below_a_fortnight_of_history_there_is_no_projection(self) -> None:
        result = assess(a_goal(banked_rupees=100000), START + timedelta(days=5))

        assert result.verdict is Verdict.INSUFFICIENT_HISTORY
        assert result.projected is None
        assert result.gap is None

    def test_and_it_says_how_much_longer_it_needs(self) -> None:
        result = assess(a_goal(), START + timedelta(days=5))

        assert f"{MINIMUM_HISTORY_DAYS - 5} more days" in result.limiting_factor

    def test_confidence_grows_with_history(self) -> None:
        assert (
            assess(a_goal(banked_rupees=1), START + timedelta(days=20)).confidence is Confidence.LOW
        )
        assert (
            assess(a_goal(banked_rupees=1), START + timedelta(days=40)).confidence
            is Confidence.MEDIUM
        )
        assert (
            assess(a_goal(banked_rupees=1), START + timedelta(days=100)).confidence
            is Confidence.HIGH
        )


class TestVerdicts:
    def test_keeping_up_is_on_track(self) -> None:
        # Half the window gone, half the target banked.
        result = assess(a_goal(banked_rupees=50_00_000), START + timedelta(days=91))

        assert result.verdict in {Verdict.ON_TRACK, Verdict.AHEAD}
        assert result.gap is not None
        assert result.gap >= 0

    def test_falling_a_little_short_is_behind_not_unreachable(self) -> None:
        result = assess(a_goal(banked_rupees=35_00_000), START + timedelta(days=91))

        assert result.verdict is Verdict.BEHIND
        assert result.short_by is not None

    def test_needing_five_times_the_observed_rate_is_unreachable(self) -> None:
        """Past a point it is not a slower plan, it is a different one."""
        result = assess(a_goal(banked_rupees=2_00_000), START + timedelta(days=91))

        assert result.verdict is Verdict.UNREACHABLE
        assert result.acceleration_needed is not None
        assert result.acceleration_needed >= 5

    def test_nothing_recorded_at_all_is_unreachable(self) -> None:
        result = assess(a_goal(banked_rupees=0), START + timedelta(days=91))

        assert result.verdict is Verdict.UNREACHABLE


class TestSayingWhatWouldChangeIt:
    def test_an_unreachable_verdict_never_arrives_bare(self) -> None:
        goal = a_goal(banked_rupees=2_00_000)
        result = assess(goal, START + timedelta(days=91))

        explanation = what_would_have_to_change(goal, result)

        assert "Either the target moves" in explanation
        assert "lakh" in explanation or "crore" in explanation

    def test_it_names_the_multiple_required(self) -> None:
        goal = a_goal(banked_rupees=2_00_000)
        explanation = what_would_have_to_change(goal, assess(goal, START + timedelta(days=91)))

        assert "x increase" in explanation

    def test_with_nothing_recorded_it_says_the_money_does_not_exist_yet(self) -> None:
        goal = a_goal(banked_rupees=0)
        explanation = what_would_have_to_change(goal, assess(goal, START + timedelta(days=91)))

        assert "does not currently exist" in explanation

    def test_a_healthy_goal_gets_no_lecture(self) -> None:
        goal = a_goal(banked_rupees=50_00_000)
        assert what_would_have_to_change(goal, assess(goal, START + timedelta(days=91))) == ""
