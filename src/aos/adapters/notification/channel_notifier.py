"""Delivery across channels: policy first, then the wire.

The scheduler hands over a request and stops caring. Classification, quiet
hours, the daily budget, ordering and failure handling all live here (AD-11).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from aos.domain.notification.policy import NotificationPolicy, Verdict
from aos.ports.channel import Channel, OutboundMessage
from aos.ports.notification import NotificationRequest

log = logging.getLogger(__name__)


@dataclass
class Tally:
    """What today cost the user, in interruptions."""

    day: date
    delivered: int = 0
    suppressed_duplicate: int = 0
    deferred: int = 0
    batched: int = 0
    failed: int = 0

    def roll_over(self, today: date) -> Tally:
        return self if self.day == today else Tally(day=today)


@dataclass(frozen=True, slots=True)
class Held:
    request: NotificationRequest
    release_at: datetime
    reason: str


class ChannelNotifier:
    def __init__(
        self,
        channels: list[Channel],
        policy: NotificationPolicy,
        zone: ZoneInfo,
        now: Callable[[], datetime],
    ) -> None:
        if not channels:
            msg = "a notifier with no channel would deliver nothing, silently"
            raise ValueError(msg)
        self._channels = channels
        self._policy = policy
        self._zone = zone
        self._now = now
        self._delivered: set[str] = set()
        self._held: list[Held] = []
        self._batched: list[NotificationRequest] = []
        self._tally = Tally(day=now().astimezone(zone).date())

    # --- intake ----------------------------------------------------------

    def submit(self, request: NotificationRequest) -> None:
        now = self._now()
        self._tally = self._tally.roll_over(now.astimezone(self._zone).date())

        if request.dedupe_key in self._delivered:
            self._tally.suppressed_duplicate += 1
            log.debug("suppressed duplicate %s", request.dedupe_key)
            return

        decision = self._policy.decide(
            request.notification_class, now, self._zone, self._tally.delivered
        )

        if decision.verdict is Verdict.DEFER:
            self._hold(request, now, decision.reason)
        elif decision.verdict is Verdict.BATCH:
            self._batched.append(request)
            self._tally.batched += 1
            log.info("batched %s: %s", request.dedupe_key, decision.reason)
        else:
            self._deliver(request)

    def release_due(self) -> int:
        """Send anything whose window has opened. Called on each tick."""
        now = self._now()
        ready = [held for held in self._held if held.release_at <= now]
        self._held = [held for held in self._held if held.release_at > now]
        for held in ready:
            log.info("releasing %s held for %s", held.request.dedupe_key, held.reason)
            self._deliver(held.request)
        return len(ready)

    def drain_batched(self) -> list[NotificationRequest]:
        """Hand the folded-up ones to whoever is assembling a briefing."""
        pending, self._batched = self._batched, []
        return pending

    @property
    def tally(self) -> Tally:
        return self._tally

    @property
    def pending(self) -> int:
        return len(self._held) + len(self._batched)

    # --- delivery --------------------------------------------------------

    def _hold(self, request: NotificationRequest, now: datetime, reason: str) -> None:
        release_at = self._policy.releases_at(now, self._zone)
        if release_at is None:  # pragma: no cover - defer implies a window
            self._deliver(request)
            return
        self._held.append(Held(request=request, release_at=release_at, reason=reason))
        self._tally.deferred += 1
        log.info("holding %s until %s (%s)", request.dedupe_key, release_at.isoformat(), reason)

    def _deliver(self, request: NotificationRequest) -> None:
        message = OutboundMessage(
            dedupe_key=request.dedupe_key,
            title=request.title,
            body=request.body,
            notification_class=request.notification_class,
            late=request.late,
        )
        for channel in self._channels:
            result = channel.send(message)
            if result.delivered:
                self._delivered.add(request.dedupe_key)
                self._tally.delivered += 1
                log.info("delivered %s via %s", request.dedupe_key, result.channel)
                return
            # Recorded, not swallowed: a silent failure is indistinguishable
            # from nothing having been due.
            log.warning(
                "delivery failed on %s for %s: %s",
                result.channel,
                request.dedupe_key,
                result.detail,
            )
        self._tally.failed += 1
        log.error("every channel failed for %s", request.dedupe_key)
