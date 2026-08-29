from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo


class Clock(Protocol):
    """Time, injected rather than read from the global process clock.

    Scheduling correctness is testable only when time is a dependency.
    """

    def now_utc(self) -> datetime:
        """Current instant, always timezone-aware and always UTC (AD-16)."""
        ...

    def now_local(self) -> datetime:
        """Current instant in the configured local zone, for schedule evaluation."""
        ...

    @property
    def zone(self) -> ZoneInfo: ...
