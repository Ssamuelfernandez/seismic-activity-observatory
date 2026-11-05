"""Procedimiento de hueco >24 h contra PostgreSQL real (T018, B12, constitución §1 y §2).

Base con 10 eventos SINTÉTICOS cargados por el camino normal (`process_record` con mensajes live); un
archivo de hueco repite 4 (mismo `updated`), 1 con `updated` menor y 3 nuevos.
"""
from pathlib import Path

from tests.support import evidence
from tests.support.geo_harness import admin_rows, process_messages
from tests.support.historical_fixtures import MINUTE_MS, write_fixture
from tests.support.historical_harness import load_directory
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, SOURCE_FEED, build_event, build_message

EVIDENCE_NAME = "historico_hueco"
GAP_FILE = "usgs_gap_20251230T000000_20251231T000000.geojson"
COUNTS_SQL = ("SELECT (SELECT count(*) FROM live.current_event), (SELECT count(*) FROM live.event_version), "
              "(SELECT count(*) FROM live.quarantine)")
SOURCES_SQL = "SELECT source, count(*) FROM live.current_event GROUP BY source ORDER BY source"
ROWS_SQL = "SELECT * FROM live.current_event WHERE event_id = ANY($1) ORDER BY event_id"


def _gap_id(number: int) -> str:
    return f"synthetic-gap-{number:02d}"


def _existing_messages() -> list[dict]:
    """Los 10 eventos ya presentes (camino normal, `source = usgs_feed`, sintéticos)."""
    return [build_message(build_event(_gap_id(n), E1_TIME_MS, E1_UPDATED_1005 + n * MINUTE_MS, 4.0),
                          source=SOURCE_FEED, is_synthetic=True) for n in range(10)]


def _gap_features() -> list[dict]:
    """Hueco: 4 iguales (0-3), 1 con `updated` menor (4) y 3 nuevos (10-12)."""
    same = [build_event(_gap_id(n), E1_TIME_MS, E1_UPDATED_1005 + n * MINUTE_MS, 4.0) for n in range(4)]
    older = [build_event(_gap_id(4), E1_TIME_MS, E1_UPDATED_1005 + 4 * MINUTE_MS - 1, 2.0)]
    new = [build_event(_gap_id(n), E1_TIME_MS, E1_UPDATED_1005 + n * MINUTE_MS, 4.0) for n in range(10, 13)]
    return same + older + new


def _counts(db) -> tuple[int, int, int]:
    return admin_rows(db, COUNTS_SQL)[0]


def test_gap_file_adds_only_new_events_and_never_goes_back(db, tmp_path: Path) -> None:
    process_messages(db, _existing_messages())
    watched = [_gap_id(n) for n in range(10)]
    rows_before = admin_rows(db, ROWS_SQL, watched)
    counts_before = _counts(db)
    assert counts_before == (10, 10, 0)

    write_fixture(tmp_path, {}, gaps={GAP_FILE: _gap_features()})
    first = load_directory(db, tmp_path)
    counts_after = _counts(db)
    evidence.record_text(EVIDENCE_NAME, f"antes (current, version, cuarentena): {counts_before}\n"
                                        f"después del hueco: {counts_after}\n"
                                        f"resumen: nuevos={first.summary.new_event} "
                                        f"iguales={first.summary.unchanged} antiguos={first.summary.late_old}",
                         "carga del hueco")
    assert (first.summary.new_event, first.summary.unchanged, first.summary.late_old) == (3, 4, 1)
    assert counts_after == (13, 14, 0)
    assert admin_rows(db, ROWS_SQL, watched) == rows_before
    assert dict(admin_rows(db, SOURCES_SQL)) == {"usgs_feed": 10, "usgs_historical": 3}


def test_repeating_the_gap_load_changes_nothing(db, tmp_path: Path) -> None:
    process_messages(db, _existing_messages())
    write_fixture(tmp_path, {}, gaps={GAP_FILE: _gap_features()})
    first = load_directory(db, tmp_path)
    again = load_directory(db, tmp_path)
    assert again.fingerprint == first.fingerprint
    assert (again.summary.new_event, again.summary.newer_version) == (0, 0)
    evidence.record_text(EVIDENCE_NAME, f"huella tras la 1.ª carga: {first.fingerprint}\n"
                                        f"huella tras repetir: {again.fingerprint}", "repetir el hueco")
