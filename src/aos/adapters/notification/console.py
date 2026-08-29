"""Delivery to the terminal.

Stands in until a real channel exists, and remains the dev-environment
adapter afterwards so a development run can never message anyone.
"""

from __future__ import annotations

import logging

from aos.ports.notification import NotificationRequest

log = logging.getLogger(__name__)


class ConsoleNotifier:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def submit(self, request: NotificationRequest) -> None:
        # A first pass at AD-23. The real budget, quiet hours and cross-producer
        # collapsing arrive with the notifier proper in story 1.5.
        if request.dedupe_key in self._seen:
            log.debug("suppressed duplicate %s", request.dedupe_key)
            return
        self._seen.add(request.dedupe_key)

        when = request.due_at.astimezone().strftime("%H:%M")
        suffix = "  (missed while I was off)" if request.late else ""
        print(f"\n  [{when}]  {request.title}{suffix}\n         {request.body}\n", flush=True)
        log.info("delivered %s", request.dedupe_key)
