"""Composition root: the one place adapters are chosen.

The environment picks the adapter set, not a flag someone might forget, so a
development run cannot reach a real channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from aos.adapters.notification.console import ConsoleNotifier
from aos.adapters.persistence.sqlite.engine import create_sqlite_engine, session_factory
from aos.adapters.persistence.sqlite.trigger_repository import SqliteTriggerRepository
from aos.adapters.system.file_heartbeat import FileHeartbeat
from aos.adapters.system.settings import Settings
from aos.adapters.system.system_clock import SystemClock
from aos.app.scheduling.scheduler import Scheduler
from aos.common import paths
from aos.ports.notification import Notifier


@dataclass(frozen=True)
class Runtime:
    settings: Settings
    clock: SystemClock
    zone: ZoneInfo
    heartbeat: FileHeartbeat
    triggers: SqliteTriggerRepository
    notifier: Notifier
    scheduler: Scheduler


def _notifier_for(settings: Settings) -> Notifier:
    # Telegram arrives in story 1.4. Until then, and always in dev, the console
    # is the only place a notification can land.
    del settings
    return ConsoleNotifier()


def build(settings: Settings) -> Runtime:
    zone = settings.zone
    environment = settings.environment

    engine = create_sqlite_engine(paths.database_file(environment))
    triggers = SqliteTriggerRepository(session_factory(engine))
    notifier = _notifier_for(settings)

    return Runtime(
        settings=settings,
        clock=SystemClock(zone),
        zone=zone,
        heartbeat=FileHeartbeat(paths.state_dir(environment) / "heartbeat"),
        triggers=triggers,
        notifier=notifier,
        scheduler=Scheduler(triggers, notifier, zone),
    )
