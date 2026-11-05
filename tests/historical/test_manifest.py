"""Pruebas del manifiesto: estructuras, sha256, escritura atómica y verificación (T003, B15)."""
import hashlib
from pathlib import Path

import pytest

from historical.manifest import (
    FileRecord, Manifest, ManifestFileError, QueryRecord, Totals, read_manifest, sha256_of,
    verify_file, write_manifest,
)


def sample_manifest(sha: str) -> Manifest:
    """Manifiesto sintético con un archivo y una consulta."""
    query = QueryRecord("https://example.invalid/q", "2025-01-01T00:00:00", "2025-02-01T00:00:00", 2, 2)
    record = FileRecord("usgs_2025-01.geojson", sha, 2, "2026-11-05T10:00:00Z", [query])
    return Manifest(year=2025, files=[record], gaps=[], totals=Totals(2, 0, 2, 2))


def test_sha256_of_matches_hashlib() -> None:
    assert sha256_of(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_round_trip(tmp_path: Path) -> None:
    manifest = sample_manifest("a" * 64)
    write_manifest(tmp_path, manifest)
    assert read_manifest(tmp_path) == manifest
    assert not list(tmp_path.glob("*.tmp"))


def test_read_missing_manifest_returns_none(tmp_path: Path) -> None:
    assert read_manifest(tmp_path) is None


def test_verify_file_ok(tmp_path: Path) -> None:
    (tmp_path / "usgs_2025-01.geojson").write_bytes(b"data")
    record = sample_manifest(sha256_of(b"data")).files[0]
    verify_file(tmp_path, record)


def test_verify_file_altered_names_file(tmp_path: Path) -> None:
    (tmp_path / "usgs_2025-01.geojson").write_bytes(b"data")
    record = sample_manifest(sha256_of(b"other")).files[0]
    with pytest.raises(ManifestFileError, match="usgs_2025-01.geojson"):
        verify_file(tmp_path, record)


def test_verify_file_absent_names_file(tmp_path: Path) -> None:
    record = sample_manifest("a" * 64).files[0]
    with pytest.raises(ManifestFileError, match="usgs_2025-01.geojson"):
        verify_file(tmp_path, record)
