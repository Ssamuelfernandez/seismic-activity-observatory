"""Reglas del procesamiento común aplicadas al histórico (T016, B16, SC-006, constitución §2, §4, §5, §6).

Eventos SINTÉTICOS (`synthetic-rule-…`), base temporal y catálogo real.
"""
from pathlib import Path

from tests.support import evidence
from tests.support.geo_harness import admin_rows, process_messages
from tests.support.historical_fixtures import MINUTE_MS, synthetic_feature, write_fixture
from tests.support.historical_harness import load_directory
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, SOURCE_FEED, build_event, build_message

EVIDENCE_NAME = "historico_reglas"
CURRENT_SQL = ("SELECT event_id, mag, depth_km, country_id, source, updated_ms FROM live.current_event "
               "WHERE event_id = $1")
QUARANTINE_SQL = "SELECT reason FROM live.quarantine WHERE event_id = $1"
VERSIONS_SQL = "SELECT count(*) FROM live.event_version WHERE event_id = $1"
MADRID = (-3.70, 40.42)
ATLANTIC = (-30.0, 35.0)
FILE = "usgs_2025-01.geojson"
OTHER_FILE = "usgs_2025-02.geojson"


def _load(db, tmp_path: Path, features: list[dict], second: list[dict] | None = None):
    files = {FILE: features}
    if second is not None:
        files[OTHER_FILE] = second
    write_fixture(tmp_path, files)
    return load_directory(db, tmp_path)


def _one(db, sql: str, event_id: str) -> tuple:
    rows = admin_rows(db, sql, event_id)
    assert len(rows) == 1
    return rows[0]


def test_null_magnitude_is_null_not_zero(db, tmp_path: Path) -> None:
    _load(db, tmp_path, [synthetic_feature("synthetic-rule-nullmag", mag=None)])
    row = _one(db, CURRENT_SQL, "synthetic-rule-nullmag")
    assert row[1] is None


def test_negative_magnitude_and_depth_are_valid(db, tmp_path: Path) -> None:
    feature = synthetic_feature("synthetic-rule-neg", mag=-0.06)
    feature["geometry"]["coordinates"][2] = -0.18
    outcome = _load(db, tmp_path, [feature])
    row = _one(db, CURRENT_SQL, "synthetic-rule-neg")
    assert outcome.summary.quarantined == 0 and float(row[1]) == -0.06 and float(row[2]) == -0.18


def test_latitude_145_goes_to_quarantine_once(db, tmp_path: Path) -> None:
    _load(db, tmp_path, [synthetic_feature("synthetic-rule-lat", lat=145)])
    assert admin_rows(db, QUARANTINE_SQL, "synthetic-rule-lat") == [("coordinates_out_of_range",)]
    assert admin_rows(db, CURRENT_SQL, "synthetic-rule-lat") == []


def test_country_by_geometry_madrid_and_atlantic(db, tmp_path: Path) -> None:
    _load(db, tmp_path, [synthetic_feature("synthetic-rule-madrid", lon=MADRID[0], lat=MADRID[1]),
                         synthetic_feature("synthetic-rule-atlantic", lon=ATLANTIC[0], lat=ATLANTIC[1])])
    assert _one(db, CURRENT_SQL, "synthetic-rule-madrid")[3] == "ESP"
    assert _one(db, CURRENT_SQL, "synthetic-rule-atlantic")[3] is None


def test_two_versions_in_different_files_only_the_latest_is_current(db, tmp_path: Path) -> None:
    older = synthetic_feature("synthetic-rule-ver", E1_UPDATED_1005, mag=4.0)
    newer = synthetic_feature("synthetic-rule-ver", E1_UPDATED_1005 + MINUTE_MS, mag=4.6)
    outcome = _load(db, tmp_path, [older], [newer])
    row = _one(db, CURRENT_SQL, "synthetic-rule-ver")
    assert float(row[1]) == 4.6 and row[5] == E1_UPDATED_1005 + MINUTE_MS
    assert _one(db, VERSIONS_SQL, "synthetic-rule-ver") == (1,) and outcome.summary.unique == 1


def test_event_already_in_database_with_higher_updated_does_not_go_back(db, tmp_path: Path) -> None:
    event_id = "synthetic-rule-live"
    live = build_message(build_event(event_id, E1_TIME_MS, E1_UPDATED_1005 + 5 * MINUTE_MS, 5.1),
                         source=SOURCE_FEED, is_synthetic=True)
    process_messages(db, [live])
    before = _one(db, CURRENT_SQL, event_id)
    outcome = _load(db, tmp_path, [synthetic_feature(event_id, E1_UPDATED_1005, mag=3.0)])
    after = _one(db, CURRENT_SQL, event_id)
    evidence.record_text(EVIDENCE_NAME, f"antes: source={before[4]} updated_ms={before[5]}\n"
                                        f"después de cargar un histórico con updated menor: "
                                        f"source={after[4]} updated_ms={after[5]}", "no retrocede")
    assert after == before and after[4] == SOURCE_FEED, f"source={after[4]} updated_ms={after[5]}"
    assert outcome.summary.late_old == 1 and outcome.summary.new_event == 0
