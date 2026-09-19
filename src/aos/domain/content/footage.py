"""Whether there is anything to publish with.

The nightly upload is a daily deadline fed by footage shot on the three days a
week the commute happens. The gap is arithmetic, and knowing it at 10:00 is
worth far more than discovering it at 23:10.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class FootageReserve:
    clips_available: int
    clips_per_publish: int = 1

    def __post_init__(self) -> None:
        if self.clips_available < 0:
            msg = "a negative reserve is not a thing that can exist"
            raise ValueError(msg)
        if self.clips_per_publish < 1:
            msg = "a publish needs at least one clip"
            raise ValueError(msg)

    @property
    def days_covered(self) -> int:
        return self.clips_available // self.clips_per_publish

    def covers(self, horizon_days: int) -> bool:
        return self.days_covered >= horizon_days

    def first_uncovered(self, today: date, horizon_days: int) -> date | None:
        """The first publish date with nothing behind it, within the horizon."""
        if self.covers(horizon_days):
            return None
        return today + timedelta(days=self.days_covered)

    def spend(self, publishes: int = 1) -> FootageReserve:
        used = publishes * self.clips_per_publish
        return FootageReserve(
            clips_available=max(0, self.clips_available - used),
            clips_per_publish=self.clips_per_publish,
        )

    def add(self, clips: int) -> FootageReserve:
        if clips < 0:
            msg = "use spend() to reduce the reserve"
            raise ValueError(msg)
        return FootageReserve(
            clips_available=self.clips_available + clips,
            clips_per_publish=self.clips_per_publish,
        )


@dataclass(frozen=True, slots=True)
class Shortfall:
    days_covered: int
    horizon_days: int
    first_uncovered: date

    @property
    def tonight(self) -> bool:
        return self.days_covered == 0

    def describe(self) -> str:
        if self.tonight:
            return (
                "Tonight's upload has no footage behind it. "
                "Worth catching something today, or picking a format that needs none."
            )
        days = self.days_covered
        plural = "day" if days == 1 else "days"
        return (
            f"{days} {plural} of footage left - the {self.first_uncovered:%a %d %b} "
            f"upload is the first with nothing behind it."
        )


def assess(reserve: FootageReserve, today: date, horizon_days: int) -> Shortfall | None:
    """None when every upload inside the horizon is covered - and then say nothing."""
    uncovered = reserve.first_uncovered(today, horizon_days)
    if uncovered is None:
        return None
    return Shortfall(
        days_covered=reserve.days_covered,
        horizon_days=horizon_days,
        first_uncovered=uncovered,
    )
