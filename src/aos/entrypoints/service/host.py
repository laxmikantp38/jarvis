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
from aos.app.finance.goals import seed_goals
from aos.app.scheduling.routine import default_routine
from aos.app.scheduling.scheduler import MissedOccurrence
from aos.app.work.projects import default_projects
from aos.common import paths
from aos.common.logging_setup import configure
from aos.common.timeutil import utc_now
from aos.domain.scheduling.trigger import NotificationClass
from aos.entrypoints.api.app import create_app
from aos.entrypoints.api.server import LocalInterface
from aos.entrypoints.service.wiring import Runtime, build
from aos.ports.channel import InboundMessage, OutboundMessage

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
        self._interface: LocalInterface | None = None
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
            self._start_channels()
            self._start_interface()
            try:
                self._serve()
            finally:
                self._stop_interface()
                self._stop_channels()
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
        new_projects = runtime.projects.add_missing(default_projects())
        if new_projects:
            print(f"  Tracking: {', '.join(new_projects)}." + chr(10), flush=True)
            log.info("seeded projects: %s", new_projects)

        self._seed_goals()

        seeded = runtime.triggers.add_missing(default_routine())
        if seeded:
            print(f"  Set up your routine: {', '.join(seeded)}.\n", flush=True)
            log.info("seeded triggers: %s", seeded)

        now = utc_now()
        runtime.scheduler.prepare(now)
        self._report_missed(runtime.scheduler.catch_up(now))
        self._print_next_due()

    def _report_missed(self, missed: list[MissedOccurrence]) -> None:
        """Say what came due while the machine was off, once and concisely.

        A list beats a pile of individual nudges at breakfast; the ones worth
        acting on have already been re-raised through the notifier.
        """
        if not missed:
            return
        runtime = self._require_runtime()
        reraised = [m for m in missed if m.reraised]
        let_go = [m for m in missed if not m.reraised]

        report = [f"  While I was off, {len(missed)} came due:"]
        for occurrence in sorted(missed, key=lambda m: m.due_at):
            when = occurrence.due_at.astimezone(runtime.zone).strftime("%a %H:%M")
            marker = "resent" if occurrence.reraised else "let go"
            report.append(f"    {when}  {occurrence.title}  ({marker})")
        newline = chr(10)
        print(newline.join(report) + newline, flush=True)

        log.info(
            "missed %d occurrences: %d re-raised, %d discarded",
            len(missed),
            len(reraised),
            len(let_go),
        )

    def _seed_goals(self) -> None:
        """Seed the tree once, then keep it in step with what has arrived."""
        runtime = self._require_runtime()
        goals = runtime.settings.goals
        new_goals = runtime.goals.add_missing(
            seed_goals(goals.target_money, goals.start_date, goals.deadline_date)
        )
        if new_goals:
            log.info("seeded goals: %s", new_goals)
        runtime.goal_engine.sync_root_target(goals.target_money)
        runtime.goal_engine.refresh_from_records()

        standing = runtime.goal_engine.standing()
        if standing is not None and standing.assessment.projects:
            goal = standing.goal
            print(
                f"  Goal:       {goal.describe_value(goal.current)} of "
                f"{goal.describe_value(goal.target_or_zero)} "
                f"- {standing.assessment.verdict.value}" + chr(10),
                flush=True,
            )

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

    def _start_channels(self) -> None:
        runtime = self._require_runtime()
        for channel in runtime.channels:
            channel.start(self._on_inbound)
        reachable = [c.name for c in runtime.channels if c.reaches_a_real_person]
        if reachable:
            names = ", ".join(reachable)
            print(f"  Listening on {names}." + chr(10), flush=True)
            log.info("channels listening: %s", reachable)

    def _start_interface(self) -> None:
        runtime = self._require_runtime()
        server = runtime.settings.server
        self._interface = LocalInterface(create_app(runtime), host=server.host, port=server.port)
        if self._interface.start():
            print(f"  Interface:  {self._interface.url}" + chr(10), flush=True)
        else:
            # Said out loud rather than logged: a dead interface with a live
            # service looks like the whole thing is broken.
            print(
                f"  Interface could not start on port {server.port} - something else"
                f" is using it. Everything else is running." + chr(10),
                flush=True,
            )

    def _stop_interface(self) -> None:
        if self._interface is not None:
            self._interface.stop()

    def _stop_channels(self) -> None:
        runtime = self._require_runtime()
        for channel in runtime.channels:
            channel.stop()

    def _on_inbound(self, message: InboundMessage) -> None:
        """Every channel converges here; none gets a private route in (AD-6)."""
        runtime = self._require_runtime()
        origin = next((c for c in runtime.channels if c.name == message.channel), None)

        def reply(text: str) -> None:
            if origin is None:
                log.warning("no channel named %s to reply on", message.channel)
                return
            origin.send(
                OutboundMessage(
                    dedupe_key=f"reply:{message.channel}:{message.external_id}",
                    title="",
                    body=text,
                    notification_class=NotificationClass.NORMAL,
                )
            )

        try:
            runtime.intake.handle(message, reply)
        except Exception:
            log.exception("intake failed for %s", message.external_id)
            reply("Something went wrong handling that. It is in the log.")

    # --- loop ------------------------------------------------------------

    def _serve(self) -> None:
        runtime = self._require_runtime()
        log.info("scheduler running; ctrl-c to stop")
        # Work first, then wait. Otherwise a check that is already due sits idle
        # for a full tick after every start.
        self._work(runtime)
        while not self._stop.wait(TICK.total_seconds()):
            self._work(runtime)

    def _work(self, runtime: Runtime) -> None:
        now = utc_now()
        runtime.scheduler.tick(now)
        runtime.footage_watch.run_if_due(now)
        runtime.notifier.release_due()
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
