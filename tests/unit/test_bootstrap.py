"""AD-19: one command, idempotent, never destructive."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_bootstrap():
    spec = importlib.util.spec_from_file_location("bootstrap", ROOT / "run.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap"] = module
    spec.loader.exec_module(module)
    return module


def test_dependency_fingerprint_tracks_pyproject() -> None:
    boot = _load_bootstrap()
    first = boot._dependency_fingerprint()
    assert first == boot._dependency_fingerprint()
    assert len(first) == 64


def test_config_scaffolding_never_overwrites(tmp_path: Path, monkeypatch) -> None:
    boot = _load_bootstrap()
    existing = tmp_path / "config.toml"
    existing.write_text("agent_name = 'Mine'", encoding="utf-8")
    monkeypatch.setattr(boot, "CONFIG", existing)

    assert boot.ensure_config() is False
    assert existing.read_text(encoding="utf-8") == "agent_name = 'Mine'"


def test_directory_creation_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    boot = _load_bootstrap()
    monkeypatch.setattr(boot, "ROOT", tmp_path)

    assert boot.ensure_directories("dev") is True
    assert boot.ensure_directories("dev") is False
