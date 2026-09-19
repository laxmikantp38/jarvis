"""The composition root decides what a run can reach.

Dev safety is a property of the wiring, not a flag someone has to remember.
"""

from __future__ import annotations

import pytest

from aos.adapters.system.settings import Settings
from aos.entrypoints.service.wiring import _channels_for


def settings_for(environment: str, **telegram: object) -> Settings:
    payload: dict[str, object] = {"environment": environment, "timezone": "Asia/Kolkata"}
    if telegram:
        payload["telegram"] = telegram
    return Settings(**payload)  # type: ignore[arg-type]


def test_a_dev_run_cannot_reach_a_real_person() -> None:
    channels = _channels_for(settings_for("dev", enabled=True, chat_id="12345"))

    assert [c.name for c in channels] == ["console"]
    assert not any(c.reaches_a_real_person for c in channels), (
        "even fully configured, dev must not be able to send"
    )


def test_live_without_a_chat_id_stays_on_the_console() -> None:
    channels = _channels_for(settings_for("live", enabled=True, chat_id=""))

    assert [c.name for c in channels] == ["console"]


def test_live_without_a_stored_token_stays_on_the_console(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aos.adapters.system import keyring_secrets

    monkeypatch.setattr(keyring_secrets.KeyringSecretStore, "get", lambda self, name: None)
    channels = _channels_for(settings_for("live", enabled=True, chat_id="12345"))

    assert [c.name for c in channels] == ["console"]


def test_live_with_a_token_puts_telegram_first_and_keeps_a_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aos.adapters.system import keyring_secrets

    monkeypatch.setattr(keyring_secrets.KeyringSecretStore, "get", lambda self, name: "a-token")
    channels = _channels_for(settings_for("live", enabled=True, chat_id="12345"))

    assert [c.name for c in channels] == ["telegram", "console"]
    assert channels[0].reaches_a_real_person is True
    assert channels[-1].reaches_a_real_person is False, "the last resort always works"


def test_enabled_without_a_chat_id_is_not_usable() -> None:
    """Intent and capability are different things."""
    assert settings_for("live", enabled=True, chat_id="").telegram.usable is False
    assert settings_for("live", enabled=True, chat_id="1").telegram.usable is True
