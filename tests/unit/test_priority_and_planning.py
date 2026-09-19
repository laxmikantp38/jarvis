"""Scoring and the day plan.

Both are pure. If scoring is not deterministic the system cannot explain
itself, and if the plan over-fills it gets abandoned after the first
interruption.
"""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal

import pytest

from aos.domain.planning.plan import (
    BUFFER_SHARE,
    DEEP_WORK_CUTOFF,
    Attention,
    Candidate,
    Commitment,
    build,
    free_slots,
)
from aos.domain.priority.scoring import (
    LIVE_HARM_FLOOR,
    Band,
    Factor,
    Inputs,
    Score,
    band_for,
    score,
)

TODAY = date(2026, 9, 21)  # a Monday


class TestDeterminism:
    def test_the_same_inputs_always_give_the_same_score(self) -> None:
        inputs = Inputs(revenue_impact=Decimal("0.8"), effort=Decimal("0.2"))

        assert score(inputs).value == score(inputs).value

    def test_every_factor_is_accounted_for(self) -> None:
        result = score(Inputs())

        assert len(result.contributions) == len(Factor)

    def test_the_breakdown_is_ordered_by_influence(self) -> None:
        result = score(Inputs(revenue_impact=Decimal(1), unblocks_others=Decimal("0.1")))
        lines = result.breakdown()

        assert "revenue impact" in lines[0], "the biggest mover is named first"


class TestHonestyAboutGuesses:
    def test_a_missing_factor_is_marked_estimated(self) -> None:
        result = score(Inputs(revenue_impact=Decimal("0.9")))

        estimated = [c for c in result.contributions if c.estimated]
        assert estimated
        assert not result.fully_measured

    def test_a_fully_supplied_score_says_so(self) -> None:
        result = score(
            Inputs(
                revenue_impact=Decimal("0.5"),
                business_impact=Decimal("0.5"),
                user_impact=Decimal("0.5"),
                urgency=Decimal("0.5"),
                strategic_alignment=Decimal("0.5"),
                risk_reduction=Decimal("0.5"),
                unblocks_others=Decimal("0.5"),
                effort=Decimal("0.5"),
                opportunity_cost=Decimal("0.5"),
            )
        )

        assert result.fully_measured
        assert result.estimated_inputs == 0

    def test_an_estimate_is_visible_in_the_breakdown(self) -> None:
        result = score(Inputs(revenue_impact=Decimal("0.9")))

        assert any("estimated" in line for line in result.breakdown())


class TestWhatOutranksWhat:
    def _signup_bug(self) -> Score:
        return score(
            Inputs(
                revenue_impact=Decimal("0.9"),
                user_impact=Decimal("0.9"),
                urgency=Decimal("0.9"),
                effort=Decimal("0.2"),
                affects_live_users=True,
            )
        )

    def _button_radius(self) -> Score:
        return score(
            Inputs(
                revenue_impact=Decimal("0.05"),
                user_impact=Decimal("0.05"),
                urgency=Decimal("0.05"),
                strategic_alignment=Decimal("0.05"),
                effort=Decimal("0.4"),
            )
        )

    def test_the_signup_bug_is_do_now(self) -> None:
        assert self._signup_bug().band is Band.P1

    def test_the_button_radius_is_a_deletion_candidate(self) -> None:
        assert self._button_radius().band is Band.P4

    def test_effort_penalises_rather_than_rewards(self) -> None:
        cheap = score(Inputs(revenue_impact=Decimal("0.6"), effort=Decimal("0.1")))
        dear = score(Inputs(revenue_impact=Decimal("0.6"), effort=Decimal("0.9")))

        assert cheap.value > dear.value


class TestLiveUserFloor:
    def test_harm_to_live_users_cannot_be_outranked_by_tidying(self) -> None:
        """Whatever else is true, this does not sink below the floor."""
        result = score(Inputs(revenue_impact=Decimal(0), effort=Decimal(1), affects_live_users=True))

        assert result.value >= LIVE_HARM_FLOOR
        assert result.floored_for_live_harm

    def test_the_reason_says_so_plainly(self) -> None:
        result = score(Inputs(effort=Decimal(1), affects_live_users=True))

        assert result.why() == "it is affecting live users"

    def test_the_floor_does_not_apply_when_nobody_is_affected(self) -> None:
        assert not score(Inputs(effort=Decimal(1))).floored_for_live_harm


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("0.95"), Band.P1),
        (Decimal("0.70"), Band.P1),
        (Decimal("0.50"), Band.P2),
        (Decimal("0.30"), Band.P3),
        (Decimal("0.05"), Band.P4),
    ],
)
def test_bands_are_thresholds_on_the_score(value: Decimal, expected: Band) -> None:
    assert band_for(value) is expected


# --- planning ---------------------------------------------------------------


