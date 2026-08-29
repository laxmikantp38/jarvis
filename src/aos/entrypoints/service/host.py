"""Service lifecycle: wiring and loop, no domain logic.

Starts, announces itself, reports anything it missed, then ticks the scheduler
until stopped. A failure here is surfaced to the user rather than left in a log
nobody opens (FR-97).
"""

from __future__ import annotations

import logging
import signal
import threading
from dataclasses import dataclass
from datetime import timedelta

from aos.adapters.system.file_instance_lock import FileInstanceLock
from aos.adapters.system.settings import Settings
from aos.app.scheduling.routine import default_routine
from aos.common import paths
from aos.common.logging_setup import configure
from aos.common.timeutil import utc_now
from aos.entrypoints.service.wiring import Runtime, build

log = logging.getLogger(__name__)

TICK = timedelta(seconds=20)
DOWNTIME_WORTH_REPORTING = timedelta(minutes=5)


@dataclass(frozen=True)
class Downtime:
    since: str
    duration: timedelta


def describe(gap: timedelta) -> str:
    hours, seconds = divmod(int(gap.total_seconds()), 3600)
    minutes = seconds // 60
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


class ServiceHost:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._runtime: Runtime | None = None
        self._stop = threading.Event()

    def run(self) -> int:
        configure(
            level=self._settings.logging.level,
            log_directory=paths.log_dir(self._settings.environment),
            json_file=self._settings.logging.json_file,
        )
        # AD-17: nothing that fires or polls starts before the lock is held.
        with FileInstanceLock(paths.lock_file(self._settings.environment)):
            self._runtime = build(self._settings)
            self._install_signal_handlers()
            self._announce()
            self._report_downtime()
            self._prepare_schedule()
            self._serve()
        log.info("stopped cleanly")
        return 0

    # --- startup ---------------------------------------------------------

    def _announce(self) -> None:
        runtime = self._require_runtime()
        name = self._settings.agent_name
        local = runtime.clock.now_local().strftime("%a %d %b, %H:%M")
        banner = f"\n  {name} is online.  {local}  ({self._settings.environment})"
        if not self._settings.is_live:
            banner += "\n  dev environment - channels are stubbed, nothing will be sent."
        # Flushed: this is the signal the user looks for, and a hard kill must
        # not swallow it in a buffer.
        print(banner + "\n", flush=True)
        log.info("%s online in %s", name, self._settings.environment)

    def _report_downtime(self) -> None:
        """AD-26 / NFR-20: say what was missed instead of pretending nothing was."""
        runtime = self._require_runtime()
        previous = runtime.heartbeat.last_beat()
        if previous is None:
            return
        gap = utc_now() - previous
        if gap < DOWNTIME_WORTH_REPORTING:
            return
        window = describe(gap)
        print(
            f"  I was not running for {window} (since {previous.isoformat()})."
            "\n  Scheduled nudges only fire while this machine is on.\n",
            flush=True,
        )
        log.warning("downtime detected: %s", window)

    def _prepare_schedule(self) -> None:
        runtime = self._require_runtime()
        seeded = runtime.triggers.add_missing(default_routine())
        if seeded:
            print(f"  Set up your routine: {', '.join(seeded)}.\n", flush=True)
            log.info("seeded triggers: %s", seeded)

        now = utc_now()
        runtime.scheduler.prepare(now)
        for missed in runtime.scheduler.catch_up(now):
            log.info(
                "missed %s due %s (%s)",
                missed.key,
                missed.due_at.isoformat(),
                "re-raised" if missed.reraised else "discarded",
            )
        self._print_next_due()

    def _print_next_due(self) -> None:
        runtime = self._require_runtime()
        upcoming = sorted(
            (t for t in runtime.triggers.all() if t.enabled and t.next_due_at),
            key=lambda t: t.next_due_at,  # type: ignore[arg-type,return-value]
        )
        if not upcoming:
            return
        nxt = upcoming[0]
        when = nxt.next_due_at.astimezone(runtime.zone)  # type: ignore[union-attr]
        print(f"  Next up: {nxt.title} at {when.strftime('%H:%M on %a')}.\n", flush=True)

    # --- loop ------------------------------------------------------------

    def _serve(self) -> None:
        runtime = self._require_runtime()
        runtime.heartbeat.beat()
        log.info("scheduler running; ctrl-c to stop")
        while not self._stop.wait(TICK.total_seconds()):
            runtime.scheduler.tick(utc_now())
            runtime.heartbeat.beat()

    def _install_signal_handlers(self) -> None:
        def handle(signum: int, _frame: object) -> None:
            log.info("received signal %s, shutting down", signum)
            self._stop.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, handle)

    def _require_runtime(self) -> Runtime:
        if self._runtime is None:  # pragma: no cover - programmer error
            msg = "runtime not built"
            raise RuntimeError(msg)
        return self._runtime
