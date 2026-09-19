"""Running the local interface alongside the service.

Uvicorn in a background thread, bound to loopback. The service loop stays the
main thread, because that is what the scheduler lives in.
"""

from __future__ import annotations

import contextlib
import logging
import threading

import uvicorn
from fastapi import FastAPI

log = logging.getLogger(__name__)

STARTUP_TIMEOUT = 15.0


class LocalInterface:
    def __init__(self, app: FastAPI, host: str, port: int) -> None:
        self._config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(self._config)
        self._thread: threading.Thread | None = None
        self._host = host
        self._port = port

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def start(self) -> bool:
        """Returns False when the port is already taken, rather than dying."""
        self._thread = threading.Thread(target=self._run, name="interface", daemon=True)
        self._thread.start()

        waited = 0.0
        while waited < STARTUP_TIMEOUT:
            if self._server.started:
                log.info("interface listening on %s", self.url)
                return True
            if not self._thread.is_alive():
                log.warning("interface failed to start on port %s", self._port)
                return False
            threading.Event().wait(0.1)
            waited += 0.1
        log.warning("interface did not start within %ss", STARTUP_TIMEOUT)
        return False

    def _run(self) -> None:
        with contextlib.suppress(SystemExit, OSError):
            self._server.run()

    def stop(self) -> None:
        self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
