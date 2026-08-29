from __future__ import annotations

import contextlib
from datetime import datetime
from pathlib import Path

from aos.common.timeutil import isoformat_utc, utc_now


class FileHeartbeat:
    def __init__(self, path: Path) -> None:
        self._path = path

    def beat(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(isoformat_utc(utc_now()), encoding="utf-8")

    def last_beat(self) -> datetime | None:
        with contextlib.suppress(OSError, ValueError):
            raw = self._path.read_text(encoding="utf-8").strip()
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return None
