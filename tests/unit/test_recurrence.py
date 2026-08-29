"""Scheduling arithmetic. No clock, no database, no model - just the maths."""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

import pytest

from aos.domain.scheduling.recurrence import (
    EVERY_DAY,
    WEEKDAYS,
    Recurrence,
    next_occurrence,
    occurrences_between,
)

KOLKATA = ZoneInfo("Asia/Kolkata")
NEW_YORK = ZoneInfo("America/New_York")


def test_a_wall_clock_time_becomes_the_right_utc_instant() -> None:
    rule = Recurrence(at=time(6, 0))
    friday_night = datetime(2026, 8, 28, 20, 0, tzinfo=UTC)
    # 06:00 in Kolkata is 00:30 UTC.
    assert next_occurrence(friday_night, rule, KOLKATA) == datetime(2026, 8, 29, 0, 30, tzinfo=UTC)


def test_weekday_rules_skip_the_weekend() -> None:
    rule = Recurrence(at=time(19, 50), days=WEEKDAYS)
    saturday = datetime(2026, 8, 29, 18, 0, tzinfo=KOLKATA)
    following = next_occurrence(saturday, rule, KOLKATA)
    assert following.astimezone(KOLKATA).strftime("%a") == "Mon"


def test_the_same_instant_is_never_returned_twice() -> None:
    """Strictly-after is what makes a double fire impossible."""
    rule = Recurrence(at=time(6, 0))
    first = next_occurrence(datetime(2026, 8, 29, 0, 0, tzinfo=UTC), rule, KOLKATA)
    second = next_occurrence(first, rule, KOLKATA)
    assert second > first
    assert (second - first).days == 1


def test_a_rule_with_no_days_is_rejected() -> None:
    with pytest.raises(ValueError, match="never fire"):
        Recurrence(at=time(6, 0), days=frozenset())


def test_the_time_of_day_must_be_wall_clock() -> None:
    with pytest.raises(ValueError, match="wall-clock"):
        Recurrence(at=time(6, 0, tzinfo=UTC))


class TestDaylightSaving:
    """India has no DST, but the arithmetic must not depend on that."""

    def test_spring_forward_neither_skips_nor_repeats(self) -> None:
        # 2026-03-08: New York jumps 02:00 -> 03:00.
        rule = Recurrence(at=time(6, 0), days=EVERY_DAY)
        window_start = datetime(2026, 3, 6, 12, 0, tzinfo=UTC)
        window_end = datetime(2026, 3, 11, 12, 0, tzinfo=UTC)

        found = occurrences_between(window_start, window_end, rule, NEW_YORK)

        local_times = [m.astimezone(NEW_YORK).strftime("%m-%d %H:%M") for m in found]
        assert local_times == [
            "03-07 06:00",
            "03-08 06:00",
            "03-09 06:00",
            "03-10 06:00",
            "03-11 06:00",
        ]
        assert len(set(found)) == len(found), "no instant may repeat"

    def test_fall_back_neither_skips_nor_repeats(self) -> None:
        # 2026-11-01: New York falls back 02:00 -> 01:00.
        rule = Recurrence(at=time(1, 30), days=EVERY_DAY)
        found = occurrences_between(
            datetime(2026, 10, 30, 12, 0, tzinfo=UTC),
            datetime(2026, 11, 3, 12, 0, tzinfo=UTC),
            rule,
            NEW_YORK,
        )
        assert len(found) == 4, "one occurrence per day across the ambiguous hour"
        assert len(set(found)) == len(found)

    def test_the_offset_actually_changes_across_the_boundary(self) -> None:
        """Proves the test above is exercising a real transition, not a flat zone."""
        rule = Recurrence(at=time(6, 0))
        before = next_occurrence(datetime(2026, 3, 6, 12, 0, tzinfo=UTC), rule, NEW_YORK)
        after = next_occurrence(datetime(2026, 3, 9, 12, 0, tzinfo=UTC), rule, NEW_YORK)
        assert before.astimezone(NEW_YORK).utcoffset() != after.astimezone(NEW_YORK).utcoffset()
