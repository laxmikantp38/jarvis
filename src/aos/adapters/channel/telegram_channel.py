"""Telegram, bridged into a synchronous host.

python-telegram-bot is asyncio-only, so it gets one background thread with its
own event loop. Everything crossing that boundary does so through two narrow
calls, which keeps the rest of the system free of async colouring.

Long polling means the connection is outbound: no port is opened, no router is
configured, and nothing about this works differently behind home NAT (AD-5).
Telegram permits one polling connection per token, which the single-instance
lock already guarantees (AD-17).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import threading
from typing import TYPE_CHECKING, Any

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, ApplicationBuilder, ContextTypes, MessageHandler, filters

from aos.common.timeutil import utc_now
from aos.ports.channel import DeliveryResult, InboundMessage, OutboundMessage
from aos.ports.channel import MessageHandler as InboundHandler

if TYPE_CHECKING:
    from collections.abc import Coroutine

log = logging.getLogger(__name__)

NAME = "telegram"
STARTUP_TIMEOUT = 30.0
SEND_TIMEOUT = 20.0


class TelegramChannel:
    def __init__(self, token: str, chat_id: str) -> None:
        self._token = token
        self._chat_id = chat_id
        self._loop: asyncio.AbstractEventLoop | None = None
        self._application: Application[Any, Any, Any, Any, Any, Any] | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._failure: BaseException | None = None
        self._handler: InboundHandler | None = None

    @property
    def name(self) -> str:
        return NAME

    @property
    def reaches_a_real_person(self) -> bool:
        return True

    # --- lifecycle -------------------------------------------------------

    def start(self, on_message: InboundHandler) -> None:
        self._handler = on_message
        self._thread = threading.Thread(target=self._run_loop, name="telegram", daemon=True)
        self._thread.start()
        if not self._ready.wait(STARTUP_TIMEOUT):
            msg = "Telegram did not finish starting within 30s"
            raise TimeoutError(msg)
        if self._failure is not None:
            raise self._failure
        log.info("telegram connected by long polling")

    def stop(self) -> None:
        if self._loop is None or self._thread is None:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=10)
        log.info("telegram stopped")

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._start_polling())
            self._ready.set()
            loop.run_forever()
        except BaseException as exc:
            self._failure = exc
            self._ready.set()
        finally:
            with contextlib.suppress(Exception):
                loop.run_until_complete(self._shutdown())
            loop.close()

    async def _start_polling(self) -> None:
        application = ApplicationBuilder().token(self._token).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_update))
        await application.initialize()
        await application.start()
        if application.updater is not None:
            await application.updater.start_polling(drop_pending_updates=False)
        self._application = application

    async def _shutdown(self) -> None:
        application = self._application
        if application is None:
            return
        if application.updater is not None:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()

    # --- inbound ---------------------------------------------------------

    async def _on_update(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if message is None or message.text is None or self._handler is None:
            return
        inbound = InboundMessage(
            channel=NAME,
            external_id=str(message.message_id),
            sender=str(message.chat_id),
            text=message.text,
            received_at=utc_now(),
        )
        # Hand back to the synchronous world; intake owns what happens next.
        await asyncio.get_running_loop().run_in_executor(None, self._handler, inbound)

    # --- outbound --------------------------------------------------------

    def send(self, message: OutboundMessage) -> DeliveryResult:
        application = self._application
        if self._loop is None or application is None:
            return DeliveryResult(NAME, delivered=False, detail="not started")
        try:
            self._await(
                application.bot.send_message(chat_id=self._chat_id, text=message.rendered())
            )
        except (TelegramError, TimeoutError, RuntimeError) as exc:
            log.warning("telegram delivery failed: %s", exc)
            return DeliveryResult(NAME, delivered=False, detail=str(exc))
        return DeliveryResult(NAME, delivered=True)

    def _await(self, coroutine: Coroutine[Any, Any, Any]) -> Any:
        assert self._loop is not None  # noqa: S101 - guarded by the caller
        return asyncio.run_coroutine_threadsafe(coroutine, self._loop).result(SEND_TIMEOUT)
