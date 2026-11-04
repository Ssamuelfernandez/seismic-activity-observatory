"""Escenario `quarantine` (T075, prueba 6, quickstart §6 y §7): cuarentena con Kafka real.

Publica el caso `quarantine-set` (latitud 145, un válido, NUL en `place`, bytes no UTF-8, tombstone,
`mode = replay` en el tema `live` y un id de 600 caracteres) y lee `live.quarantine` con el administrador.
"""
import re

from scripts.consumer_scenarios import stack
from scripts.consumer_scenarios.report import Checks, Evidence

TOPIC = "earthquakes.live"
VALID_ID = "synthetic-quarantine-valid"
QUARANTINE_SQL = (
    "SELECT id, reason, event_id, source, is_synthetic, kafka_topic, kafka_partition, kafka_offset, "
    "left(original_sha256, 12) AS sha, original IS NOT NULL AS has_json, left(raw_text, 40) AS raw "
    "FROM live.quarantine ORDER BY id;"
)
ROWS_SQL = ("SELECT kafka_offset, reason, coalesce(event_id, ''), is_synthetic, kafka_topic, kafka_partition, "
            "original_sha256 FROM live.quarantine ORDER BY kafka_offset")
# offset -> (motivo, ¿el sobre es legible y por tanto hereda `is_synthetic = true`?)
EXPECTED = {
    0: ("coordinates_out_of_range", True), 2: ("db_constraint_violation", True), 3: ("invalid_json", False),
    4: ("invalid_json", False), 5: ("mode_topic_mismatch", True), 6: ("value_out_of_range", True),
}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def check_rows(checks: Checks) -> None:
    """Una fila por mensaje inválido, con motivo, referencia Kafka y SHA-256 de 64 hex."""
    rows = {int(r[0]): r for r in stack.psql_rows(ROWS_SQL)}
    checks.record(set(rows) == set(EXPECTED) and len(rows) == len(EXPECTED),
                  "1 fila de cuarentena por mensaje inválido (6) y ninguna para el válido", str(sorted(rows)))
    for offset, (reason, readable) in EXPECTED.items():
        row = rows.get(offset, [""] * 7)
        ok = (row[1] == reason and row[4] == TOPIC and row[5] == "0" and bool(SHA256_PATTERN.fullmatch(row[6]))
              and (row[3] == "t") is readable)
        checks.record(ok, f"offset {offset}: motivo {reason}, tema, partición 0 y SHA-256 de 64 hex",
                      f"reason={row[1]} topic={row[4]} partition={row[5]} is_synthetic={row[3]}")


def check_current_event(checks: Checks) -> None:
    """El válido (offset 1) está guardado; ningún inválido llegó a `current_event` ni a `event_version`."""
    ids = [r[0] for r in stack.psql_rows("SELECT event_id FROM live.current_event ORDER BY 1")]
    checks.record(ids == [VALID_ID], "current_event contiene solo el mensaje válido", str(ids))
    versions = stack.psql_scalar("SELECT count(*) FROM live.event_version")
    checks.record(versions == "1", "event_version contiene 1 fila (la del válido)", versions)
    flags = stack.psql_rows("SELECT DISTINCT is_synthetic FROM live.current_event")
    checks.record(flags == [["t"]], "is_synthetic = true en las filas guardadas", str(flags))


def run(checks: Checks) -> None:
    """Ejecuta el escenario y escribe `prueba6_cuarentena.out`."""
    stack.build_images(needs_tests_image=True)
    stack.reset_stack()
    group = stack.consumer_group()
    evidence = Evidence("prueba6_cuarentena", "out")
    checks.record(True, "Publicado el caso quarantine-set", stack.publish("quarantine-set"))
    checks.record(stack.wait_lag_zero(group), "El grupo llega a lag 0 tras quarantine-set")
    evidence.add("live.quarantine leída con el administrador (versión Kafka real)", f"{QUARANTINE_SQL}\n{stack.psql_table(QUARANTINE_SQL)}")
    check_rows(checks)
    check_current_event(checks)
    checks.record(stack.service_health(stack.CONSUMER) == "healthy", "El consumidor sigue healthy")
    evidence.add("Comprobaciones", checks.take_lines())
    evidence.write()
