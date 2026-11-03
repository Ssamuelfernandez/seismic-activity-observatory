"""Pruebas de common/health.py: el latido caduca y su ausencia significa no sano (A4)."""
import os

from common.health import clear_heartbeat, is_heartbeat_fresh, touch_heartbeat


def test_missing_heartbeat_is_not_fresh(tmp_path):
    assert not is_heartbeat_fresh(str(tmp_path / "no-existe"), 60, now=1000.0)


def test_recent_heartbeat_is_fresh(tmp_path):
    path = tmp_path / "alive"
    touch_heartbeat(str(path))
    os.utime(path, (990.0, 990.0))
    assert is_heartbeat_fresh(str(path), 60, now=1000.0)


def test_old_heartbeat_is_not_fresh(tmp_path):
    path = tmp_path / "alive"
    touch_heartbeat(str(path))
    os.utime(path, (800.0, 800.0))
    assert not is_heartbeat_fresh(str(path), 60, now=1000.0)


def test_clear_heartbeat_removes_previous_run_and_tolerates_absence(tmp_path):
    path = tmp_path / "alive"
    touch_heartbeat(str(path))
    clear_heartbeat(str(path))
    clear_heartbeat(str(path))
    assert not path.exists()
