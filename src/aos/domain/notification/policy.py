"""Whether a notification goes out now, later, or not at all.

Attention is the scarcest thing this system spends, so the rules are explicit
and pure: same inputs, same decision, no clock read and no I/O (AD-1, NFR-8).

Silence is a valid output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum, auto
from zoneinfo import ZoneInfo

from aos.domain.scheduling.trigger import NotificationClass


class Verdict(StrEnum):
    DELIVER = auto()
    DEFER = auto()
    """Held for the next permitted window - quiet hours or a blackout."""
    BATCH = auto()
    """Budget spent; folded into the next briefing instead of interrupting."""


@dataclass(frozen=True, slots=True)
class Decision:
    verdict: Verdict
    reason: str

    @property
    def delivers(self) -> bool:
        return self.verdict is Verdict.DELIVER


@dataclass(frozen=True, slots=True)
class TimeWindow:
    """A wall-clock window, which may wrap past midnight."""

    start: time
    end: time

    @classmethod
    def parse(cls, text: str) -> TimeWindow:
        try:
            start, end = (part.strip() for part in text.split("-", 1))
            return cls(time.fromisoformat(start), time.fromisoformat(end))
        except ValueError as exc:
            msg = f"expected a window like '23:45-05:45', got {text!r}"
            raise ValueError(msg) from exc

    @property
    def wraps_midnight(self) -> bool:
        return self.start > self.end

    def contains(self, moment: time) -> bool:
        if self.wraps_midnight:
            return moment >= self.start or moment < self.end
        return self.start <= moment < self.end

    def next_end_after(self, moment: datetime) -> datetime:
        """When this window lets go, given an instant inside it."""
        local_date: date = moment.date()
        closing = datetime.combine(local_date, self.end, tzinfo=moment.tzinfo)
        if closing <= moment:
            closing = datetime.combine(
                local_date.fromordinal(local_date.toordinal() + 1),
                self.end,
                tzinfo=moment.tzinfo,
            )
        return closing


@dataclass(frozen=True, slots=True)
class NotificationPolicy:
    daily_budget: int
    quiet_hours: TimeWindow | None = None
    blackouts: tuple[TimeWindow, ...] = ()

    def decide(
        self,
        notification_class: NotificationClass,
        now: datetime,
        zone: ZoneInfo,
        spent_today: int,
    ) -> Decision:
        # Critical interrupts anything, including the standup. That is what the
        # class means; if it did not, nothing would.
        if notification_class.may_interrupt:
            return Decision(Verdict.DELIVER, "critical")

        local = now.astimezone(zone).timetz().replace(tzinfo=None)

        if self.quiet_hours and self.quiet_hours.contains(local):
            return Decision(Verdict.DEFER, "quiet hours")

        for window in self.blackouts:
            if window.contains(local):
                return Decision(Verdict.DEFER, "blackout window")

        # Important still counts toward nothing: a real deadline is not noise.
        if notification_class is NotificationClass.IMPORTANT:
            return Decision(Verdict.DELIVER, "important")

        if spent_today >= self.daily_budget:
            return Decision(Verdict.BATCH, f"daily budget of {self.daily_budget} spent")

        return Decision(Verdict.DELIVER, "within budget")

    def releases_at(self, now: datetime, zone: ZoneInfo) -> datetime | None:
        """When a deferred notification may go out."""
        local_now = now.astimezone(zone)
        local = local_now.timetz().replace(tzinfo=None)
        for window in (*([self.quiet_hours] if self.quiet_hours else []), *self.blackouts):
            if window.contains(local):
                return window.next_end_after(local_now).astimezone(now.tzinfo)
        return None
