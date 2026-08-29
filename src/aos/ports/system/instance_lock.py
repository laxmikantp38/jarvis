from types import TracebackType
from typing import Protocol, Self


class LockHeldError(RuntimeError):
    """Another live process already holds the lock."""


class InstanceLock(Protocol):
    """Guarantees one writer (AD-17).

    Two schedulers double-fire every trigger, and Telegram permits only one
    polling connection per token, so this is acquired before either starts.
    """

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @property
    def holder_pid(self) -> int | None:
        """PID of the process holding the lock, when one does."""
        ...
