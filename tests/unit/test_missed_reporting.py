"""What the user is told about time the system was not running (FR-28, NFR-20)."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from aos.app.scheduling.scheduler import MissedOccurrence
from aos.entrypoints.service.host import ServiceHost, describe

KOLKATA = ZoneInfo("Asia/Kolkata")


class TestDescribeGap:
    def test_minutes_only_when_under_an_hour(self) -> None:
        from datetime import timedelta

        assert describe(timedelta(minutes=42)) == "42m"

    def test_hours_and_minutes_for_a_long_outage(self) -> None:
        from datetime import timedelta

        assert describe(timedelta(hours=9, minutes=14)) == "9h 14m"

    def test_a_multi_day_outage_reads_in_hours_rather_than_days(self) -> None:
        from datetime import timedelta

        assert describe(timedelta(days=2, hours=3)) == "51h 0m"


class TestMissedReport:
    def _host_with_zone(self) -> ServiceHost:
        from aos.adapters.system.settings import Settings

        host = ServiceHost(Settings(environment="dev", timezone="Asia/Kolkata"))

        class Stub:
            zone = KOLKATA

        host._runtime = Stub()  # type: ignore[assignment]
        return host

    def test_nothing_is_printed_when_nothing_was_missed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self._host_with_zone()._report_missed([])
        assert capsys.readouterr().out == ""

    def test_each_occurrence_is_listed_with_its_fate(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missed = [
            MissedOccurrence(
                key="wake",
                title="Morning",
                due_at=datetime(2026, 9, 19, 0, 30, tzinfo=UTC),
                reraised=True,
            ),
            MissedOccurrence(
                key="gym-return",
                title="Wrap up at the gym",
                due_at=datetime(2026, 9, 19, 3, 40, tzinfo=UTC),
                reraised=False,
            ),
        ]
        self._host_with_zone()._report_missed(missed)
        out = capsys.readouterr().out

        assert "2 came due" in out
        assert "Morning" in out and "resent" in out
        assert "Wrap up at the gym" in out and "let go" in out

    def test_occurrences_are_listed_in_the_order_they_came_due(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missed = [
            MissedOccurrence("b", "Later", datetime(2026, 9, 19, 5, 0, tzinfo=UTC), False),
            MissedOccurrence("a", "Earlier", datetime(2026, 9, 19, 1, 0, tzinfo=UTC), False),
        ]
        self._host_with_zone()._report_missed(missed)
        out = capsys.readouterr().out

        assert out.index("Earlier") < out.index("Later")

    def test_times_are_shown_in_the_users_zone(self, capsys: pytest.CaptureFixture[str]) -> None:
        missed = [
            MissedOccurrence("wake", "Morning", datetime(2026, 9, 19, 0, 30, tzinfo=UTC), True)
        ]
        self._host_with_zone()._report_missed(missed)

        assert "06:00" in capsys.readouterr().out, "00:30 UTC is 06:00 in Kolkata"
