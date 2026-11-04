"""Escenario `faq12` (T074, quickstart §5): secuencia de la FAQ 12 con Kafka real, en tres lecturas.

L1: 5 mensajes con la base vacía; se para el consumidor y se lee su `COUNTERS` (sesión 1).
L2 (prueba 2): 100 reenvíos del mensaje 1; los dos `count(*)` no cambian.
L3 (pruebas 3 y 4): versión antigua no vista; se para el consumidor y se lee su `COUNTERS` (sesión 2).
"""
import json

from consumer.counters import check_identities
from scripts.consumer_scenarios import stack
from scripts.consumer_scenarios.helpers import (
    compare_counters, compare_with_sql, evidence_path, extract_last_counters,
)
from scripts.consumer_scenarios.report import ENCODING, Checks, Evidence

E1, E2 = "synthetic-faq12-e1", "synthetic-faq12-e2"
E1_MAG_FINAL, E1_UPDATED_FINAL = 4.6, "1793786940000"
EVIDENCE_QUERIES = (
    "SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY event_id;",
    "SELECT event_id, updated_ms, mag FROM live.event_version ORDER BY event_id, updated_ms;",
    "SELECT count(*) AS current_rows FROM live.current_event;",
    "SELECT count(*) AS version_rows FROM live.event_version;",
)
COUNT_SQL = "SELECT (SELECT count(*) FROM live.current_event), (SELECT count(*) FROM live.event_version)"
L1_COUNTERS = {"received": 5, "new_events": 2, "newer_versions_applied": 1, "redeliveries_ignored": 2,
               "late_old_versions": 0, "ms_to_utc_conversions": 5}
L3_COUNTERS = {"received": 101, "redeliveries_ignored": 100, "late_old_versions": 1, "new_events": 0,
               "ms_to_utc_conversions": 101}


def snapshot(evidence: Evidence, label: str) -> None:
    """Añade a la evidencia las cuatro consultas de evidencia con su salida, bajo una lectura."""
    body = "\n\n".join(f"{query}\n{stack.psql_table(query)}" for query in EVIDENCE_QUERIES)
    evidence.add(label, body)


def counts() -> tuple[int, int]:
    """(filas de `current_event`, filas de `event_version`)."""
    current, versions = stack.psql_rows(COUNT_SQL)[0]
    return int(current), int(versions)


def finish_session(evidence: Evidence, label: str) -> dict:
    """Para el consumidor (SIGTERM), lee su última línea `COUNTERS` y la guarda como bloque."""
    stack.stop_consumer()
    counters = extract_last_counters(stack.consumer_log())
    evidence.add(label, "COUNTERS " + json.dumps(counters, sort_keys=True))
    return counters


def publish_and_wait(checks: Checks, group: str, case: str) -> None:
    """Publica un caso y espera a lag 0."""
    checks.record(True, f"Publicado el caso {case}", stack.publish(case))
    checks.record(stack.wait_lag_zero(group), f"El grupo llega a lag 0 tras {case}")


def check_l1_state(checks: Checks) -> None:
    """L1: 2 filas actuales, E1 en 4.6 / 1793786940000 y 3 versiones."""
    rows = stack.psql_rows("SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY 1")
    e1, e2 = (rows + [[""] * 4] * 2)[:2]
    ok = (len(rows) == 2 and e1[0] == E1 and float(e1[1]) == E1_MAG_FINAL and e1[2] == E1_UPDATED_FINAL
          and e2[0] == E2 and float(e2[1]) == 3.1 and e1[3] == e2[3] == "t")
    checks.record(ok, "L1: 2 filas actuales, E1 mag 4.6 con updated_ms 1793786940000, E2 mag 3.1, sintéticos", str(rows))
    checks.record(counts() == (2, 3), "L1: current_event = 2 y event_version = 3", str(counts()))


