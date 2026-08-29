"""AD-20: limits are enforced, not aspirational.

Ruff covers function length, argument count, complexity and nesting. Module
length has no ruff rule, so it is checked here.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOFT_LIMIT = 400
HARD_LIMIT = 500
SCANNED = ("src", "relay")


def _modules() -> list[Path]:
    files = [
        path
        for folder in SCANNED
        if (ROOT / folder).is_dir()
        for path in (ROOT / folder).rglob("*.py")
        if "__pycache__" not in path.parts
    ]
    entrypoint = ROOT / "run.py"
    if entrypoint.exists():
        files.append(entrypoint)
    return files


def test_no_module_exceeds_the_hard_limit() -> None:
    oversized = [
        f"{path.relative_to(ROOT)}: {len(path.read_text(encoding='utf-8').splitlines())} lines"
        for path in _modules()
        if len(path.read_text(encoding="utf-8").splitlines()) > HARD_LIMIT
    ]
    assert not oversized, "split these; a module over 500 lines is a defect:\n" + "\n".join(
        oversized
    )


def test_modules_over_the_soft_limit_are_reported() -> None:
    """Not a failure, but worth seeing before it becomes one."""
    approaching = [
        (path.relative_to(ROOT), len(path.read_text(encoding="utf-8").splitlines()))
        for path in _modules()
        if SOFT_LIMIT < len(path.read_text(encoding="utf-8").splitlines()) <= HARD_LIMIT
    ]
    for path, count in approaching:
        print(f"  approaching the limit: {path} at {count} lines")
