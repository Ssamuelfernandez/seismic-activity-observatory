"""Validez de los casos geográficos contra PostgreSQL real: pruebas 5 y 6 (T017).

Mag nula, negativos y coordenadas/geometría/tiempos inválidos, con el pipeline y el catálogo reales.
Todo es sintético (`synthetic-geo-...`, `is_synthetic = true`).
"""
import pytest

from common.records import ResultKind
from tests.support.geo_harness import admin_rows, process_messages, record_rows
from tests.support.messages import GEO_PREFIX, NEGATIVE_DEPTH, NEGATIVE_MAG, geo_cases

PRUEBA5 = "geografia_prueba5"
PRUEBA6 = "geografia_prueba6_cuarentena"
MAG_SQL = ("SELECT event_id, mag, depth_km, country_id, is_synthetic FROM live.current_event "
           "WHERE event_id = $1")
VERSION_MAG_SQL = "SELECT event_id, mag FROM live.event_version WHERE event_id = $1"
QUARANTINE_SQL = ("SELECT event_id, reason, kafka_topic, kafka_partition, kafka_offset, "
                  "left(original_sha256, 12) AS sha FROM live.quarantine ORDER BY kafka_offset")
HASH_LENGTH = 64
# caso -> motivo de cuarentena (kafka-message.md §6)
INVALID_CASES = {
    "lat-145": "coordinates_out_of_range",
    "lon-nan": "coordinates_out_of_range",
    "no-point": "invalid_geometry",
    "sin-time": "missing_time",
    "sin-updated": "missing_updated",
}


def _quoted(case: str) -> str:
    return f"'{GEO_PREFIX}{case}'"


def test_null_magnitude_stays_null_and_keeps_country(db) -> None:
    process_messages(db, [geo_cases()["mag-nula"]])
    current = record_rows(db, PRUEBA5, MAG_SQL.replace("$1", _quoted("mag-nula")), "current_event: mag NULL, país ESP")
    versions = record_rows(db, PRUEBA5, VERSION_MAG_SQL.replace("$1", _quoted("mag-nula")), "event_version: mag NULL")
    assert current == [(f"{GEO_PREFIX}mag-nula", None, 10.0, "ESP", True)]
    assert versions == [(f"{GEO_PREFIX}mag-nula", None)]
    zero = record_rows(db, PRUEBA5, "SELECT (SELECT count(*) FROM live.current_event WHERE mag = 0) AS current_mag_cero, "
                       "(SELECT count(*) FROM live.event_version WHERE mag = 0) AS version_mag_cero", "filas con mag = 0")
    assert zero == [(0, 0)]


def test_negative_values_are_stored_as_received_with_country(db) -> None:
    process_messages(db, [geo_cases()["negativos"]])
    rows = record_rows(db, PRUEBA5, MAG_SQL.replace("$1", _quoted("negativos")), "negativos: mag y profundidad tal cual")
    assert len(rows) == 1
    _, mag, depth, country, _ = rows[0]
    assert (float(mag), float(depth), country) == (NEGATIVE_MAG, NEGATIVE_DEPTH, "ESP")


def test_latitude_145_goes_to_quarantine_with_kafka_reference_and_hash(db) -> None:
    results, calls = process_messages(db, [geo_cases()["lat-145"]], start_offset=7)
    assert results[0].kind is ResultKind.QUARANTINE and calls == []
    rows = admin_rows(db, "SELECT event_id, reason, kafka_topic, kafka_partition, kafka_offset, "
                          "length(original_sha256) FROM live.quarantine")
    assert rows == [(f"{GEO_PREFIX}lat-145", "coordinates_out_of_range", "earthquakes.live", 0, 7, HASH_LENGTH)]
    assert admin_rows(db, "SELECT (SELECT count(*) FROM live.current_event), "
                          "(SELECT count(*) FROM live.event_version)") == [(0, 0)]


@pytest.mark.parametrize(("case", "reason"), list(INVALID_CASES.items()))
def test_invalid_case_goes_to_quarantine_without_calling_locator(db, case: str, reason: str) -> None:
    results, calls = process_messages(db, [geo_cases()[case]])
    assert results[0].kind is ResultKind.QUARANTINE and results[0].reason == reason
    assert calls == []
    assert admin_rows(db, "SELECT reason FROM live.quarantine") == [(reason,)]
    assert admin_rows(db, "SELECT count(*) FROM live.current_event") == [(0,)]


def test_all_cases_together_and_only_synthetic_events_are_flagged(db) -> None:
    cases = geo_cases()
    results, calls = process_messages(db, list(cases.values()))
    assert len(calls) == 4  # madrid, atlantico, mag-nula y negativos; los 5 inválidos no llegan al localizador
    assert sorted(r.reason for r in results if r.kind is ResultKind.QUARANTINE) == sorted(INVALID_CASES.values())
    record_rows(db, PRUEBA6, QUARANTINE_SQL, "cuarentena de los casos inválidos (referencia Kafka y hash)")
    stored = record_rows(db, PRUEBA6, "SELECT event_id, is_synthetic FROM live.current_event ORDER BY event_id",
                         "eventos guardados: todos sintéticos")
    assert len(stored) == 4 and all(flag is True and key.startswith(GEO_PREFIX) for key, flag in stored)
    assert admin_rows(db, "SELECT count(*) FROM live.current_event WHERE NOT is_synthetic") == [(0,)]
    assert admin_rows(db, "SELECT count(*) FROM live.quarantine WHERE is_synthetic IS FALSE") == [(0,)]
