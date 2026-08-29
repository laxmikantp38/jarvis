from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aos.common.timeutil import utc_now


class SystemClock:
    """Real time. Tests substitute a fixed clock through the same port."""

    def __init__(self, zone: ZoneInfo) -> None:
        self._zone = zone

    def now_utc(self) -> datetime:
        return utc_now()

    def now_local(self) -> datetime:
        return utc_now().astimezone(self._zone)

    @property
    def zone(self) -> ZoneInfo:
        return self._zone
