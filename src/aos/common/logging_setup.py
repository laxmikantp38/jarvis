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
_OURS = "_aos_handler"
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
        if isinstance(record.msg, str):
            record.msg = _mask(record.msg)
        # Only strings are masked. Coercing every argument would break any
        # numeric format such as %d, which is a silent way to lose a log line.
        if isinstance(record.args, dict):
            record.args = {
                key: _mask(value) if isinstance(value, str) else value
                for key, value in record.args.items()
            }
        elif record.args:
            record.args = tuple(_mask(arg) if isinstance(arg, str) else arg for arg in record.args)
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
    # Remove only what we installed. Tearing out every root handler would take
    # a host application's logging with it - and pytest's caplog handler too.
    for existing in list(root.handlers):
        if getattr(existing, _OURS, False):
            root.removeHandler(existing)

    console = logging.StreamHandler()
    setattr(console, _OURS, True)
    console.setFormatter(_ConsoleFormatter())
    console.addFilter(_RedactionFilter())
    root.addHandler(console)

    if log_directory is not None and json_file:
        log_directory.mkdir(parents=True, exist_ok=True)
        stamp = utc_now().strftime("%Y-%m-%d")
        handler = logging.FileHandler(log_directory / f"{stamp}.jsonl", encoding="utf-8")
        setattr(handler, _OURS, True)
        handler.setFormatter(_JsonFormatter())
        handler.addFilter(_RedactionFilter())
        root.addHandler(handler)
