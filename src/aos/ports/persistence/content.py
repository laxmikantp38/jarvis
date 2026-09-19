from typing import Protocol

from aos.domain.content.footage import FootageReserve


class FootageRepository(Protocol):
    def get(self) -> FootageReserve: ...

    def save(self, reserve: FootageReserve) -> None: ...


class DailyCheckLog(Protocol):
    """Remembers which daily checks have already run, so a restart at 11:00
    does not re-run the 10:00 check and nag a second time."""

    def last_run(self, name: str) -> str | None:
        """ISO date of the last run, in the user's local zone."""
        ...

    def mark_run(self, name: str, local_day: str) -> None: ...
