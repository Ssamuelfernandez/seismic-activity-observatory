"""País por geometría contra PostgreSQL real: pruebas 7 y refuerzo de C9, C11 y C12 (T016).

Catálogo real cargado por `load_country_catalog` y pipeline real con el localizador real. Los eventos
son sintéticos (`synthetic-geo-...`). `public.country` se vacía entre pruebas: cada llamada recarga.
"""
from common.records import ResultKind
from tests.support.geo_harness import admin_rows, newer_version, process_messages, record_rows
from tests.support.messages import ATLANTIC, geo_cases

REPEATS = 100
EVIDENCE_NAME = "geografia_prueba7"
COUNTRY_SQL = "SELECT event_id, country_id, place FROM live.current_event WHERE event_id = $1"
TOTALS_SQL = ("SELECT count(*) AS total, count(country_id) AS con_pais, count(*) - count(country_id) AS sin_pais "
              "FROM live.current_event")
CASES_SQL = ("SELECT event_id, country_id, place FROM live.current_event "
             "WHERE event_id LIKE 'synthetic-geo-%' ORDER BY event_id")
QUARANTINE_COUNT_SQL = "SELECT count(*) FROM live.quarantine"
FK_ORPHANS_SQL = ("SELECT count(*) FROM live.current_event e LEFT JOIN public.country c USING (country_id) "
                  "WHERE e.country_id IS NOT NULL AND c.country_id IS NULL")
SNAPSHOT_SQL = {
    "current_event": "SELECT * FROM live.current_event ORDER BY event_id",
    "event_version": "SELECT * FROM live.event_version ORDER BY event_id, updated_ms",
    "quarantine": "SELECT * FROM live.quarantine ORDER BY id",
    "date_dim": "SELECT * FROM public.date_dim ORDER BY date_id",
}
PARIS = (2.35, 48.85)


def _country_of(db, event_id: str):
    rows = admin_rows(db, COUNTRY_SQL, event_id)
    assert len(rows) == 1
    return rows[0][1]


def test_madrid_is_spain_even_if_place_names_another_country(db) -> None:
    madrid = geo_cases()["madrid"]
    process_messages(db, [madrid])
    assert "París" in madrid["event"]["properties"]["place"]
    assert _country_of(db, "synthetic-geo-madrid") == "ESP"
    record_rows(db, EVIDENCE_NAME, COUNTRY_SQL.replace("$1", "'synthetic-geo-madrid'"), "Madrid: país por geometría")


def test_reprocessing_madrid_100_times_changes_no_table(db) -> None:
    raw_message = geo_cases()["madrid"]
    process_messages(db, [raw_message])
    before = {name: admin_rows(db, sql) for name, sql in SNAPSHOT_SQL.items()}
    results, _ = process_messages(db, [raw_message] * REPEATS, start_offset=1)
    after = {name: admin_rows(db, sql) for name, sql in SNAPSHOT_SQL.items()}
    assert len(results) == REPEATS and before == after
    assert _country_of(db, "synthetic-geo-madrid") == "ESP"


def test_atlantic_event_is_stored_without_country_and_not_quarantined(db) -> None:
    results, calls = process_messages(db, [geo_cases()["atlantico"]])
    assert results[0].kind is ResultKind.EVENT and calls == [(ATLANTIC[0], ATLANTIC[1])]
    assert _country_of(db, "synthetic-geo-atlantico") is None
    assert admin_rows(db, QUARANTINE_COUNT_SQL) == [(0,)]
    record_rows(db, EVIDENCE_NAME, CASES_SQL, "Atlántico: fila con country_id vacío (NULL) y sin cuarentena")


def test_with_country_plus_without_country_equals_total(db) -> None:
    cases = geo_cases()
    process_messages(db, [cases["madrid"], cases["atlantico"], cases["mag-nula"]])
    total, with_country, without_country = record_rows(db, EVIDENCE_NAME, TOTALS_SQL,
                                                       "total = con país + sin país")[0]
    assert (total, with_country, without_country) == (3, 2, 1)
    assert with_country + without_country == total and with_country > 0 and without_country > 0
    record_rows(db, EVIDENCE_NAME, CASES_SQL, "Filas de los casos geográficos")


def test_later_version_at_sea_clears_country(db) -> None:
    madrid = geo_cases()["madrid"]
    process_messages(db, [madrid])
    assert _country_of(db, "synthetic-geo-madrid") == "ESP"
    process_messages(db, [newer_version(madrid, *ATLANTIC)], start_offset=1)
    assert _country_of(db, "synthetic-geo-madrid") is None


def test_late_old_version_in_another_country_does_not_change_country(db) -> None:
    madrid = geo_cases()["madrid"]
    process_messages(db, [newer_version(madrid, *madrid["event"]["geometry"]["coordinates"][:2], steps=2)])
    process_messages(db, [newer_version(madrid, *PARIS, steps=1)], start_offset=1)
    assert _country_of(db, "synthetic-geo-madrid") == "ESP"
    assert admin_rows(db, "SELECT count(*) FROM live.event_version") == [(2,)]


def test_every_country_id_exists_in_the_catalog(db) -> None:
    cases = geo_cases()
    process_messages(db, [cases["madrid"], cases["atlantico"], newer_version(cases["negativos"], *PARIS)])
    assert admin_rows(db, FK_ORPHANS_SQL) == [(0,)]
    assert admin_rows(db, "SELECT country_id FROM live.current_event WHERE event_id = 'synthetic-geo-negativos'") == [("FRA",)]
