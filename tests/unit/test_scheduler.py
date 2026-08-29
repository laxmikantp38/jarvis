"""The tick, driven by a fixed clock. No real time, no database, no channel."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from aos.app.scheduling.scheduler import Scheduler
from aos.domain.scheduling.recurrence import EVERY_DAY, Recurrence
from aos.domain.scheduling.trigger import NotificationClass, Trigger
from aos.ports.notification import NotificationRequest

KOLKATA = ZoneInfo("Asia/Kolkata")


class FakeTriggers:
    def __init__(self, triggers: list[Trigger]) -> None:
        self._by_key = {t.key: t for t in triggers}

    def all(self) -> list[Trigger]:
        return list(self._by_key.values())

    def get(self, key: str) -> Trigger | None:
        return self._by_key.get(key)

    def save(self, trigger: Trigger) -> None:
        self._by_key[trigger.key] = trigger

    def add_missing(self, triggers: list[Trigger]) -> list[str]:
        added = [t.key for t in triggers if t.key not in self._by_key]
        for t in triggers:
            self._by_key.setdefault(t.key, t)
        return added


class RecordingNotifier:
    def __init__(self) -> None:
        self.requests: list[NotificationRequest] = []

    def submit(self, request: NotificationRequest) -> None:
        self.requests.append(request)


def a_trigger(key: str = "wake", **overrides: object) -> Trigger:
    defaults = {
        "key": key,
        "title": "Morning",
        "body": "Time to get up.",
        "recurrence": Recurrence(at=time(6, 0), days=EVERY_DAY),
        "notification_class": NotificationClass.CRITICAL,
    }
    return Trigger(**{**defaults, **overrides})  # type: ignore[arg-type]


def build(triggers: list[Trigger]) -> tuple[Scheduler, FakeTriggers, RecordingNotifier]:
    repo = FakeTriggers(triggers)
    notifier = RecordingNotifier()
    return Scheduler(repo, notifier, KOLKATA), repo, notifier


class TestFiring:
    def test_nothing_fires_before_it_is_due(self) -> None:
        scheduler, _, notifier = build([a_trigger()])
        midnight = datetime(2026, 8, 29, 18, 0, tzinfo=UTC)
        scheduler.prepare(midnight)

        assert scheduler.tick(midnight) == 0
        assert notifier.requests == []

    def test_a_due_trigger_fires_once(self) -> None:
        scheduler, _, notifier = build([a_trigger()])
        before = datetime(2026, 8, 29, 18, 0, tzinfo=UTC)
        scheduler.prepare(before)

        due = datetime(2026, 8, 30, 0, 30, tzinfo=UTC)  # 06:00 in Kolkata
        assert scheduler.tick(due) == 1
        assert len(notifier.requests) == 1
        assert notifier.requests[0].title == "Morning"

    def test_repeated_ticks_do_not_fire_it_again(self) -> None:
        """The guarantee that matters: a busy loop must not nag."""
        scheduler, _, notifier = build([a_trigger()])
        scheduler.prepare(datetime(2026, 8, 29, 18, 0, tzinfo=UTC))

        due = datetime(2026, 8, 30, 0, 30, tzinfo=UTC)
        for offset in range(10):
            scheduler.tick(due + timedelta(seconds=offset))

        assert len(notifier.requests) == 1

    def test_a_disabled_trigger_never_fires(self) -> None:
        scheduler, _, notifier = build([a_trigger(enabled=False)])
        scheduler.prepare(datetime(2026, 8, 29, 18, 0, tzinfo=UTC))

        scheduler.tick(datetime(2026, 8, 30, 0, 30, tzinfo=UTC))
        assert notifier.requests == []

    def test_the_dedupe_key_identifies_the_occurrence(self) -> None:
        """AD-23: two producers raising the same event must collapse to one."""
        scheduler, _, notifier = build([a_trigger()])
        scheduler.prepare(datetime(2026, 8, 29, 18, 0, tzinfo=UTC))
        scheduler.tick(datetime(2026, 8, 30, 0, 30, tzinfo=UTC))

        assert notifier.requests[0].dedupe_key == "wake@2026-08-30T00:30:00+00:00"


class TestFirstRun:
    def test_a_trigger_created_today_does_not_fire_this_mornings_occurrence(self) -> None:
        scheduler, repo, notifier = build([a_trigger()])
        afternoon = datetime(2026, 8, 29, 8, 30, tzinfo=UTC)  # 14:00 in Kolkata
        scheduler.prepare(afternoon)

        assert scheduler.tick(afternoon) == 0
        assert notifier.requests == []
        assert repo.get("wake").next_due_at.astimezone(KOLKATA).day == 30


class TestCatchUp:
    """FR-28: what came due while the machine was off."""

    def _overdue(
        self, notification_class: NotificationClass
    ) -> tuple[Scheduler, RecordingNotifier]:
        overnight = datetime(2026, 8, 30, 0, 30, tzinfo=UTC)
        trigger = a_trigger(notification_class=notification_class, next_due_at=overnight)
        scheduler, _, notifier = build([trigger])
        scheduler.catch_up(datetime(2026, 8, 30, 6, 0, tzinfo=UTC))
        return scheduler, notifier

    def test_something_important_is_raised_late_rather_than_lost(self) -> None:
        _, notifier = self._overdue(NotificationClass.CRITICAL)
        assert len(notifier.requests) == 1
        assert notifier.requests[0].late is True

    def test_something_informational_is_discarded_not_dumped_at_breakfast(self) -> None:
        _, notifier = self._overdue(NotificationClass.INFORMATIONAL)
        assert notifier.requests == []

    def test_a_missed_occurrence_is_reported_either_way(self) -> None:
        overnight = datetime(2026, 8, 30, 0, 30, tzinfo=UTC)
        trigger = a_trigger(
            notification_class=NotificationClass.INFORMATIONAL, next_due_at=overnight
        )
        scheduler, _, _ = build([trigger])

        missed = scheduler.catch_up(datetime(2026, 8, 30, 6, 0, tzinfo=UTC))

        assert [(m.key, m.reraised) for m in missed] == [("wake", False)]

    def test_catching_up_advances_past_the_missed_occurrence(self) -> None:
        scheduler, notifier = self._overdue(NotificationClass.CRITICAL)
        # A second pass must not raise it again.
        scheduler.catch_up(datetime(2026, 8, 30, 6, 1, tzinfo=UTC))
        assert len(notifier.requests) == 1
