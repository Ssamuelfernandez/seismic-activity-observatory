"""Pruebas sin Docker de la semilla real (T076, K4). Usa `data/historical/` de verdad."""
import shutil
from pathlib import Path

import pytest

from scripts.benchmarks.seed import SeedError, load_seed

HISTORICAL = Path(__file__).resolve().parents[2] / "data" / "historical"
EXPECTED_UNIQUE = 18302
EXPECTED_FILES = 13


def test_real_seed_gives_unique_events_and_verified_files() -> None:
    seed = load_seed(HISTORICAL)
    assert len(seed.events) == EXPECTED_UNIQUE
    assert len(seed.verified_files) == EXPECTED_FILES
    ids = [event["id"] for event in seed.events]
    assert len(set(ids)) == EXPECTED_UNIQUE


def test_altered_file_stops_with_error(tmp_path: Path) -> None:
    copy = tmp_path / "historical"
    shutil.copytree(HISTORICAL, copy)
    target = copy / "usgs_2025-06.geojson"
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(SeedError, match="usgs_2025-06.geojson"):
        load_seed(copy)


def test_missing_file_and_missing_manifest_stop_with_error(tmp_path: Path) -> None:
    copy = tmp_path / "historical"
    shutil.copytree(HISTORICAL, copy)
    (copy / "usgs_2025-03.geojson").unlink()
    with pytest.raises(SeedError, match="falta"):
        load_seed(copy)
    with pytest.raises(SeedError, match="manifest.json"):
        load_seed(tmp_path / "vacio")
