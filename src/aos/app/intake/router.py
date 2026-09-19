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

from aos.ports.channel import InboundMessage
from aos.ports.persistence.triggers import TriggerRepository

log = logging.getLogger(__name__)

Reply = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class Intake:
    triggers: TriggerRepository
    zone: ZoneInfo
    agent_name: str
    now: Callable[[], datetime]

    def handle(self, message: InboundMessage, reply: Reply) -> None:
        text = message.text.strip().lower()
        log.info("inbound from %s: %s", message.channel, text[:80])

        if text in {"next", "what's next", "whats next"}:
            reply(self._next_up())
        elif text in {"status", "how are you"}:
            reply(self._status())
        elif text in {"help", "?"}:
            reply(self._help())
        else:
            # Saying so beats inventing an answer.
            reply(
                "I don't understand that yet. I can answer 'next', 'status' or 'help'.\n"
                "Anything else has to wait until I learn to do it."
            )

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
        return "I understand: next, status, help."
