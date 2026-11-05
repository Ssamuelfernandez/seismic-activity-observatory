"""Escenario `geo` (T021, pruebas 5 y 7, FR-009): catálogo de países y país por geometría con Kafka real.

Arranca el stack limpio, comprueba la carga del catálogo (177), publica los casos `geo-*`, lee
`current_event` y `quarantine` con el administrador y reinicia el consumidor (carga repetible).
"""
import re

from scripts.consumer_scenarios import stack
from scripts.consumer_scenarios.helpers import GEO_EVIDENCE_DIR
from scripts.consumer_scenarios.report import Checks, Evidence

CATALOG_TOTAL = 177
CATALOG_LINE = re.compile(r"catalog loaded total=(\d+) inserted=(\d+) updated=(\d+)")
COUNT_SQL = "SELECT count(*) FROM public.country"
EVENTS_SQL = ("SELECT event_id, coalesce(country_id, '(NULL)') AS country_id, coalesce(mag::text, '(NULL)') AS mag, "
              "is_synthetic FROM live.current_event WHERE event_id LIKE 'synthetic-geo-%' ORDER BY event_id;")
QUARANTINE_SQL = ("SELECT event_id, reason, kafka_topic, kafka_partition, kafka_offset FROM live.quarantine "
                  "WHERE event_id LIKE 'synthetic-geo-%' ORDER BY kafka_offset;")
TOTALS_SQL = ("SELECT count(*) AS total, count(country_id) AS con_pais, count(*) - count(country_id) AS sin_pais "
              "FROM live.current_event;")
CASES = ("geo-madrid", "geo-atlantico", "geo-mag-nula", "geo-lat-145")
NULL_TEXT = "(NULL)"
# evento -> (country_id, mag) esperados en current_event; None en mag = sin comprobar
EXPECTED_EVENTS = {
    "synthetic-geo-atlantico": (NULL_TEXT, None),
    "synthetic-geo-madrid": ("ESP", None),
    "synthetic-geo-mag-nula": ("ESP", NULL_TEXT),
}
LAT_145_REASON = "coordinates_out_of_range"
LAT_145_ID = "synthetic-geo-lat-145"


def catalog_load_results(log_text: str) -> list[tuple[int, int, int]]:
    """Tripletas (total, inserted, updated) de las líneas `catalog loaded ...` de un registro, en orden."""
    return [tuple(int(group) for group in match.groups()) for match in CATALOG_LINE.finditer(log_text)]


def check_catalog(checks: Checks, expected_runs: list[tuple[int, int, int]]) -> None:
    """La línea de carga y el recuento de `public.country` coinciden con lo esperado."""
    found = catalog_load_results(stack.consumer_log())
    checks.record(found == expected_runs, f"Línea `catalog loaded` por arranque: {expected_runs}", str(found))
    count = stack.psql_scalar(COUNT_SQL)
    checks.record(count == str(CATALOG_TOTAL), f"SELECT count(*) FROM public.country = {CATALOG_TOTAL}", count)


def check_events(checks: Checks) -> None:
    """Madrid ESP, Atlántico sin país, mag nula NULL con ESP y todos sintéticos."""
    rows = {r[0]: r for r in stack.psql_rows(EVENTS_SQL)}
    checks.record(set(rows) == set(EXPECTED_EVENTS), "current_event contiene madrid, atlantico y mag-nula", str(sorted(rows)))
    for event_id, (country, mag) in EXPECTED_EVENTS.items():
        row = rows.get(event_id, [""] * 4)
        ok = row[1] == country and (mag is None or row[2] == mag) and row[3] == "t"
        checks.record(ok, f"{event_id}: country_id={country}" + ("" if mag is None else f", mag={mag}"),
                      f"country_id={row[1]} mag={row[2]} is_synthetic={row[3]}")


def check_quarantine(checks: Checks) -> None:
    """La latitud 145 está en cuarentena con su motivo y no en `current_event`."""
    rows = stack.psql_rows(QUARANTINE_SQL)
    ok = len(rows) == 1 and rows[0][:3] == [LAT_145_ID, LAT_145_REASON, "earthquakes.live"]
    checks.record(ok, f"{LAT_145_ID} en cuarentena ({LAT_145_REASON}), referencia Kafka incluida", str(rows))
    stored = stack.psql_scalar(f"SELECT count(*) FROM live.current_event WHERE event_id = '{LAT_145_ID}'")
    checks.record(stored == "0", "lat-145 no está en current_event", stored)


def run(checks: Checks) -> None:
    """Ejecuta el escenario y escribe `geografia_catalogo.out` y `geografia_pruebas5_7_kafka.out`."""
    stack.build_images(needs_tests_image=True)
    stack.reset_stack()
    catalog = Evidence("geografia_catalogo", "out", GEO_EVIDENCE_DIR)
    check_catalog(checks, [(CATALOG_TOTAL, CATALOG_TOTAL, 0)])
    catalog.add("Primer arranque (base nueva): línea del registro y recuento", checks.take_lines())
    kafka = Evidence("geografia_pruebas5_7_kafka", "out", GEO_EVIDENCE_DIR)
    group = stack.consumer_group()
    for case in CASES:
        checks.record(True, f"Publicado el caso {case}", stack.publish(case))
    checks.record(stack.wait_lag_zero(group), "El grupo llega a lag 0 tras publicar los casos geo-*")
    kafka.add("current_event (administrador, Kafka real)", f"{EVENTS_SQL}\n{stack.psql_table(EVENTS_SQL)}")
    kafka.add("Recuentos: total = con país + sin país", f"{TOTALS_SQL}\n{stack.psql_table(TOTALS_SQL)}")
    kafka.add("quarantine (administrador, Kafka real)", f"{QUARANTINE_SQL}\n{stack.psql_table(QUARANTINE_SQL)}")
    check_events(checks)
    check_quarantine(checks)
    kafka.add("Comprobaciones de las pruebas 5 y 7", checks.take_lines())
    healthy = stack.restart_consumer()
    checks.record(healthy, "docker compose restart consumer: vuelve a estar healthy")
    check_catalog(checks, [(CATALOG_TOTAL, CATALOG_TOTAL, 0), (CATALOG_TOTAL, 0, 0)])
    catalog.add("Tras `docker compose restart consumer` (carga repetible: inserted=0 updated=0)", checks.take_lines())
    catalog.write()
    kafka.write()
