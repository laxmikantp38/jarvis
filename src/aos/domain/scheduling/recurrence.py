"""When a trigger is next due. Pure arithmetic, no I/O, no model (AD-1).

Wall-clock times are what a person means: "wake me at 06:00" is 06:00 where the
person is, whatever the offset happens to be that day. So occurrences are
computed in the local zone and converted to UTC for storage (AD-16).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
WEEKDAYS = frozenset({MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY})
EVERY_DAY = frozenset(range(7))

_SEARCH_HORIZON_DAYS = 8  # a week plus one, enough for any weekday set


@dataclass(frozen=True, slots=True)
class Recurrence:
    """A wall-clock time on a chosen set of weekdays."""

    at: time
    days: frozenset[int] = EVERY_DAY

    def __post_init__(self) -> None:
        if not self.days:
            msg = "a recurrence with no days would never fire"
            raise ValueError(msg)
        if not self.days <= EVERY_DAY:
            msg = f"weekdays must be 0-6, got {sorted(self.days)}"
            raise ValueError(msg)
        if self.at.tzinfo is not None:
            msg = "the time of day is wall-clock; the zone belongs to the schedule"
            raise ValueError(msg)

    def describe(self) -> str:
        when = self.at.strftime("%H:%M")
        if self.days == EVERY_DAY:
            return f"every day at {when}"
        if self.days == WEEKDAYS:
            return f"weekdays at {when}"
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        chosen = " ".join(names[d] for d in sorted(self.days))
        return f"{chosen} at {when}"


def _local_instant(day: date, at: time, zone: ZoneInfo) -> datetime:
    """The instant a wall-clock time falls on, as UTC.

    Across a spring-forward gap the named wall time does not exist; zoneinfo
    resolves it to a real instant just after the jump, which is the closest
    honest answer to "wake me at 06:00" on a day where 06:00 was skipped.
    """
    return datetime.combine(day, at, tzinfo=zone).astimezone(UTC)


def next_occurrence(after: datetime, rule: Recurrence, zone: ZoneInfo) -> datetime:
    """First instant strictly after `after` that satisfies the rule, in UTC.

    Strictly after is what prevents a double fire: the same instant can be
    evaluated repeatedly and will never be returned twice.
    """
    if after.tzinfo is None:
        msg = "naive datetime: attach a timezone before scheduling"
        raise ValueError(msg)
    after_utc = after.astimezone(UTC)
    start = after_utc.astimezone(zone).date()

    for offset in range(_SEARCH_HORIZON_DAYS):
        day = start + timedelta(days=offset)
        if day.weekday() not in rule.days:
            continue
        candidate = _local_instant(day, rule.at, zone)
        if candidate > after_utc:
            return candidate

    msg = f"no occurrence within {_SEARCH_HORIZON_DAYS} days for {rule.describe()}"
    raise RuntimeError(msg)


def occurrences_between(
    start: datetime, end: datetime, rule: Recurrence, zone: ZoneInfo
) -> list[datetime]:
    """Every occurrence in (start, end]. Used to report what was missed while down."""
    found: list[datetime] = []
    cursor = start
    while True:
        cursor = next_occurrence(cursor, rule, zone)
        if cursor > end:
            return found
        found.append(cursor)
