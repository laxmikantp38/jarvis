"""Where things live on disk.

Dev and live never share a database file, so a development run cannot
corrupt or read real data.
"""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Repository root, found by walking up to the directory holding pyproject.toml."""
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    # Installed rather than run from a checkout: fall back to the working directory.
    return Path.cwd()


def config_file() -> Path:
    return project_root() / "config.toml"


def config_example_file() -> Path:
    return project_root() / "config.example.toml"


def data_dir(environment: str) -> Path:
    return project_root() / "data" / environment


def database_file(environment: str) -> Path:
    return data_dir(environment) / "aos.db"


def log_dir(environment: str) -> Path:
    return project_root() / "logs" / environment


def lock_file(environment: str) -> Path:
    return data_dir(environment) / "instance.lock"


def state_dir(environment: str) -> Path:
    """Runtime state that is not the database — heartbeat, last-run markers."""
    return data_dir(environment) / "state"
