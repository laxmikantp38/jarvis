"""UTC storage, local evaluation (AD-16).

Every timestamp persisted is UTC. Schedules are evaluated in the user's zone,
so a DST transition neither double-fires nor silently skips a trigger.
"""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_utc(moment: datetime) -> datetime:
    """Normalise to UTC. A naive datetime is rejected rather than guessed at."""
    if moment.tzinfo is None:
        msg = "naive datetime: attach a timezone before storing"
        raise ValueError(msg)
    return moment.astimezone(UTC)


def to_zone(moment: datetime, zone: ZoneInfo) -> datetime:
    return to_utc(moment).astimezone(zone)


def isoformat_utc(moment: datetime) -> str:
    return to_utc(moment).isoformat().replace("+00:00", "Z")
