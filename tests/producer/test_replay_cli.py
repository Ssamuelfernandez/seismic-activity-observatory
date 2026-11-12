"""Pruebas del CLI del replay (T045). Sin Docker, con dobles del lector y del publicador."""
import logging
import shutil
from pathlib import Path

import pytest

from producer.replay import DEFAULT_COUNT, DEFAULT_DATA_DIR, DEFAULT_INTERVAL_SECONDS, build_parser, main
from producer.replay_runner import ReplaySummary
from producer.replay_selection import DEFAULT_ZONE
from producer.replay_source import load_verified_features

REAL_DIR = Path(__file__).resolve().parents[2] / "data" / "historical"


class FakeRunner:
    """Doble de `run_replay` que guarda lo recibido."""

    def __init__(self):
        self.calls = []

    async def __call__(self, items, interval, settings, retry):
        self.calls.append((items, interval, settings))
        real = sum(1 for item in items if not item.is_synthetic)
        return ReplaySummary(real, len(items) - real, len(items))


@pytest.fixture(autouse=True)
def kafka_env(monkeypatch):
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def test_defaults_are_the_documented_ones():
    args = build_parser().parse_args([])
    assert (args.interval, args.zone, args.count, args.data_dir) == (2.0, "chile-norte", 20, "data/historical")
    assert (DEFAULT_INTERVAL_SECONDS, DEFAULT_ZONE, DEFAULT_COUNT, DEFAULT_DATA_DIR) == (
        2.0, "chile-norte", 20, "data/historical")


def test_real_run_publishes_26_and_reports_summary(caplog):
    runner = FakeRunner()
    with caplog.at_level(logging.INFO):
        code = main(["--data-dir", str(REAL_DIR)], runner=runner)
    assert code == 0
    items, interval, settings = runner.calls[0]
    assert len(items) == 26 and interval == 2.0
    assert settings.bootstrap_servers == "kafka:9092"
    assert "Publicados: 26 (20 reales + 6 del bloque controlado)" in caplog.text


def test_unknown_zone_exits_1_without_publishing():
    runner = FakeRunner()
    assert main(["--zone", "marte", "--data-dir", str(REAL_DIR)], runner=runner) == 1
    assert runner.calls == []


def test_altered_file_exits_1_without_publishing(tmp_path, caplog):
    directory = tmp_path / "historical"
    shutil.copytree(REAL_DIR, directory)
    path = directory / "usgs_2025-01.geojson"
    data = bytearray(path.read_bytes())
    data[-5] ^= 1
    path.write_bytes(bytes(data))
    runner = FakeRunner()
    assert main(["--data-dir", str(directory)], runner=runner, loader=load_verified_features) == 1
    assert runner.calls == []
    assert "usgs_2025-01.geojson" in caplog.text


def test_empty_selection_exits_1():
    runner = FakeRunner()
    assert main([], runner=runner, loader=lambda directory: []) == 1
    assert runner.calls == []


def test_fewer_events_than_count_reports_real_number(caplog):
    runner = FakeRunner()
    with caplog.at_level(logging.INFO):
        code = main(["--count", "500", "--data-dir", str(REAL_DIR)], runner=runner)
    assert code == 0
    items = runner.calls[0][0]
    real = sum(1 for item in items if not item.is_synthetic)
    assert real < 500
    assert f"Solo hay {real} eventos" in caplog.text
