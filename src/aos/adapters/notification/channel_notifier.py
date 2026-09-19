"""Delivery across channels, with a fallback and an honest record.

The scheduler hands over a request and stops caring; classification, ordering
and failure handling live here (AD-11). Duplicates collapse on the dedupe key
so two producers raising the same real event reach the user once (AD-23).
"""

from __future__ import annotations

import logging

from aos.ports.channel import Channel, OutboundMessage
from aos.ports.notification import NotificationRequest

log = logging.getLogger(__name__)


class ChannelNotifier:
    def __init__(self, channels: list[Channel]) -> None:
        if not channels:
            msg = "a notifier with no channel would deliver nothing, silently"
            raise ValueError(msg)
        self._channels = channels
        self._delivered: set[str] = set()

    def submit(self, request: NotificationRequest) -> None:
        if request.dedupe_key in self._delivered:
            log.debug("suppressed duplicate %s", request.dedupe_key)
            return

        message = OutboundMessage(
            dedupe_key=request.dedupe_key,
            title=request.title,
            body=request.body,
            notification_class=request.notification_class,
            late=request.late,
        )

        for channel in self._channels:
            result = channel.send(message)
            if result.delivered:
                self._delivered.add(request.dedupe_key)
                log.info("delivered %s via %s", request.dedupe_key, result.channel)
                return
            # Recorded, not swallowed: a silent failure is indistinguishable
            # from nothing having been due.
            log.warning(
                "delivery failed on %s for %s: %s",
                result.channel,
                request.dedupe_key,
                result.detail,
            )

        log.error("every channel failed for %s", request.dedupe_key)
