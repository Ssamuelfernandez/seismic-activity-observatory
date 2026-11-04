"""Escenario `restart` (T076, prueba 8, SC-005): corte entre el commit de PostgreSQL y el del offset.

Primero una ejecución de referencia sin corte; después otra con `CONSUMER_FAULT_CRASH_AT_OFFSET=2`
pasada solo como variable de entorno del proceso de Compose (no se edita ni se muestra el `.env`).
Al final se recrea el contenedor sin la variable.
"""
import hashlib
import re
import time

from scripts.consumer_scenarios import stack
from scripts.consumer_scenarios.helpers import REPO_ROOT, check_crash_sequence
from scripts.consumer_scenarios.report import Checks, Evidence, say

CRASH_OFFSET = 2
EXIT_CODE_KILLED = "137"
MARKER = "/tmp/consumer_fault_done"
LOG_FILTER = re.compile(r"decision=|FAULT|COUNTERS|Consumidor suscrito|catalog loaded|retry |Parada")
SNAPSHOT_QUERIES = (
    "SELECT event_id, event_time_ms, updated_ms, mag, depth_km, lon, lat, place, status, url, sig, mag_type, "
    "country_id, date_id, source, is_synthetic FROM live.current_event ORDER BY event_id;",
    "SELECT event_id, updated_ms, mag, depth_km, source, is_synthetic, kafka_topic, kafka_partition, kafka_offset, "
    "md5(original::text) AS original_md5 FROM live.event_version ORDER BY event_id, updated_ms;",
    "SELECT (SELECT count(*) FROM live.current_event) AS current_rows, "
    "(SELECT count(*) FROM live.event_version) AS version_rows, (SELECT count(*) FROM live.quarantine) AS quarantine_rows;",
    "SELECT event_id, updated_ms, count(*) AS copies FROM live.event_version GROUP BY 1, 2 HAVING count(*) > 1;",
)
EXPECTED_COUNTS = ["2", "3", "0"]


def env_fingerprint() -> str:
    """Huella SHA-256 del `.env` (solo se usa para comprobar que no cambia; no se lee su contenido)."""
    return hashlib.sha256((REPO_ROOT / ".env").read_bytes()).hexdigest()


def sql_snapshot() -> str:
    """Contenido estable de las tablas (sin marcas de tiempo de ingesta) para comparar dos ejecuciones."""
    return "\n\n".join(f"{query}\n{stack.psql_table(query)}" for query in SNAPSHOT_QUERIES)


def reference_run(checks: Checks, evidence: Evidence) -> str:
    """Ejecución sin corte: base limpia, `faq12` y lectura SQL."""
    stack.reset_stack()
    group = stack.consumer_group()
    checks.record(True, "Referencia: publicado faq12", stack.publish("faq12"))
    checks.record(stack.wait_lag_zero(group), "Referencia: el grupo llega a lag 0")
    snapshot = sql_snapshot()
    evidence.add("SQL de la ejecución de referencia, sin corte", snapshot)
    return snapshot


def start_with_fault() -> None:
    """Base limpia y consumidor recreado con la variable del gancho solo en el entorno del proceso."""
    stack.compose("down", "-v")
    stack.compose("up", "-d", "kafka", "postgres")
    stack.compose("up", "-d", "--force-recreate", stack.CONSUMER, env=stack.clean_env(CRASH_OFFSET))
    stack.wait_healthy(stack.CONSUMER)


def exit_codes_since(started_at: int) -> list[str]:
    """Códigos de salida de las muertes del contenedor `consumer` desde `started_at` (eventos de Docker)."""
    until = str(int(time.time()) + 1)
    result = stack.run(["docker", "events", "--since", str(started_at), "--until", until, "--filter", "event=die",
                        "--filter", "label=com.docker.compose.service=consumer"], env=stack.clean_env())
    return re.findall(r"exitCode=(\d+)", result.stdout)


def restart_count() -> str:
    """Número de reinicios automáticos del contenedor del consumidor."""
    container = stack.compose("ps", "-q", stack.CONSUMER).stdout.strip()
    return stack.run(["docker", "inspect", "--format", "{{.RestartCount}}", container]).stdout.strip()


