"""Pruebas del cargador histórico con escritores de mentira (T011, B16, FR-008, FR-009, FR-013).

Datos SINTÉTICOS (`synthetic-…`). No hay base: los escritores anotan lo que reciben.
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from common.config import RetrySettings
from common.geo import CountryMatch
from common.records import VersionOutcome
from consumer.pipeline import PipelineDeps
from consumer.resilience import RetryControl
from historical.loader import load_historical
from historical.manifest import ManifestFileError
from tests.support.historical_fixtures import synthetic_feature, write_fixture

NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
NO_COUNTRY = CountryMatch(None, ())


class Recorder:
    """Escritores de mentira: anotan filas y devuelven el resultado pedido por `id`."""

    def __init__(self, outcomes: dict[str, VersionOutcome] | None = None) -> None:
        self.event_rows: list = []
        self.quarantine_rows: list = []
        self.outcomes = outcomes or {}

    async def write_event(self, rows, mode):
        self.event_rows.append((rows, mode))
        return self.outcomes.get(rows.current["event_id"], VersionOutcome.NEW_EVENT)

    async def write_quarantine(self, row, mode):
        self.quarantine_rows.append((row, mode))
        return True

    def deps(self) -> PipelineDeps:
        control = RetryControl(RetrySettings(1, 30), asyncio.Event())
        return PipelineDeps(self.write_event, self.write_quarantine, control, lambda lon, lat: NO_COUNTRY,
                            lambda: NOW)


def run(directory: Path, recorder: Recorder, is_synthetic: bool = True):
    return asyncio.run(load_historical(directory, recorder.deps(), is_synthetic))


def three_files(directory: Path) -> None:
    """Tres archivos con un `id` repetido en dos de ellos (la versión mayor está en el segundo)."""
    write_fixture(directory, {
        "usgs_2025-01.geojson": [synthetic_feature("synthetic-h1"), synthetic_feature("synthetic-h2", 1_000)],
        "usgs_2025-02.geojson": [synthetic_feature("synthetic-h2", 2_000), synthetic_feature("synthetic-h3")],
        "usgs_2025-03.geojson": [synthetic_feature("synthetic-h4")],
    })


def test_loads_each_unique_event_once_with_historical_envelope(tmp_path: Path) -> None:
    three_files(tmp_path)
    recorder = Recorder()
    summary = run(tmp_path, recorder)
    ids = sorted(rows.current["event_id"] for rows, _ in recorder.event_rows)
    assert ids == ["synthetic-h1", "synthetic-h2", "synthetic-h3", "synthetic-h4"]
    assert summary.unique == 4 and summary.new_event == 4 and summary.quarantined == 0
    assert sorted(summary.event_ids) == ids
    for rows, mode in recorder.event_rows:
        assert mode == "live" and rows.current["source"] == "usgs_historical"
        assert rows.current["is_synthetic"] is True and rows.current["replay_at"] is None
        assert rows.current["ingested_at"] == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        assert (rows.version["kafka_topic"], rows.version["kafka_partition"],
                rows.version["kafka_offset"]) == (None, None, None)


def test_duplicate_id_keeps_the_higher_updated(tmp_path: Path) -> None:
    three_files(tmp_path)
    recorder = Recorder()
    run(tmp_path, recorder)
    chosen = [rows for rows, _ in recorder.event_rows if rows.current["event_id"] == "synthetic-h2"]
    assert len(chosen) == 1 and chosen[0].current["updated_ms"] == 2_000


def test_summary_counts_outcomes_and_by_file(tmp_path: Path) -> None:
    three_files(tmp_path)
    recorder = Recorder({"synthetic-h1": VersionOutcome.NEWER_VERSION, "synthetic-h3": VersionOutcome.REDELIVERY,
                         "synthetic-h4": VersionOutcome.LATE_OLD_VERSION})
    summary = run(tmp_path, recorder)
    assert (summary.new_event, summary.newer_version, summary.unchanged, summary.late_old) == (1, 1, 1, 1)
    assert summary.by_file == {"usgs_2025-01.geojson": 1, "usgs_2025-02.geojson": 2, "usgs_2025-03.geojson": 1}


def test_gap_files_are_loaded_too(tmp_path: Path) -> None:
    write_fixture(tmp_path, {"usgs_2025-01.geojson": [synthetic_feature("synthetic-h1")]},
                  gaps={"usgs_gap_20251230T000000_20251231T000000.geojson": [synthetic_feature("synthetic-g1")]})
    recorder = Recorder()
    summary = run(tmp_path, recorder)
    assert summary.unique == 2 and len(recorder.event_rows) == 2


def test_invalid_event_goes_to_quarantine_and_load_continues(tmp_path: Path) -> None:
    bad = synthetic_feature("synthetic-bad", lat=145)
    write_fixture(tmp_path, {"usgs_2025-01.geojson": [synthetic_feature("synthetic-h1"), bad,
                                                      synthetic_feature("synthetic-h2")]})
    recorder = Recorder()
    summary = run(tmp_path, recorder)
    assert summary.quarantined == 1 and summary.new_event == 2
    assert summary.quarantined_ids == ["synthetic-bad"]
    row, _ = recorder.quarantine_rows[0]
    assert row.reason == "coordinates_out_of_range" and row.kafka_partition is None


def test_quarantine_bytes_are_stable_between_loads(tmp_path: Path) -> None:
    write_fixture(tmp_path, {"usgs_2025-01.geojson": [synthetic_feature("synthetic-bad", lat=145)]})
    hashes = []
    for _ in range(2):
        recorder = Recorder()
        run(tmp_path, recorder)
        hashes.append(recorder.quarantine_rows[0][0].original_sha256)
    assert hashes[0] == hashes[1]


def test_missing_file_stops_before_writing_anything(tmp_path: Path) -> None:
    three_files(tmp_path)
    (tmp_path / "usgs_2025-02.geojson").unlink()
    recorder = Recorder()
    with pytest.raises(ManifestFileError, match="usgs_2025-02.geojson"):
        run(tmp_path, recorder)
    assert recorder.event_rows == [] and recorder.quarantine_rows == []


def test_altered_file_stops_before_writing_anything(tmp_path: Path) -> None:
    three_files(tmp_path)
    path = tmp_path / "usgs_2025-03.geojson"
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    recorder = Recorder()
    with pytest.raises(ManifestFileError, match="usgs_2025-03.geojson"):
        run(tmp_path, recorder)
    assert recorder.event_rows == []


def test_missing_manifest_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestFileError, match="manifest.json"):
        run(tmp_path, Recorder())

