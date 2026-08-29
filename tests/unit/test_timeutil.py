from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from aos.common.timeutil import isoformat_utc, to_utc, to_zone, utc_now


def test_now_is_timezone_aware_and_utc() -> None:
    moment = utc_now()
    assert moment.tzinfo is not None
    assert moment.utcoffset().total_seconds() == 0


def test_naive_datetimes_are_rejected_not_guessed() -> None:
    with pytest.raises(ValueError, match="naive datetime"):
        to_utc(datetime(2026, 8, 10, 6, 0))


def test_local_evaluation_preserves_the_instant() -> None:
    kolkata = ZoneInfo("Asia/Kolkata")
    six_am_local = datetime(2026, 8, 10, 6, 0, tzinfo=kolkata)
    assert to_utc(six_am_local) == datetime(2026, 8, 10, 0, 30, tzinfo=UTC)
    assert to_zone(six_am_local, kolkata).hour == 6


def test_isoformat_uses_z_suffix() -> None:
    assert isoformat_utc(datetime(2026, 8, 10, 0, 30, tzinfo=UTC)) == "2026-08-10T00:30:00Z"
