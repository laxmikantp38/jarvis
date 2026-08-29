from typing import Protocol


class SecretStore(Protocol):
    """Credential storage. Never a config file, never a log (AD-9, FR-93)."""

    def get(self, name: str) -> str | None: ...

    def set(self, name: str, value: str) -> None: ...

    def delete(self, name: str) -> None:
        """Revocation. Deleting an absent secret is not an error."""
        ...
