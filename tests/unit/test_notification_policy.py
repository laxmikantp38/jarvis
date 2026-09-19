"""Attention rules. Pure: same inputs, same verdict, no clock and no I/O."""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

import pytest

from aos.domain.notification.policy import NotificationPolicy, TimeWindow, Verdict
from aos.domain.scheduling.trigger import NotificationClass

KOLKATA = ZoneInfo("Asia/Kolkata")


def at(hour: int, minute: int = 0) -> datetime:
    """A UTC instant corresponding to the given wall-clock time in Kolkata."""
    return datetime(2026, 9, 19, hour, minute, tzinfo=KOLKATA).astimezone(UTC)


def policy(budget: int = 12) -> NotificationPolicy:
    return NotificationPolicy(
        daily_budget=budget,
        quiet_hours=TimeWindow.parse("23:45-05:45"),
        blackouts=(TimeWindow.parse("20:00-20:30"),),
    )


class TestTimeWindow:
    def test_a_window_that_wraps_midnight(self) -> None:
        window = TimeWindow.parse("23:45-05:45")
        assert window.wraps_midnight
        assert window.contains(time(2, 0))
        assert window.contains(time(23, 50))
        assert not window.contains(time(12, 0))

    def test_an_ordinary_window(self) -> None:
        window = TimeWindow.parse("20:00-20:30")
        assert not window.wraps_midnight
        assert window.contains(time(20, 15))
        assert not window.contains(time(20, 30)), "the end is exclusive"

    def test_a_malformed_window_is_rejected_at_startup(self) -> None:
        with pytest.raises(ValueError, match="23:45-05:45"):
            TimeWindow.parse("sometime at night")


class TestCritical:
    def test_critical_interrupts_quiet_hours(self) -> None:
        decision = policy().decide(NotificationClass.CRITICAL, at(2, 0), KOLKATA, 0)
        assert decision.verdict is Verdict.DELIVER

    def test_critical_interrupts_the_standup(self) -> None:
        decision = policy().decide(NotificationClass.CRITICAL, at(20, 10), KOLKATA, 0)
        assert decision.verdict is Verdict.DELIVER

    def test_critical_ignores_a_spent_budget(self) -> None:
        decision = policy(budget=1).decide(NotificationClass.CRITICAL, at(12, 0), KOLKATA, 99)
        assert decision.verdict is Verdict.DELIVER


class TestQuietHours:
    def test_an_ordinary_nudge_at_two_in_the_morning_is_held(self) -> None:
        decision = policy().decide(NotificationClass.NORMAL, at(2, 0), KOLKATA, 0)
        assert decision.verdict is Verdict.DEFER
        assert decision.reason == "quiet hours"

    def test_it_is_released_when_the_window_closes(self) -> None:
        release = policy().releases_at(at(2, 0), KOLKATA)
        assert release is not None
        assert release.astimezone(KOLKATA).strftime("%H:%M") == "05:45"

    def test_the_standup_is_protected_too(self) -> None:
        decision = policy().decide(NotificationClass.IMPORTANT, at(20, 10), KOLKATA, 0)
        assert decision.verdict is Verdict.DEFER
        assert decision.reason == "blackout window"

    def test_nothing_is_held_outside_a_window(self) -> None:
        assert policy().releases_at(at(12, 0), KOLKATA) is None


class TestBudget:
    def test_an_ordinary_nudge_within_budget_goes_out(self) -> None:
        decision = policy(budget=12).decide(NotificationClass.NORMAL, at(12, 0), KOLKATA, 5)
        assert decision.verdict is Verdict.DELIVER

    def test_a_spent_budget_folds_the_rest_into_a_briefing(self) -> None:
        decision = policy(budget=3).decide(NotificationClass.NORMAL, at(12, 0), KOLKATA, 3)
        assert decision.verdict is Verdict.BATCH
        assert "3" in decision.reason

    def test_important_is_never_capped(self) -> None:
        """A real deadline is not noise, however noisy the day has been."""
        decision = policy(budget=1).decide(NotificationClass.IMPORTANT, at(12, 0), KOLKATA, 99)
        assert decision.verdict is Verdict.DELIVER

    def test_informational_is_capped(self) -> None:
        decision = policy(budget=1).decide(NotificationClass.INFORMATIONAL, at(12, 0), KOLKATA, 1)
        assert decision.verdict is Verdict.BATCH
