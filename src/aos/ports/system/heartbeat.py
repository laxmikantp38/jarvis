from datetime import datetime
from typing import Protocol


class Heartbeat(Protocol):
    """AD-26: the system watches itself.

    Silent death is the realistic failure mode for an always-on local service,
    and it defeats the product's entire purpose, so a gap is detected and
    reported rather than discovered weeks later.
    """

    def beat(self) -> None: ...

    def last_beat(self) -> datetime | None:
        """When the previous run last reported alive, if it ever did."""
        ...
