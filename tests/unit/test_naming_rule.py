"""AD-9: the assistant's name is configuration, never source.

Renaming must be a single config change. This test is the enforcement; CI runs
it on every commit.

The forbidden term is read from configuration rather than written here, so this
file contains no literal to trip over, and the check follows a rename by itself.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCANNED_ROOTS = ("src", "tests", "relay", "migrations")


def configured_name() -> str:
    example = ROOT / "config.example.toml"
    return str(tomllib.loads(example.read_text(encoding="utf-8"))["agent_name"])


def _source_files() -> list[Path]:
    files: list[Path] = []
    for folder in SCANNED_ROOTS:
        base = ROOT / folder
        if base.is_dir():
            files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    entrypoint = ROOT / "run.py"
    if entrypoint.exists():
        files.append(entrypoint)
    return files


def test_the_name_is_defined_in_configuration() -> None:
    assert configured_name(), "config.example.toml must define agent_name"


def test_no_source_file_mentions_the_assistant_name() -> None:
    pattern = re.compile(re.escape(configured_name()), re.IGNORECASE)
    offenders = [
        f"{path.relative_to(ROOT)}:{number}: {line.strip()}"
        for path in _source_files()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if pattern.search(line)
    ]
    assert not offenders, "the name must live only in configuration:\n" + "\n".join(offenders)


def test_renaming_needs_only_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    from aos.adapters.system.settings import Settings

    monkeypatch.setenv("AOS_AGENT_NAME", "Friday")
    assert Settings().agent_name == "Friday"
