#!/usr/bin/env python3
"""The only supported way to start this system (AD-19).

Idempotent: it works out what is missing, does just that, then starts. Running
it again on a healthy install skips straight to starting. Nothing here destroys
existing data.

    python run.py                     set up if needed, then run
    python run.py --setup-only        prepare everything, do not start
    python run.py --check             report what is and is not ready
    python run.py --env live          run against the live environment
    python run.py --set-secret NAME   store a credential in the OS keychain
    python run.py --register-startup  print the command to start on boot

Standard library only: this must run before any dependency exists.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PYPROJECT = ROOT / "pyproject.toml"
CONFIG = ROOT / "config.toml"
CONFIG_EXAMPLE = ROOT / "config.example.toml"
DEPS_MARKER = VENV / ".deps-hash"
MINIMUM_PYTHON = (3, 12)
TASK_NAME = "PersonalAgentOS"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def in_venv() -> bool:
    try:
        return Path(sys.executable).resolve() == venv_python().resolve()
    except OSError:
        return False


def say(message: str) -> None:
    print(f"  {message}")


def fail(message: str) -> None:
    print(f"\n  {message}\n", file=sys.stderr)
    raise SystemExit(1)


def check_python() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        have = ".".join(str(p) for p in sys.version_info[:3])
        want = ".".join(str(p) for p in MINIMUM_PYTHON)
        fail(f"Python {want} or newer is required; this is {have}.")


def ensure_venv() -> bool:
    """Returns True when it created one."""
    if venv_python().exists():
        return False
    say("creating the virtual environment ...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)  # noqa: S603
    return True


def _dependency_fingerprint() -> str:
    return hashlib.sha256(PYPROJECT.read_bytes()).hexdigest()


def dependencies_current() -> bool:
    if not DEPS_MARKER.exists():
        return False
    return DEPS_MARKER.read_text(encoding="utf-8").strip() == _dependency_fingerprint()


def _preferred_installer() -> list[str]:
    """uv when present, plain pip otherwise, so Python is the only prerequisite."""
    uv = shutil.which("uv")
    if uv:
        return [uv, "pip", "install", "--python", str(venv_python()), "-e", ".[dev]"]
    return [str(venv_python()), "-m", "pip", "install", "--quiet", "-e", ".[dev]"]


def ensure_dependencies() -> bool:
    if dependencies_current():
        return False
    say("installing dependencies (first run takes a minute) ...")
    subprocess.run(_preferred_installer(), check=True, cwd=ROOT)  # noqa: S603
    DEPS_MARKER.write_text(_dependency_fingerprint(), encoding="utf-8")
    return True


def ensure_config() -> bool:
    if CONFIG.exists():
        return False
    if not CONFIG_EXAMPLE.exists():
        fail("config.example.toml is missing; cannot scaffold configuration.")
    shutil.copyfile(CONFIG_EXAMPLE, CONFIG)
    say(f"created {CONFIG.name} from the example - review it when you get a moment")
    return True


def ensure_directories(environment: str) -> bool:
    made = False
    for directory in (ROOT / "data" / environment / "state", ROOT / "logs" / environment):
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            made = True
    return made


def ensure_migrations(environment: str) -> bool:
    """Bring the schema up to date. Forward-only, and safe on a live database.

    A failed migration leaves the previous version in place rather than a
    half-migrated system.
    """
    before = _schema_revision(environment)
    result = subprocess.run(  # noqa: S603
        [str(venv_python()), "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=dict(os.environ, AOS_ENVIRONMENT=environment),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "no detail reported"
        fail("Schema migration failed; nothing was changed." + chr(10) + "  " + detail)
    return _schema_revision(environment) != before


def _schema_revision(environment: str) -> str | None:
    import sqlite3

    database = ROOT / "data" / environment / "aos.db"
    if not database.exists():
        return None
    try:
        with sqlite3.connect(database) as connection:
            row = connection.execute("select version_num from alembic_version").fetchone()
    except sqlite3.Error:
        return None
    return str(row[0]) if row else None


def setup(environment: str) -> None:
    check_python()
    steps = [
        ensure_venv(),
        ensure_dependencies(),
        ensure_config(),
        ensure_directories(environment),
        ensure_migrations(environment),
    ]
    if any(steps):
        say("setup complete")


def report(environment: str) -> int:
    checks = [
        ("python >= 3.12", sys.version_info >= MINIMUM_PYTHON),
        ("virtual environment", venv_python().exists()),
        ("dependencies installed", dependencies_current()),
        ("config.toml present", CONFIG.exists()),
        ("data directory", (ROOT / "data" / environment).exists()),
        ("schema migrated", _schema_revision(environment) is not None),
    ]
    print()
    for label, ok in checks:
        print(f"  {'ok     ' if ok else 'MISSING'}  {label}")
    print()
    return 0 if all(ok for _, ok in checks) else 1


def _startup_command() -> str:
    quote = chr(34)
    escaped = chr(92) + quote
    target = escaped + str(venv_python()) + escaped
    script = escaped + str(ROOT / "run.py") + escaped
    user = os.environ.get("USERNAME", "%USERNAME%")
    return (
        f"schtasks /Create /TN {quote}{TASK_NAME}{quote} /SC ONSTART /RL HIGHEST /F "
        f"/TR {quote}{target} {script} --env live{quote} "
        f"/RU {quote}{user}{quote} /RP *"
    )


def register_startup() -> int:
    """Windows Task Scheduler, not NSSM: NSSM has had no stable release in over a decade."""
    if os.name != "nt":
        fail("Startup registration is Windows-only for now.")
    print()
    say("Run this once, in an ELEVATED terminal:")
    print()
    print(f"    {_startup_command()}")
    print()
    say("It prompts for your Windows password. That is what lets the task run when")
    say("nobody is logged in, which is what makes the 06:00 nudge fire after an")
    say("overnight reboot. Windows stores it, this project never sees it.")
    print()
    say("Prefer not to store it? Use /SC ONLOGON and drop /RU and /RP. The trade is")
    say("that nudges only fire once you have logged in.")
    print()
    return 0


def start(environment: str, module: str, extra: list[str]) -> int:
    if in_venv():
        from importlib import import_module

        sys.argv = [module, *extra]
        entry = import_module(f"{module}.__main__")
        return int(entry.main() or 0)
    env = dict(os.environ, AOS_ENVIRONMENT=environment)
    result = subprocess.run(  # noqa: S603
        [str(venv_python()), "-m", module, *extra], cwd=ROOT, env=env, check=False
    )
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the personal agent.")
    parser.add_argument("--env", choices=["dev", "live"], help="which environment to run")
    parser.add_argument("--setup-only", action="store_true", help="prepare, do not start")
    parser.add_argument("--check", action="store_true", help="report readiness and exit")
    parser.add_argument("--set-secret", metavar="NAME", help="store a credential")
    parser.add_argument("--forget-secret", metavar="NAME", help="revoke a credential")
    parser.add_argument("--show-config", action="store_true", help="print effective settings")
    parser.add_argument(
        "--register-startup",
        action="store_true",
        help="print the command that makes this start on boot",
    )
    return parser


CLI = "aos.entrypoints.cli"
SERVICE = "aos.entrypoints.service"


def main() -> int:
    args = build_parser().parse_args()
    environment = args.env or os.environ.get("AOS_ENVIRONMENT") or "dev"

    if args.register_startup:
        return register_startup()
    if args.check:
        return report(environment)

    setup(environment)

    if args.setup_only:
        say("ready. Start it with: python run.py")
        return 0
    if args.set_secret:
        return start(environment, CLI, ["set-secret", args.set_secret])
    if args.forget_secret:
        return start(environment, CLI, ["forget-secret", args.forget_secret])
    if args.show_config:
        return start(environment, CLI, ["config"])
    return start(environment, SERVICE, [])


if __name__ == "__main__":
    raise SystemExit(main())
