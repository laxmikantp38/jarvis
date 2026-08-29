"""Credentials in the OS store — Windows DPAPI via keyring.

Nothing here ever writes a value to a file, a log or an event. Reads are
registered with the log redactor so a leak downstream is masked on the way out.
"""

from __future__ import annotations

import logging

import keyring
from keyring.errors import KeyringError

from aos.common.logging_setup import register_secret

log = logging.getLogger(__name__)

SERVICE = "aos"


class KeyringSecretStore:
    def __init__(self, service: str = SERVICE) -> None:
        self._service = service

    def get(self, name: str) -> str | None:
        try:
            value = keyring.get_password(self._service, name)
        except KeyringError:
            log.exception("credential store unavailable while reading %s", name)
            return None
        register_secret(value)
        return value

    def set(self, name: str, value: str) -> None:
        keyring.set_password(self._service, name, value)
        register_secret(value)
        log.info("stored credential %s", name)

    def delete(self, name: str) -> None:
        try:
            keyring.delete_password(self._service, name)
        except KeyringError:
            log.info("credential %s was not present", name)
            return
        log.info("revoked credential %s", name)
