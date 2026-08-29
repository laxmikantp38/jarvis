from __future__ import annotations

import pytest
from pydantic import ValidationError

from aos.adapters.system.settings import Settings
from aos.common import paths


def test_environment_defaults_to_dev() -> None:
    """A run that has not chosen must never be the one that can message people."""
    assert Settings(_env_file=None).environment == "dev"


def test_server_must_bind_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """AD-5: the local host never accepts an inbound connection."""
    monkeypatch.setenv("AOS_SERVER__HOST", "0.0.0.0")  # noqa: S104
    with pytest.raises(ValidationError, match="loopback"):
        Settings()


def test_unknown_timezone_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AOS_TIMEZONE", "Mars/Olympus")
    with pytest.raises(ValidationError):
        Settings()


def test_environment_variables_override_the_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AOS_ENVIRONMENT", "live")
    assert Settings().is_live is True


def test_dev_and_live_never_share_a_database() -> None:
    assert paths.database_file("dev") != paths.database_file("live")
