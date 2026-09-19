"""Small operator commands: credentials and configuration checks.

`python run.py --set-secret telegram_token` routes here.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from aos.adapters.system.keyring_secrets import KeyringSecretStore
from aos.adapters.system.settings import load_settings
from aos.app.maintenance.backup import BackupService
from aos.common import paths
from aos.common.timeutil import utc_now


def _set_secret(name: str) -> int:
    value = getpass.getpass(f"Value for {name} (input hidden): ").strip()
    if not value:
        print("  Nothing entered; no change made.", file=sys.stderr)
        return 1
    KeyringSecretStore().set(name, value)
    print(f"  Stored {name} in the OS credential store.")
    return 0


def _forget_secret(name: str) -> int:
    KeyringSecretStore().delete(name)
    print(f"  Revoked {name}.")
    return 0


def _backup_service() -> BackupService:
    settings = load_settings()
    return BackupService(
        database=paths.database_file(settings.environment),
        directory=paths.backup_dir(settings.environment),
        retain_days=30,
        now=utc_now,
    )


def _backup() -> int:
    service = _backup_service()
    result = service.create()
    pruned = service.prune()
    print(f"  Backed up to {result.path} ({result.bytes_written:,} bytes).")
    if pruned:
        print(f"  Removed {len(pruned)} expired backups.")
    return 0


def _restore_drill() -> int:
    """An untested backup is not a backup."""
    settings = load_settings()
    service = _backup_service()
    scratch = paths.data_dir(settings.environment) / "restore-drill.db"
    result = service.drill(scratch)
    print(f"  {result.describe()}")
    return 0 if result.passed else 1


def _show_config() -> int:
    settings = load_settings()
    print(f"  agent name   {settings.agent_name}")
    print(f"  environment  {settings.environment}")
    print(f"  timezone     {settings.timezone}")
    print(f"  server       http://{settings.server.host}:{settings.server.port}")
    print(f"  telegram     {'enabled' if settings.telegram.enabled else 'disabled'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aos", description="Operator commands.")
    sub = parser.add_subparsers(dest="command", required=True)

    setter = sub.add_parser("set-secret", help="store a credential")
    setter.add_argument("name")

    forgetter = sub.add_parser("forget-secret", help="revoke a credential")
    forgetter.add_argument("name")

    sub.add_parser("config", help="show effective configuration")
    sub.add_parser("backup", help="take a backup and prune expired ones")
    sub.add_parser("restore-drill", help="prove the latest backup restores")

    args = parser.parse_args(argv)
    if args.command == "set-secret":
        return _set_secret(args.name)
    if args.command == "forget-secret":
        return _forget_secret(args.name)
    if args.command == "backup":
        return _backup()
    if args.command == "restore-drill":
        return _restore_drill()
    return _show_config()


if __name__ == "__main__":
    raise SystemExit(main())