def a_day() -> list[Commitment]:
    """His real Tuesday: gym, a commute each way, the office, a client call."""
    return [
        Commitment("gym", time(7, 30), time(9, 15), Attention.AUDIO),
        Commitment("commute out", time(10, 0), time(10, 30), Attention.AUDIO),
        Commitment("office", time(10, 30), time(19, 0)),
        Commitment("commute home", time(19, 0), time(19, 30), Attention.AUDIO),
        Commitment("client standup", time(20, 0), time(20, 30)),
    ]


def a_task(
    title: str,
    minutes: int = 30,
    band: Band = Band.P2,
    value: str = "0.5",
    attention: Attention = Attention.SHALLOW,
    *,
    protected: bool = False,
) -> Candidate:
    return Candidate(
        task_id=title,
        title=title,
        project_key="railzy",
        band=band,
        score=Decimal(value),
        minutes=minutes,
        attention=attention,
        protected=protected,
    )


class TestFreeSlots:
    def test_fixed_commitments_are_not_available(self) -> None:
        slots = free_slots(a_day(), time(6, 0), time(23, 30))
        desk = [s for s in slots if s.attention is not Attention.AUDIO]

        assert all(
            not (s.start < time(19, 0) and s.end > time(10, 30)) for s in desk
        ), "the office day is never offered as free time"

    def test_the_commute_is_offered_as_audio_time(self) -> None:
        slots = free_slots(a_day(), time(6, 0), time(23, 30))

        audio = [s for s in slots if s.attention is Attention.AUDIO]
        assert audio, "three hours a week of usable time should not be thrown away"


class TestPlanning:
    def test_a_plan_leaves_a_buffer(self) -> None:
        """A plan with no slack fails at the first interruption."""
        plan = build(TODAY, [a_task(f"t{i}", minutes=60) for i in range(20)], a_day(),
                     time(6, 0), time(23, 30))

        assert plan.buffer_minutes > 0
        assert not plan.is_overcommitted

    def test_work_that_does_not_fit_is_dropped_and_named(self) -> None:
        plan = build(TODAY, [a_task(f"t{i}", minutes=90) for i in range(12)], a_day(),
                     time(6, 0), time(23, 30))

        assert plan.dropped
        assert all(d.reason for d in plan.dropped), "never dropped silently"

    def test_estimates_are_never_compressed_to_make_things_fit(self) -> None:
        plan = build(TODAY, [a_task("long", minutes=120)], a_day(), time(6, 0), time(23, 30))

        for placement in plan.placements:
            assert placement.candidate.minutes == 120

    def test_higher_scoring_work_is_placed_first(self) -> None:
        plan = build(
            TODAY,
            [a_task("low", value="0.2"), a_task("high", value="0.9")],
            a_day(),
            time(6, 0),
            time(23, 30),
        )

        assert plan.placements[0].candidate.title == "high"

    def test_a_protected_block_beats_a_higher_score(self) -> None:
        """The thing that never gets time is exactly what protection is for."""
        plan = build(
            TODAY,
            [a_task("loud", value="0.95"), a_task("railzy", value="0.3", protected=True)],
            a_day(),
            time(6, 0),
            time(23, 30),
        )

        assert plan.placements[0].candidate.title == "railzy"


class TestAttentionMatching:
    def test_deep_work_is_not_scheduled_into_the_commute(self) -> None:
        plan = build(
            TODAY,
            [a_task("refactor", minutes=25, attention=Attention.DEEP)],
            a_day(),
            time(6, 0),
            time(23, 30),
        )

        for placement in plan.placements:
            assert not (time(10, 0) <= placement.start < time(10, 30))

    def test_audio_work_can_use_the_commute(self) -> None:
        plan = build(
            TODAY,
            [a_task("think it through", minutes=20, attention=Attention.AUDIO)],
            a_day(),
            time(6, 0),
            time(23, 30),
        )

        assert plan.placements, "the drive is usable time"

    def test_nothing_needing_a_clear_head_lands_after_the_cutoff(self) -> None:
        plan = build(
            TODAY,
            [a_task(f"deep{i}", minutes=45, attention=Attention.DEEP) for i in range(6)],
            a_day(),
            time(6, 0),
            time(23, 30),
        )

        for placement in plan.placements:
            if placement.candidate.attention is Attention.DEEP:
                assert placement.start < DEEP_WORK_CUTOFF

    def test_the_buffer_share_is_actually_applied(self) -> None:
        plan = build(TODAY, [], a_day(), time(6, 0), time(23, 30))

        expected = int(plan.available_minutes * BUFFER_SHARE)
        assert plan.buffer_minutes == expected


class TestReadability:
    def test_the_plan_reads_as_a_schedule(self) -> None:
        plan = build(TODAY, [a_task("fix signup", value="0.9")], a_day(), time(6, 0), time(23, 30))

        lines = plan.describe()

        assert any("fix signup" in line for line in lines)

    def test_dropped_work_is_listed_with_its_reason(self) -> None:
        plan = build(
            TODAY,
            [a_task(f"t{i}", minutes=120) for i in range(10)],
            a_day(),
            time(6, 0),
            time(23, 30),
        )

        lines = plan.describe()

        assert "Not today:" in lines
