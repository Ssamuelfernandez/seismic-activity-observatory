"""Pruebas de la lectura verificada de los archivos del replay (T043). Sin Docker."""
import re
import shutil
from pathlib import Path

import pytest

from producer.replay_source import ReplaySourceError, load_verified_features

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "historical"
EXTRACTED_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MONTH_FILE = "usgs_2025-01.geojson"


def copy_data(tmp_path: Path) -> Path:
    """Copia el directorio real a uno temporal."""
    target = tmp_path / "historical"
    shutil.copytree(DATA_DIR, target)
    return target


def test_real_directory_returns_unique_events():
    pairs = load_verified_features(DATA_DIR)
    assert len(pairs) == 18302
    assert len({feature["id"] for feature, _ in pairs}) == 18302
    assert all(EXTRACTED_FORMAT.match(extracted) for _, extracted in pairs)


def test_altered_byte_names_the_file(tmp_path):
    directory = copy_data(tmp_path)
    path = directory / MONTH_FILE
    data = bytearray(path.read_bytes())
    data[-5] = data[-5] ^ 1
    path.write_bytes(bytes(data))
    with pytest.raises(ReplaySourceError, match=MONTH_FILE):
        load_verified_features(directory)


def test_missing_file_names_the_file(tmp_path):
    directory = copy_data(tmp_path)
    (directory / MONTH_FILE).unlink()
    with pytest.raises(ReplaySourceError, match=MONTH_FILE):
        load_verified_features(directory)
