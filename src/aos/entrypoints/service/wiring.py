"""Composition root: the one place adapters are chosen.

The environment picks the adapter set, not a flag someone might forget, so a
development run cannot reach a real channel.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from aos.adapters.channel.stub import StubChannel
from aos.adapters.channel.telegram_channel import TelegramChannel
from aos.adapters.notification.channel_notifier import ChannelNotifier
from aos.adapters.persistence.sqlite.engine import create_sqlite_engine, session_factory
from aos.adapters.persistence.sqlite.trigger_repository import SqliteTriggerRepository
from aos.adapters.system.file_heartbeat import FileHeartbeat
from aos.adapters.system.keyring_secrets import KeyringSecretStore
from aos.adapters.system.settings import Settings
from aos.adapters.system.system_clock import SystemClock
from aos.app.intake.router import Intake
from aos.app.scheduling.scheduler import Scheduler
from aos.common import paths
from aos.common.timeutil import utc_now
from aos.ports.channel import Channel

log = logging.getLogger(__name__)

TELEGRAM_TOKEN = "telegram_token"  # noqa: S105 - the lookup name, not a secret


@dataclass(frozen=True)
class Runtime:
    settings: Settings
    clock: SystemClock
    zone: ZoneInfo
    heartbeat: FileHeartbeat
    triggers: SqliteTriggerRepository
    channels: list[Channel]
    notifier: ChannelNotifier
    scheduler: Scheduler
    intake: Intake


def _channels_for(settings: Settings) -> list[Channel]:
    """Ordered by preference. The last one always works, so nothing is lost."""
    console = StubChannel("console")

    if not settings.is_live:
        # Not a policy check that could be bypassed: in dev the real adapter is
        # never constructed, so there is nothing to accidentally send through.
        return [console]

    if not settings.telegram.usable:
        log.info("telegram not configured; delivering to the console only")
        return [console]

    token = KeyringSecretStore().get(TELEGRAM_TOKEN)
    if not token:
        log.warning(
            "telegram is enabled but no token is stored; run: python run.py --set-secret %s",
            TELEGRAM_TOKEN,
        )
        return [console]

    return [TelegramChannel(token, settings.telegram.chat_id), console]


def build(settings: Settings) -> Runtime:
    zone = settings.zone
    environment = settings.environment

    engine = create_sqlite_engine(paths.database_file(environment))
    triggers = SqliteTriggerRepository(session_factory(engine))
    channels = _channels_for(settings)
    notifier = ChannelNotifier(channels)

    return Runtime(
        settings=settings,
        clock=SystemClock(zone),
        zone=zone,
        heartbeat=FileHeartbeat(paths.state_dir(environment) / "heartbeat"),
        triggers=triggers,
        channels=channels,
        notifier=notifier,
        scheduler=Scheduler(triggers, notifier, zone),
        intake=Intake(
            triggers=triggers,
            zone=zone,
            agent_name=settings.agent_name,
            now=utc_now,
        ),
    )
