"""Aceptación de la carga histórica contra PostgreSQL real (T014, B14, B16, SC-004, FR-010).

Fixture SINTÉTICO de 30 features (`synthetic-hist-…`) en 3 archivos con un `id` repetido y 3
inválidas; base temporal, rol `observatory_consumer` y catálogo real.
"""
from datetime import datetime, timezone
from pathlib import Path

from tests.support.geo_harness import admin_rows, record_rows
from tests.support.historical_fixtures import (
    BAD_IDS, FIXTURE_QUARANTINED, FIXTURE_UNIQUE, FIXTURE_VALID, REPEATED_NUMBER, REPEATED_V2_UPDATED, hist_id,
    write_integration_fixture,
)
from tests.support.historical_harness import load_directory

EVIDENCE_NAME = "historico_carga_fixture"
CURRENT_SQL = ("SELECT count(*), count(*) FILTER (WHERE source = 'usgs_historical'), "
               "count(*) FILTER (WHERE is_synthetic), count(*) FILTER (WHERE replay_at IS NULL), "
               "count(DISTINCT ingested_at), min(ingested_at) FROM live.current_event")
KAFKA_SQL = ("SELECT (SELECT count(*) FROM live.event_version), "
             "(SELECT count(*) FROM live.event_version WHERE kafka_topic IS NOT NULL OR kafka_partition IS NOT NULL "
             "OR kafka_offset IS NOT NULL), (SELECT count(*) FROM live.quarantine), "
             "(SELECT count(*) FROM live.quarantine WHERE kafka_topic IS NOT NULL OR kafka_partition IS NOT NULL "
             "OR kafka_offset IS NOT NULL)")
OTHER_SCHEMA_SQL = ("SELECT (SELECT count(*) FROM replay.current_event) + (SELECT count(*) FROM replay.event_version) "
                    "+ (SELECT count(*) FROM replay.quarantine)")
QUARANTINE_SQL = "SELECT event_id, reason FROM live.quarantine ORDER BY event_id"
REPEATED_SQL = "SELECT updated_ms FROM live.current_event WHERE event_id = $1"
EXPECTED_INGESTED = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def test_load_counts_envelope_and_verification(db, tmp_path: Path) -> None:
    write_integration_fixture(tmp_path)
    outcome = load_directory(db, tmp_path)
    assert outcome.summary.unique == FIXTURE_UNIQUE and outcome.summary.quarantined == FIXTURE_QUARANTINED
    assert outcome.summary.new_event == FIXTURE_VALID
    total, historical, synthetic, no_replay, distinct_ingested, ingested = record_rows(
        db, EVIDENCE_NAME, CURRENT_SQL, "current_event: únicos - cuarentena, origen y marca sintética")[0]
    assert (total, historical, synthetic, no_replay) == (FIXTURE_VALID,) * 4
    assert distinct_ingested == 1 and ingested == EXPECTED_INGESTED
    assert outcome.verify.ok is True and outcome.verify.loaded == FIXTURE_VALID


def test_versions_have_null_kafka_columns_and_only_live_schema(db, tmp_path: Path) -> None:
    write_integration_fixture(tmp_path)
    load_directory(db, tmp_path)
    versions, versions_kafka, quarantine, quarantine_kafka = record_rows(
        db, EVIDENCE_NAME, KAFKA_SQL, "event_version y cuarentena: una fila por (id, updated); kafka_* nulos")[0]
    assert (versions, versions_kafka, quarantine, quarantine_kafka) == (FIXTURE_VALID, 0, FIXTURE_QUARANTINED, 0)
    assert admin_rows(db, OTHER_SCHEMA_SQL) == [(0,)]


def test_quarantine_reasons_and_repeated_id_keeps_latest_version(db, tmp_path: Path) -> None:
    write_integration_fixture(tmp_path)
    load_directory(db, tmp_path)
    reasons = record_rows(db, EVIDENCE_NAME, QUARANTINE_SQL, "cuarentena por evento inválido")
    assert reasons == [(BAD_IDS["lat"], "coordinates_out_of_range"), (BAD_IDS["lon"], "coordinates_out_of_range"),
                       (BAD_IDS["mag"], "mag_out_of_range")]
    assert admin_rows(db, REPEATED_SQL, hist_id(REPEATED_NUMBER)) == [(REPEATED_V2_UPDATED,)]
