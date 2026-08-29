"""One writer, enforced by an exclusively-created lock file (AD-17).

Two schedulers would double-fire every trigger, and Telegram permits only one
polling connection per bot token, so this is acquired before either starts.

A lock left behind by a process that died is detected and taken over; a lock
held by a live process is refused with a diagnostic naming the holder.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from types import TracebackType
from typing import Self

from aos.ports.system.instance_lock import LockHeldError

log = logging.getLogger(__name__)


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return False
    return True


class FileInstanceLock:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._acquired = False

    @property
    def holder_pid(self) -> int | None:
        try:
            return int(self._path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    def __enter__(self) -> Self:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._create()
        except FileExistsError:
            self._break_stale_or_fail()
            self._create()
        self._acquired = True
        return self

    def _create(self) -> None:
        handle = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write(str(os.getpid()))

    def _break_stale_or_fail(self) -> None:
        pid = self.holder_pid
        if pid is not None and _process_alive(pid):
            msg = (
                f"another instance is already running (pid {pid}). "
                f"Stop it before starting a second, or delete {self._path} if you are "
                f"certain it is gone."
            )
            raise LockHeldError(msg)
        log.warning("clearing a stale lock left by pid %s", pid)
        with contextlib.suppress(OSError):
            self._path.unlink()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self._acquired:
            return
        with contextlib.suppress(OSError):
            self._path.unlink()
        self._acquired = False
