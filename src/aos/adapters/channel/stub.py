"""The channel a development run gets.

It records what would have been sent and never touches the network, which is
what makes "dev cannot message anyone" a property of the wiring rather than a
flag someone has to remember.
"""

from __future__ import annotations

import logging

from aos.ports.channel import DeliveryResult, InboundMessage, MessageHandler, OutboundMessage

log = logging.getLogger(__name__)


class StubChannel:
    def __init__(self, name: str = "stub", *, echo: bool = True) -> None:
        self._name = name
        self._echo = echo
        self._handler: MessageHandler | None = None
        self.sent: list[OutboundMessage] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def reaches_a_real_person(self) -> bool:
        return False

    def send(self, message: OutboundMessage) -> DeliveryResult:
        self.sent.append(message)
        if self._echo:
            print(f"\n  [{self._name}]  {message.rendered()}\n", flush=True)
        log.info("stub delivery %s", message.dedupe_key)
        return DeliveryResult(channel=self._name, delivered=True)

    def start(self, on_message: MessageHandler) -> None:
        self._handler = on_message

    def stop(self) -> None:
        self._handler = None

    def deliver_inbound(self, message: InboundMessage) -> None:
        """Test and development seam: pretend a reply arrived."""
        if self._handler is not None:
            self._handler(message)
