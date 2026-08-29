from typing import Protocol

from aos.domain.scheduling.trigger import Trigger


class TriggerRepository(Protocol):
    """Schedule state lives on disk, so a trigger survives a restart and is not
    reconstructed from code on every boot (FR-25)."""

    def all(self) -> list[Trigger]: ...

    def get(self, key: str) -> Trigger | None: ...

    def save(self, trigger: Trigger) -> None:
        """Insert or update by key."""
        ...

    def add_missing(self, triggers: list[Trigger]) -> list[str]:
        """Insert only those whose key is absent. Returns the keys inserted.

        Seeding must never overwrite a trigger the user has edited or disabled.
        """
        ...
