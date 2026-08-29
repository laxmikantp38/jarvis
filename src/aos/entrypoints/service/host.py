"""Service lifecycle: wiring only, no domain logic.

Starts, announces itself, reports anything it missed while it was down, then
holds until stopped. A failure here is surfaced to the user rather than left
in a log nobody opens (FR-97).
"""

from __future__ import annotations

import logging
import signal
import threading
from dataclasses import dataclass
from datetime import timedelta

from aos.adapters.system.file_heartbeat import FileHeartbeat
from aos.adapters.system.file_instance_lock import FileInstanceLock
from aos.adapters.system.settings import Settings
from aos.adapters.system.system_clock import SystemClock
from aos.common import paths
from aos.common.logging_setup import configure
from aos.common.timeutil import utc_now

log = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = timedelta(seconds=30)
DOWNTIME_WORTH_REPORTING = timedelta(minutes=5)


@dataclass(frozen=True)
class Downtime:
    since: str
    duration: timedelta


def _downtime(heartbeat: FileHeartbeat) -> Downtime | None:
    previous = heartbeat.last_beat()
    if previous is None:
        return None
    gap = utc_now() - previous
    if gap < DOWNTIME_WORTH_REPORTING:
        return None
    return Downtime(since=previous.isoformat(), duration=gap)


def _describe(gap: timedelta) -> str:
    hours, seconds = divmod(int(gap.total_seconds()), 3600)
    minutes = seconds // 60
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


class ServiceHost:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._clock = SystemClock(settings.zone)
        self._heartbeat = FileHeartbeat(paths.state_dir(settings.environment) / "heartbeat")
        self._lock = FileInstanceLock(paths.lock_file(settings.environment))
        self._stop = threading.Event()

    def run(self) -> int:
        configure(
            level=self._settings.logging.level,
            log_directory=paths.log_dir(self._settings.environment),
            json_file=self._settings.logging.json_file,
        )
        # AD-17: nothing that fires or polls starts before the lock is held.
        with self._lock:
            self._install_signal_handlers()
            self._announce()
            self._report_downtime()
            self._serve()
        log.info("stopped cleanly")
        return 0

    def _announce(self) -> None:
        name = self._settings.agent_name
        local = self._clock.now_local().strftime("%a %d %b, %H:%M")
        print(f"\n  {name} is online.  {local}  ({self._settings.environment})", flush=True)
        if not self._settings.is_live:
            print("  dev environment - channels are stubbed, nothing will be sent.\n", flush=True)
        else:
            print("", flush=True)
        log.info("%s online in %s", name, self._settings.environment)

    def _report_downtime(self) -> None:
        """AD-26 / NFR-20: say what was missed instead of pretending nothing was."""
        gap = _downtime(self._heartbeat)
        if gap is None:
            return
        window = _describe(gap.duration)
        print(f"  I was not running for {window} (since {gap.since}).", flush=True)
        print("  Scheduled nudges only fire while this machine is on.\n", flush=True)
        log.warning("downtime detected: %s since %s", window, gap.since)

    def _serve(self) -> None:
        self._heartbeat.beat()
        log.info("heartbeat started; ctrl-c to stop")
        while not self._stop.wait(HEARTBEAT_INTERVAL.total_seconds()):
            self._heartbeat.beat()

    def _install_signal_handlers(self) -> None:
        def handle(signum: int, _frame: object) -> None:
            log.info("received signal %s, shutting down", signum)
            self._stop.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, handle)