def lecture_1(checks: Checks, group: str, evidence: Evidence) -> None:
    """L1 (SC-001): base vacía, 5 mensajes, lag 0, consultas y COUNTERS de la sesión 1."""
    snapshot(evidence, "L1 antes: base vacía")
    publish_and_wait(checks, group, "faq12")
    snapshot(evidence, "L1 después: tras publicar los 5 mensajes de la FAQ 12")
    check_l1_state(checks)
    counters = finish_session(evidence, "L1 COUNTERS de la sesión 1 (tras docker compose stop consumer)")
    problems = compare_counters(counters, L1_COUNTERS) + compare_with_sql(counters, 2, {})
    checks.record(not problems, "L1: COUNTERS de la sesión 1 y conciliación con SQL", "; ".join(problems) or str(counters))
    checks.record(stack.start_consumer(), "El consumidor vuelve a estar healthy (sesión 2)")
    evidence.add("L1 comprobaciones", checks.take_lines())


def lecture_2(checks: Checks, group: str) -> None:
    """L2 (prueba 2): 100 reenvíos del mensaje 1 no cambian ningún recuento."""
    evidence = Evidence("prueba2_reenvio", "out")
    before = counts()
    evidence.add("L2 antes del reenvío (sesión 2)", f"current_event={before[0]} event_version={before[1]}")
    publish_and_wait(checks, group, "replay-100")
    snapshot(evidence, "L2 después de reenviar 100 veces el mensaje 1")
    checks.record(counts() == before == (2, 3), "L2: current_event = 2 y event_version = 3 tras 100 repeticiones", str(counts()))
    evidence.add("L2 comprobaciones", checks.take_lines())
    evidence.write()


def check_l3_state(checks: Checks) -> None:
    """L3: 4 versiones (3 de E1) y E1 sigue en 4.6 / 1793786940000."""
    versions = stack.psql_rows("SELECT event_id FROM live.event_version")
    current = stack.psql_rows(f"SELECT mag, updated_ms FROM live.current_event WHERE event_id = '{E1}'")[0]
    checks.record(len(versions) == 4 and sum(v[0] == E1 for v in versions) == 3,
                  "L3: event_version = 4 filas (3 de E1)", str(len(versions)))
    checks.record(float(current[0]) == E1_MAG_FINAL and current[1] == E1_UPDATED_FINAL,
                  "L3: E1 sigue en mag 4.6 y updated_ms 1793786940000", str(current))


def lecture_3(checks: Checks, group: str) -> None:
    """L3 (pruebas 3 y 4): versión antigua tardía no vista; COUNTERS de la sesión 2."""
    evidence = Evidence("prueba3_4_versiones", "out")
    publish_and_wait(checks, group, "late-old")
    snapshot(evidence, "L3 después de publicar E1 con updated 1793786820000 (10:07) y mag 4.4")
    check_l3_state(checks)
    counters = finish_session(evidence, "L3 COUNTERS de la sesión 2 (tras docker compose stop consumer)")
    problems = compare_counters(counters, L3_COUNTERS) + check_identities(counters)
    checks.record(not problems, "L3: COUNTERS de la sesión 2 e identidades de FR-023", "; ".join(problems) or str(counters))
    checks.record(stack.start_consumer(), "El consumidor vuelve a estar healthy")
    evidence.add("L3 comprobaciones", checks.take_lines())
    evidence.write()


def run(checks: Checks) -> None:
    """Ejecuta el escenario completo y escribe `faq12_antes_despues.sql/.out`, `prueba2_*` y `prueba3_4_*`."""
    stack.build_images(needs_tests_image=True)
    stack.reset_stack()
    group = stack.consumer_group()
    evidence = Evidence("faq12_antes_despues", "out")
    lecture_1(checks, group, evidence)
    evidence.write()
    evidence_path("faq12_antes_despues", "sql").write_text("\n".join(EVIDENCE_QUERIES) + "\n", encoding=ENCODING, newline="\n")
    lecture_2(checks, group)
    lecture_3(checks, group)
