"""The local interface.

Bound to loopback and nowhere else (AD-5). Every section exists so the
navigation does not lie about what the system has; the ones with no data yet
say so plainly rather than rendering a zero (NFR-18).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from aos.common.timeutil import utc_now
from aos.entrypoints.api.render import Chrome, empty, instrument, kv, page, table

if TYPE_CHECKING:
    from aos.entrypoints.service.wiring import Runtime

NOT_BUILT_YET = "Nothing here yet"


def create_app(runtime: Runtime) -> FastAPI:
    app = FastAPI(title="Personal agent", docs_url=None, redoc_url=None)

    def chrome() -> Chrome:
        return Chrome(
            agent_name=runtime.settings.agent_name,
            environment=runtime.settings.environment,
            counts={
                "tasks": len(runtime.tasks.open_tasks()),
                "projects": len(runtime.projects.all()),
            },
        )

    def local(moment: datetime) -> str:
        return moment.astimezone(runtime.zone).strftime("%a %H:%M")

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        # Pair the due instant with its trigger so the type stays honest: the
        # filter guarantees it is set, but the field is optional.
        upcoming = sorted(
            (
                (trigger.next_due_at, trigger)
                for trigger in runtime.triggers.all()
                if trigger.enabled and trigger.next_due_at is not None
            ),
            key=lambda pair: pair[0],
        )
        open_tasks = runtime.tasks.open_tasks()
        reserve = runtime.footage.get()
        tally = runtime.notifier.tally

        next_up = (
            instrument(
                "Next up",
                f'<div class="big">{local(upcoming[0][0])}</div>'
                f'<p class="sub" style="margin:6px 0 0">{upcoming[0][1].title}</p>',
                stripe="ok",
            )
            if upcoming
            else instrument("Next up", empty("Nothing scheduled", "No triggers are enabled."))
        )

        footage_state = "crit" if reserve.days_covered == 0 else "ok"
        return page(
            chrome(),
            "/",
            "Dashboard",
            f"{runtime.settings.agent_name} is running. Everything on this page is local.",
            '<div class="grid">'
            + next_up
            + instrument(
                "Open work",
                f'<div class="big">{len(open_tasks)}</div>'
                + "".join(
                    kv(
                        project.name,
                        str(sum(1 for t in open_tasks if t.project_key == project.key)),
                    )
                    for project in runtime.projects.all()
                    if any(t.project_key == project.key for t in open_tasks)
                ),
                stripe="idle",
            )
            + instrument(
                "Footage",
                f'<div class="big">{reserve.days_covered}</div>'
                '<p class="sub" style="margin:6px 0 0">days of uploads covered</p>',
                stripe=footage_state,
                pill="none left" if reserve.days_covered == 0 else "",
            )
            + instrument(
                "Today's attention",
                kv("delivered", str(tally.delivered))
                + kv("held", str(tally.deferred))
                + kv("folded into a briefing", str(tally.batched))
                + kv("duplicates suppressed", str(tally.suppressed_duplicate)),
                stripe="idle",
            )
            + "</div>",
        )

    @app.get("/tasks", response_class=HTMLResponse)
    def tasks() -> str:
        open_tasks = runtime.tasks.open_tasks()
        body = (
            table(
                ["Task", "Project", "Needs", "Captured"],
                [
                    [t.title, t.project_key, t.attention.value, local(t.created_at)]
                    for t in open_tasks
                ],
            )
            if open_tasks
            else empty(
                "Nothing open",
                "Send a message to capture something: ",
                "task railzy: fix the signup handler",
            )
        )
        return page(chrome(), "/tasks", "Tasks", "Everything open, oldest first.", body)

    @app.get("/projects", response_class=HTMLResponse)
    def projects() -> str:
        rows = [
            [p.name, p.objective, "active" if p.exists_yet else "not formed yet"]
            for p in runtime.projects.all()
        ]
        return page(
            chrome(),
            "/projects",
            "Projects",
            "The ventures competing for the same evenings.",
            table(["Project", "Objective", "Status"], rows),
        )

    @app.get("/schedule", response_class=HTMLResponse)
    def schedule() -> str:
        rows = [
            [
                t.title,
                t.recurrence.describe(),
                t.notification_class.value,
                local(t.next_due_at) if t.next_due_at else "-",
                "on" if t.enabled else "off",
            ]
            for t in sorted(runtime.triggers.all(), key=lambda t: t.recurrence.at)
        ]
        return page(
            chrome(),
            "/schedule",
            "Schedule",
            "Your routine, held as data. Each one is editable and can be turned off.",
            table(["Trigger", "When", "Class", "Next", "State"], rows),
        )

    @app.get("/audit", response_class=HTMLResponse)
    def audit() -> str:
        events = runtime.events.recent(100)
        body = (
            table(
                ["When", "What", "Project", "Detail"],
                [
                    [
                        local(e.occurred_at),
                        e.type.value,
                        e.project_key or "-",
                        ", ".join(f"{k}={v}" for k, v in e.payload.items()),
                    ]
                    for e in events
                ],
            )
            if events
            else empty("No events yet", "Everything the system does will be recorded here.")
        )
        return page(
            chrome(),
            "/audit",
            "Audit",
            "Append-only. The database itself rejects an update or a delete.",
            body,
        )

    @app.get("/memory", response_class=HTMLResponse)
    def memory() -> str:
        facts = runtime.facts.all()
        body = (
            table(["Fact", "Value"], [[k, v] for k, v in facts.items()])
            if facts
            else empty(
                "Nothing remembered yet",
                "Stable facts about you will collect here as the system learns them.",
            )
        )
        return page(chrome(), "/memory", "Memory", "Six separated stores, not one pile.", body)

    @app.get("/notifications", response_class=HTMLResponse)
    def notifications() -> str:
        tally = runtime.notifier.tally
        policy = runtime.settings.notifications
        return page(
            chrome(),
            "/notifications",
            "Notifications",
            "Attention is the scarcest thing this spends.",
            '<div class="grid">'
            + instrument(
                "Today",
                kv("delivered", str(tally.delivered))
                + kv("held for a quiet window", str(tally.deferred))
                + kv("folded into a briefing", str(tally.batched))
                + kv("duplicates suppressed", str(tally.suppressed_duplicate))
                + kv("failed", str(tally.failed)),
            )
            + instrument(
                "Policy",
                kv("daily budget", str(policy.daily_budget))
                + kv("quiet hours", policy.quiet_hours or "none")
                + kv("blackouts", ", ".join(policy.blackouts) or "none")
                + kv("still held", str(runtime.notifier.pending)),
            )
            + "</div>",
        )

    @app.get("/integrations", response_class=HTMLResponse)
    def integrations() -> str:
        rows = [
            [
                channel.name,
                "reaches you" if channel.reaches_a_real_person else "local only",
                "primary" if index == 0 else "fallback",
            ]
            for index, channel in enumerate(runtime.channels)
        ]
        return page(
            chrome(),
            "/integrations",
            "Integrations",
            "Channels are tried in order; the last one always works.",
            table(["Channel", "Reach", "Order"], rows),
        )

    @app.get("/settings", response_class=HTMLResponse)
    def settings() -> str:
        current = runtime.settings
        return page(
            chrome(),
            "/settings",
            "Settings",
            "Edit config.toml and restart. Nothing here is stored in code.",
            instrument(
                "Effective configuration",
                kv("name", current.agent_name)
                + kv("environment", current.environment)
                + kv("timezone", current.timezone)
                + kv("interface", f"http://{current.server.host}:{current.server.port}")
                + kv("footage check", current.content.check_at)
                + kv("now", local(utc_now())),
            ),
        )

    _register_placeholders(app, chrome)
    return app


def _register_placeholders(app: FastAPI, chrome: Callable[[], Chrome]) -> None:
    """Sections whose feature has not been built yet.

    They exist so the navigation does not lie, and each says which story brings
    it to life rather than showing an empty chart.
    """
    pending = {
        "/agent": ("Agent", "Who is working, and what needs your approval.", "epic 5"),
        "/goals": ("Goals", "Targets, required pace, trajectory and the gap.", "epic 3"),
        "/revenue": ("Revenue", "Earnings, expenses and net position.", "epic 3"),
        "/decisions": ("Decisions", "What was chosen, why, and whether it still holds.", "epic 7"),
        "/experiments": ("Experiments", "Hypotheses that reach a conclusion.", "epic 7"),
    }

    for path, (title, subtitle, when) in pending.items():

        def make(
            path: str = path,
            title: str = title,
            subtitle: str = subtitle,
            when: str = when,
        ) -> None:
            @app.get(path, response_class=HTMLResponse)
            def view() -> str:
                return page(
                    chrome(),
                    path,
                    title,
                    subtitle,
                    empty(NOT_BUILT_YET, f"This arrives with {when}."),
                )

        make()
