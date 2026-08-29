"""`python -m aos.entrypoints.service`

Startup failure is surfaced to the user, not buried in a log file (FR-97).
"""

from __future__ import annotations

import sys

from aos.adapters.system.settings import load_settings
from aos.entrypoints.service.host import ServiceHost
from aos.ports.system.instance_lock import LockHeldError

EXIT_LOCK_HELD = 2
EXIT_STARTUP_FAILED = 3


def main() -> int:
    try:
        settings = load_settings()
    except Exception as exc:
        print(f"\n  Could not start: configuration is invalid.\n  {exc}\n", file=sys.stderr)
        return EXIT_STARTUP_FAILED

    try:
        return ServiceHost(settings).run()
    except LockHeldError as exc:
        print(f"\n  Not starting: {exc}\n", file=sys.stderr)
        return EXIT_LOCK_HELD
    except Exception as exc:
        print(f"\n  Startup failed: {exc}\n", file=sys.stderr)
        return EXIT_STARTUP_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