def crash_run(checks: Checks, evidence: Evidence) -> str:
    """Ejecución con corte en el offset 2: publica, espera el reinicio y comprueba el registro."""
    start_with_fault()
    group = stack.consumer_group()
    started_at = int(time.time()) - 1
    checks.record(True, "Con corte: publicado faq12", stack.publish("faq12"))
    checks.record(stack.wait_lag_zero(group), "Con corte: el grupo llega a lag 0 tras el reinicio")
    log = stack.consumer_log()
    problems = check_crash_sequence(log, CRASH_OFFSET)
    checks.record(not problems, f"Registro: FAULT offset={CRASH_OFFSET} y luego decision=redelivery_ignored", "; ".join(problems))
    codes = exit_codes_since(started_at)
    checks.record(codes.count(EXIT_CODE_KILLED) == 1 and len(codes) == 1, "El proceso terminó una sola vez, con código 137", str(codes))
    checks.record(restart_count() == "1", "Compose reinició el contenedor una sola vez (no vuelve a morir)", restart_count())
    marker = stack.compose("exec", "-T", stack.CONSUMER, "ls", MARKER, check=False)
    checks.record(marker.returncode == 0, "El marcador existe en /tmp antes de la recreación final", marker.stdout.strip())
    evidence.add("Registro filtrado del consumidor con corte", "\n".join(line for line in log.splitlines() if LOG_FILTER.search(line)))
    return sql_snapshot()


def compare_runs(checks: Checks, reference: str, crashed: str, evidence: Evidence) -> None:
    """Mismo contenido SQL con y sin corte; 0 duplicados y 0 pérdidas."""
    checks.record(reference == crashed, "El SQL con corte es idéntico al de la ejecución sin corte")
    counts = stack.psql_rows(SNAPSHOT_QUERIES[2])[0]
    checks.record(counts == EXPECTED_COUNTS, "2 actuales, 3 versiones y 0 en cuarentena (0 pérdidas)", str(counts))
    checks.record(stack.psql_rows(SNAPSHOT_QUERIES[3]) == [], "0 versiones duplicadas por (event_id, updated_ms)")
    evidence.add("SQL de la ejecución con corte", crashed)


def final_recreate(checks: Checks, evidence: Evidence) -> None:
    """Recrea el contenedor sin la variable: el marcador desaparece y la variable queda vacía."""
    stack.compose("up", "-d", "--force-recreate", stack.CONSUMER)
    checks.record(stack.wait_healthy(stack.CONSUMER), "Tras recrear sin la variable, el consumidor está healthy")
    probe = stack.compose("exec", "-T", stack.CONSUMER, "sh", "-c", f'echo "[$CONSUMER_FAULT_CRASH_AT_OFFSET]"; ls {MARKER}', check=False)
    shown = f"{probe.stdout.strip()} | {probe.stderr.strip()}"
    checks.record(probe.stdout.strip().startswith("[]") and probe.returncode != 0,
                  "La variable queda vacía [] y el marcador ya no existe", shown)
    evidence.add("Tras la recreación final", shown)


def run(checks: Checks) -> None:
    """Ejecuta el escenario y escribe `prueba8_reinicio.log` y `prueba8_reinicio.out`."""
    stack.build_images(needs_tests_image=True)
    env_before = env_fingerprint()
    evidence, log_evidence = Evidence("prueba8_reinicio", "out"), Evidence("prueba8_reinicio", "log")
    reference = reference_run(checks, evidence)
    crashed = crash_run(checks, log_evidence)
    compare_runs(checks, reference, crashed, evidence)
    final_recreate(checks, evidence)
    env_after = env_fingerprint()
    checks.record(env_before == env_after, ".env sin cambios (huella antes y después)", f"{env_before[:16]} == {env_after[:16]}")
    evidence.add("Comprobaciones", checks.take_lines())
    evidence.write()
    log_evidence.write()
    say(f"Evidencias: {evidence.path.name}, {log_evidence.path.name}")
