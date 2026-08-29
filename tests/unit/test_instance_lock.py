"""AD-17: one writer. Two schedulers would double-fire every trigger."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from aos.adapters.system.file_instance_lock import FileInstanceLock
from aos.ports.system.instance_lock import LockHeldError


def test_lock_is_released_on_exit(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    with FileInstanceLock(path):
        assert path.exists()
    assert not path.exists()


def test_second_live_holder_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    held = FileInstanceLock(path)
    held.__enter__()
    try:
        with pytest.raises(LockHeldError, match="already running"), FileInstanceLock(path):
            pass
    finally:
        held.__exit__(None, None, None)


def test_diagnostic_names_the_holding_process(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    with FileInstanceLock(path):
        try:
            with FileInstanceLock(path):
                pass
        except LockHeldError as exc:
            assert str(os.getpid()) in str(exc)
        else:  # pragma: no cover
            pytest.fail("expected the second acquisition to be refused")


def test_a_lock_left_by_a_dead_process_is_taken_over(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    path.write_text("999999999", encoding="utf-8")  # a pid that cannot be alive
    with FileInstanceLock(path) as lock:
        assert lock.holder_pid == os.getpid()


def test_a_corrupt_lock_does_not_block_startup(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    path.write_text("not-a-pid", encoding="utf-8")
    with FileInstanceLock(path):
        assert path.exists()
