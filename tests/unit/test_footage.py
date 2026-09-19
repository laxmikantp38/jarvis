"""The 10:00 look at whether tonight has anything behind it."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from aos.app.content.footage_watch import FootageWatch
from aos.domain.content.footage import FootageReserve, assess
from aos.domain.scheduling.trigger import NotificationClass
from aos.ports.notification import NotificationRequest

KOLKATA = ZoneInfo("Asia/Kolkata")
TODAY = date(2026, 9, 19)


class TestReserve:
    def test_days_covered_is_clips_over_clips_per_publish(self) -> None:
        assert FootageReserve(clips_available=6, clips_per_publish=2).days_covered == 3

    def test_a_negative_reserve_cannot_exist(self) -> None:
        with pytest.raises(ValueError, match="negative reserve"):
            FootageReserve(clips_available=-1)

    def test_spending_never_goes_below_zero(self) -> None:
        assert FootageReserve(clips_available=1).spend(5).clips_available == 0

    def test_adding_increases_the_reserve(self) -> None:
        assert FootageReserve(clips_available=2).add(3).clips_available == 5

    def test_add_refuses_a_negative(self) -> None:
        with pytest.raises(ValueError, match="spend"):
            FootageReserve(clips_available=2).add(-1)


class TestAssessment:
    def test_silence_when_everything_is_covered(self) -> None:
        """No news is the correct output, not a reassuring message."""
        assert assess(FootageReserve(clips_available=5), TODAY, horizon_days=2) is None

    def test_an_empty_reserve_means_tonight(self) -> None:
        shortfall = assess(FootageReserve(clips_available=0), TODAY, horizon_days=2)
        assert shortfall is not None
        assert shortfall.tonight is True
        assert "Tonight" in shortfall.describe()

    def test_a_thin_reserve_names_the_first_uncovered_date(self) -> None:
        shortfall = assess(FootageReserve(clips_available=1), TODAY, horizon_days=3)
        assert shortfall is not None
        assert shortfall.tonight is False
        assert shortfall.first_uncovered == date(2026, 9, 20)
        assert "1 day of footage left" in shortfall.describe()


class FakeFootage:
    def __init__(self, reserve: FootageReserve) -> None:
        self.reserve = reserve

    def get(self) -> FootageReserve:
        return self.reserve

    def save(self, reserve: FootageReserve) -> None:
        self.reserve = reserve


class FakeChecks:
    def __init__(self) -> None:
        self.runs: dict[str, str] = {}

    def last_run(self, name: str) -> str | None:
        return self.runs.get(name)

    def mark_run(self, name: str, local_day: str) -> None:
        self.runs[name] = local_day


class Recorder:
    def __init__(self) -> None:
        self.requests: list[NotificationRequest] = []

    def submit(self, request: NotificationRequest) -> None:
        self.requests.append(request)


def watch(clips: int, checks: FakeChecks | None = None) -> tuple[FootageWatch, Recorder]:
    recorder = Recorder()
    return (
        FootageWatch(
            footage=FakeFootage(FootageReserve(clips_available=clips)),
            checks=checks or FakeChecks(),
            notifier=recorder,
            zone=KOLKATA,
            check_at=time(10, 0),
            horizon_days=2,
        ),
        recorder,
    )


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 19, hour, minute, tzinfo=KOLKATA).astimezone(UTC)


class TestWatch:
    def test_it_does_not_run_before_the_morning_check_time(self) -> None:
        checker, recorder = watch(clips=0)
        assert checker.run_if_due(at(8, 0)) is False
        assert recorder.requests == []

    def test_it_warns_in_the_morning_not_the_evening(self) -> None:
        """The whole point: 10:00, while there is still a day to act in."""
        checker, recorder = watch(clips=0)
        assert checker.run_if_due(at(10, 0)) is True
        assert len(recorder.requests) == 1
        assert "Tonight" in recorder.requests[0].body

    def test_an_empty_reserve_is_important_enough_to_get_through(self) -> None:
        _, recorder = watch(clips=0)
        checker, recorder = watch(clips=0)
        checker.run_if_due(at(10, 0))
        assert recorder.requests[0].notification_class is NotificationClass.IMPORTANT

    def test_a_covered_day_says_nothing_at_all(self) -> None:
        checker, recorder = watch(clips=5)
        assert checker.run_if_due(at(10, 0)) is True
        assert recorder.requests == []

    def test_it_runs_once_a_day_however_often_it_is_ticked(self) -> None:
        checker, recorder = watch(clips=0)
        for minute in range(0, 50, 10):
            checker.run_if_due(at(10, minute))
        assert len(recorder.requests) == 1

    def test_a_restart_later_the_same_day_does_not_nag_again(self) -> None:
        checks = FakeChecks()
        first, _ = watch(clips=0, checks=checks)
        first.run_if_due(at(10, 0))

        restarted, recorder = watch(clips=0, checks=checks)
        assert restarted.run_if_due(at(14, 0)) is False
        assert recorder.requests == []
