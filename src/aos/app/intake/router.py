"""Where every inbound message lands, whatever channel carried it.

One path in, so a capability added here works from Telegram, WhatsApp and the
phone relay without being wired three times (AD-6). Real command handling
grows here; today it answers the two questions worth answering and is honest
about the rest.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from aos.app.intake.money_commands import MoneyCommands
from aos.app.work.capture import TaskCapture
from aos.domain.content.footage import FootageReserve, assess
from aos.ports.channel import InboundMessage
from aos.ports.persistence.content import FootageRepository
from aos.ports.persistence.triggers import TriggerRepository
from aos.ports.persistence.work import ProjectRepository, TaskRepository

log = logging.getLogger(__name__)

Reply = Callable[[str], None]
Matcher = Callable[[str], bool]
Responder = Callable[[str], str]


def _exactly(*words: str) -> Matcher:
    options = set(words)
    return lambda text: text in options


def _starting(*prefixes: str) -> Matcher:
    """A verb followed by something, so "task" alone does not match "tasks"."""
    return lambda text: any(text == prefix or text.startswith(prefix + " ") for prefix in prefixes)


def _after(verb: str, raw: str) -> str:
    return raw[len(verb) :].strip()


@dataclass(frozen=True, slots=True)
class Intake:
    triggers: TriggerRepository
    footage: FootageRepository
    projects: ProjectRepository
    tasks: TaskRepository
    capture: TaskCapture
    money: MoneyCommands
    zone: ZoneInfo
    agent_name: str
    horizon_days: int
    now: Callable[[], datetime]

    def handle(self, message: InboundMessage, reply: Reply) -> None:
        """Dispatch, not a ladder.

        An if/elif chain grows a branch per capability and eventually becomes
        the thing nobody wants to touch. A table adds a row instead.
        """
        raw = message.text.strip()
        text = raw.lower()
        log.info("inbound from %s: %s", message.channel, text[:80])

        for matches, respond in self._commands():
            if matches(text):
                reply(respond(raw))
                return

        # Saying so beats inventing an answer.
        reply("I don't understand that yet. Try 'help' to see what I can do.")

    def _commands(self) -> list[tuple[Matcher, Responder]]:
        """Order matters only where prefixes could overlap."""
        return [
            (_exactly("next", "what's next", "whats next"), lambda _: self._next_up()),
            (_exactly("status", "how are you"), lambda _: self._status()),
            (_starting("earned", "earn", "received", "got paid"), self.money.earned),
            (_starting("spent", "paid", "bought"), self.money.spent),
            (_exactly("money", "net", "position"), lambda _: self.money.position()),
            (_exactly("goal", "goals", "target", "trajectory"), lambda _: self.money.standing()),
            (_starting("task"), lambda raw: self._capture(_after("task", raw))),
            (_exactly("tasks", "todo"), lambda _: self._tasks()),
            (_starting("done"), lambda raw: self._complete(_after("done", raw))),
            (_exactly("projects"), lambda _: self._projects()),
            (_starting("footage"), lambda raw: self._footage(raw.lower())),
            (_exactly("help", "?"), lambda _: self._help()),
        ]

    def _next_up(self) -> str:
        upcoming = sorted(
            (t for t in self.triggers.all() if t.enabled and t.next_due_at is not None),
            key=lambda t: t.next_due_at,  # type: ignore[arg-type,return-value]
        )
        if not upcoming:
            return "Nothing is scheduled."
        lines = []
        for trigger in upcoming[:3]:
            when = trigger.next_due_at.astimezone(self.zone)  # type: ignore[union-attr]
            lines.append(f"{when.strftime('%a %H:%M')}  {trigger.title}")
        return "Next up:\n" + "\n".join(lines)

    def _status(self) -> str:
        active = [t for t in self.triggers.all() if t.enabled]
        local = self.now().astimezone(self.zone).strftime("%a %d %b, %H:%M")
        return f"{self.agent_name} is running. {len(active)} triggers active. It is {local}."

    def _help(self) -> str:
        return (
            "I understand: next, status, goal, money, tasks, task <what>, "
            "done <n>, projects, footage, footage <n>, "
            "earned <amount> from <source>, spent <amount> on <what>, help."
        )

    def _capture(self, text: str) -> str:
        if not text.strip():
            return "Tell me what to capture: 'task fix the signup bug'."
        result = self.capture.capture(text)
        where = result.project.name if result.project else result.task.project_key
        hedge = " (guessed)" if result.guessed_project else ""
        return f"Noted against {where}{hedge}."

    def _tasks(self) -> str:
        open_tasks = self.tasks.open_tasks()
        if not open_tasks:
            return "Nothing open."
        by_project: dict[str, list[str]] = {}
        for index, task in enumerate(open_tasks, 1):
            by_project.setdefault(task.project_key, []).append(f"{index}. {task.title}")
        blocks = [f"{key}:" + chr(10) + chr(10).join(lines) for key, lines in by_project.items()]
        return (chr(10) + chr(10)).join(blocks)

    def _complete(self, reference: str) -> str:
        open_tasks = self.tasks.open_tasks()
        try:
            task = open_tasks[int(reference) - 1]
        except (ValueError, IndexError):
            return "Which one? Use the number from 'tasks'."
        self.tasks.save(task.completed(self.now()))
        return f"Done: {task.title}"

    def _projects(self) -> str:
        lines = [p.describe() for p in self.projects.all()]
        return chr(10).join(lines)

    def _footage(self, text: str) -> str:
        """`footage` reports; `footage 5` sets the reserve; `footage +3` adds."""
        argument = text.removeprefix("footage").strip()
        reserve = self.footage.get()

        if argument:
            try:
                reserve = self._applied(reserve, argument)
            except ValueError:
                return "Tell me a number: 'footage 5' to set it, or 'footage +3' to add."
            self.footage.save(reserve)

        shortfall = assess(reserve, self.now().astimezone(self.zone).date(), self.horizon_days)
        if shortfall is None:
            return f"{reserve.days_covered} days of footage. Nothing to worry about."
        return shortfall.describe()

    def _applied(self, reserve: FootageReserve, argument: str) -> FootageReserve:
        if argument.startswith("+"):
            return reserve.add(int(argument[1:]))
        if argument.startswith("-"):
            return reserve.spend(int(argument[1:]))
        return FootageReserve(
            clips_available=int(argument),
            clips_per_publish=reserve.clips_per_publish,
        )
