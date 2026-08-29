"""FR-93: a secret that reaches a log has already leaked."""

from __future__ import annotations

import logging
from pathlib import Path

from aos.common.logging_setup import REDACTED, configure, register_secret


def test_registered_secrets_are_masked_in_the_json_log(tmp_path: Path) -> None:
    token = "super-secret-token-value"
    register_secret(token)
    configure(level="INFO", log_directory=tmp_path, json_file=True)

    logging.getLogger("test").info("connecting with %s", token)
    logging.shutdown()

    written = "\n".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.jsonl"))
    assert token not in written
    assert REDACTED in written


def test_trivially_short_values_are_not_registered() -> None:
    """Masking a two-character value would redact half the log."""
    register_secret("ab")
    from aos.common.logging_setup import _sensitive

    assert "ab" not in _sensitive
