"""Structured logging with redaction applied before anything is written.

A secret that reaches a log file has already leaked, so redaction happens in a
filter on the way out rather than at each call site where it could be forgotten.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aos.common.timeutil import isoformat_utc, utc_now

REDACTED = "[redacted]"
# Masking anything shorter would redact ordinary words out of every log line.
SHORTEST_MASKABLE_SECRET = 4

_sensitive: set[str] = set()


def register_secret(value: str | None) -> None:
    """Mark a value so it is masked wherever it appears in a log record."""
    if value and len(value) >= SHORTEST_MASKABLE_SECRET:
        _sensitive.add(value)


def _mask(text: str) -> str:
    for secret in _sensitive:
        text = text.replace(secret, REDACTED)
    return text


class _RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _mask(str(record.msg))
        if record.args:
            record.args = tuple(_mask(str(a)) for a in record.args)
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": isoformat_utc(utc_now()),
            "level": record.levelname,
            "logger": record.name,
            "message": _mask(record.getMessage()),
        }
        correlation = getattr(record, "correlation_id", None)
        if correlation:
            payload["correlation_id"] = correlation
        if record.exc_info:
            payload["exception"] = _mask(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


class _ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        stamp = utc_now().strftime("%H:%M:%S")
        return f"{stamp}  {record.levelname:<7} {_mask(record.getMessage())}"


def configure(level: str, log_directory: Path | None, json_file: bool) -> None:
    """Console for a human, JSON on disk for the machine."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    for existing in list(root.handlers):
        root.removeHandler(existing)

    console = logging.StreamHandler()
    console.setFormatter(_ConsoleFormatter())
    console.addFilter(_RedactionFilter())
    root.addHandler(console)

    if log_directory is not None and json_file:
        log_directory.mkdir(parents=True, exist_ok=True)
        stamp = utc_now().strftime("%Y-%m-%d")
        handler = logging.FileHandler(log_directory / f"{stamp}.jsonl", encoding="utf-8")
        handler.setFormatter(_JsonFormatter())
        handler.addFilter(_RedactionFilter())
        root.addHandler(handler)
