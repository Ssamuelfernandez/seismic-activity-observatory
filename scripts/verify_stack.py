"""Verificación de punta a punta de infra-compose (criterios de aceptación A1–A12).

Requiere el sistema levantado (`docker compose up --build -d`) y solo usa la biblioteca estándar.
Uso:
    python scripts/verify_stack.py                  # todas las comprobaciones
    python scripts/verify_stack.py --skip-restart   # sin la prueba de persistencia (no detiene nada)

Cada comprobación imprime PASS o FAIL; el código de salida es 0 solo si todas pasan.
La prueba de persistencia crea la tabla public.zz_infra_check, la elimina al terminar y no toca
ninguna tabla del contrato.
"""
import argparse
import json
import socket
import subprocess
import sys
import time
import uuid

SERVICES = ("kafka", "postgres", "producer", "consumer", "api")
HEALTHY_TIMEOUT_SECONDS = 240
EVENT_TIMEOUT_SECONDS = 60  # SC-003: el evento debe verse en menos de 60 s
HOST_PORTS_THAT_MUST_BE_CLOSED = {"kafka": 9092, "postgres": 5432}
EXPECTED_TOPICS = ("earthquakes.live", "earthquakes.replay")
EXPECTED_RETENTION_MS = "604800000"
CHECK_TABLE = "public.zz_infra_check"

# Permisos de escritura esperados por rol (db-schema.md §1.1); todo lo demás debe estar denegado.
WRITE_TABLES = {
    "observatory_api": set(),
    "observatory_producer": {
        "live.exclusion", "replay.exclusion", "ingest.ingest_state", "ingest.ingest_run", "ingest.raw_response",
    },
    "observatory_consumer": {
        "public.country", "public.date_dim", "live.current_event", "replay.current_event",
        "live.event_version", "replay.event_version", "live.quarantine", "replay.quarantine",
    },
}
API_READ_TABLES = ("live.current_event", "replay.current_event", "public.country", "ingest.ingest_run")

results: list[tuple[bool, str]] = []


def record(passed: bool, name: str, detail: str = "") -> None:
    """Registra e imprime el resultado de una comprobación."""
    results.append((passed, name))
    print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""), flush=True)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta un comando y devuelve su salida como texto."""
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=check)


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta `docker compose` con los argumentos dados."""
    return run(["docker", "compose", *args], check=check)


def psql(sql: str) -> str:
    """Ejecuta SQL con el administrador dentro del contenedor de PostgreSQL."""
    command = f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -v ON_ERROR_STOP=1 -c "{sql}"'
    return compose("exec", "-T", "postgres", "sh", "-c", command).stdout.strip()


def service_states() -> dict[str, str]:
    """Devuelve el estado de salud de cada servicio según `docker compose ps`."""
    output = compose("ps", "--all", "--format", "json").stdout
    rows = [json.loads(line) for line in output.splitlines() if line.strip()]
    return {row["Service"]: row.get("Health") or row.get("State", "") for row in rows}


def wait_all_healthy(timeout: int) -> bool:
    """Espera hasta que los cinco servicios estén saludables."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        states = service_states()
        if all(states.get(name) == "healthy" for name in SERVICES):
            return True
        time.sleep(5)
    return False


def check_healthy() -> None:
    """A1, A4: los cinco servicios están saludables."""
    ok = wait_all_healthy(HEALTHY_TIMEOUT_SECONDS)
    record(ok, "Los cinco servicios están healthy", str(service_states()))


def is_synthetic_decision_line(entry: str) -> bool:
    """Indica si una línea del registro es la decisión del consumidor sobre un evento sintético.

    Qué hace:
        Busca `decision=` y `event_id=synthetic-` (consumer-runtime.md §4), sin exigir ningún marcador de texto.
    Recibe:
        entry: una línea del registro del consumidor.
    Devuelve:
        True si la línea es una decisión sobre un evento `synthetic-…`.
    Por qué existe:
        El consumidor idempotente ya no escribe la antigua línea «Evento recibido» (A1, FR-003).
    """
    return "decision=" in entry and "event_id=synthetic-" in entry


def check_synthetic_event_in_consumer_log() -> None:
    """A1: el consumidor deja la línea de decisión de un evento sintético del productor.

    Qué hace:
        Espera hasta `EVENT_TIMEOUT_SECONDS` una línea `decision=… event_id=synthetic-…`.
    Por qué existe:
        Comprueba el recorrido productor -> Kafka -> consumidor. Cualquier decisión sirve, también
        `decision=quarantined …` si el evento se rechazara.
    Limitación:
        El grupo del consumidor conserva su offset tras `down`/`up`, así que ya no relee el tema desde
        el principio: A1 depende de que el productor publique un evento NUEVO dentro de 60 s. Si
        `PRODUCER_INTERVAL_SECONDS` (admite hasta 60) es largo, el check puede fallar por tiempo sin
        que haya un error real.
    """
    deadline = time.time() + EVENT_TIMEOUT_SECONDS
    line = ""
    while time.time() < deadline and not line:
        logs = compose("logs", "consumer", "--no-log-prefix").stdout
        line = next((entry for entry in logs.splitlines() if is_synthetic_decision_line(entry)), "")
        if not line:
            time.sleep(3)
    record(bool(line), "El consumidor registra la decisión sobre un evento sintético", line.strip())


def check_api_health_endpoint() -> None:
    """A9, FR-014: GET /api/salud responde ok desde el equipo anfitrión."""
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/salud", timeout=5) as response:
            body = json.loads(response.read())
        record(response.status == 200 and body.get("status") == "ok" and "generated" in body,
               "GET /api/salud en 127.0.0.1:8000", json.dumps(body))
    except OSError as error:
        record(False, "GET /api/salud en 127.0.0.1:8000", str(error))


def check_only_api_is_published() -> None:
    """A8: solo la API publica puertos, y Kafka y PostgreSQL no aceptan conexiones desde el equipo."""
    output = compose("ps", "--format", "json").stdout
    rows = [json.loads(line) for line in output.splitlines() if line.strip()]
    published = {row["Service"]: [(p["URL"], p["PublishedPort"]) for p in row.get("Publishers", []) if p.get("PublishedPort")]
                 for row in rows}
    only_api = {service: ports for service, ports in published.items() if ports} == {"api": [("127.0.0.1", 8000)]}
    record(only_api, "Solo la API publica un puerto, en 127.0.0.1:8000", str({k: v for k, v in published.items() if v}))
    for service, port in HOST_PORTS_THAT_MUST_BE_CLOSED.items():
        container = compose("ps", "-q", service).stdout.strip()
        bindings = json.loads(run(["docker", "inspect", "--format", "{{json .HostConfig.PortBindings}}", container]).stdout)
        record(not bindings, f"{service} no tiene puertos enlazados al equipo", str(bindings or "sin enlaces"))
        with socket.socket() as sock:
            sock.settimeout(2)
            answers = sock.connect_ex(("127.0.0.1", port)) == 0
        if answers:
            # No es un fallo de Compose: el puerto lo atiende otro proceso del equipo (p. ej. un PostgreSQL local).
            print(f"INFO  el puerto {port} del equipo responde, pero Compose no publica ninguno: lo atiende otro proceso local")


def check_topics() -> None:
    """A6, FR-016: los temas del contrato tienen 1 partición, factor 1 y retención de 7 días."""
    for topic in EXPECTED_TOPICS:
        out = compose("exec", "-T", "kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "kafka:9092",
                      "--describe", "--topic", topic, check=False).stdout
        ok = ("PartitionCount: 1" in out and "ReplicationFactor: 1" in out
              and f"retention.ms={EXPECTED_RETENTION_MS}" in out)
        record(ok, f"Tema {topic}: 1 partición, factor 1, retención 7 días", out.splitlines()[0] if out else "sin salida")


def check_role_privileges() -> None:
    """FR-027, FR-028: cada rol tiene exactamente los permisos de escritura del contrato."""
    tables = psql("SELECT schemaname || '.' || tablename FROM pg_tables "
                  "WHERE schemaname IN ('public','live','replay','ingest') AND tablename <> 'zz_infra_check' "
                  "ORDER BY 1").splitlines()
    for role, allowed in WRITE_TABLES.items():
        wrong = []
        for table in tables:
            can_write = psql(f"SELECT has_table_privilege('{role}', '{table}', 'INSERT') "
                             f"OR has_table_privilege('{role}', '{table}', 'UPDATE') "
                             f"OR has_table_privilege('{role}', '{table}', 'DELETE')") == "t"
            if can_write != (table in allowed):
                wrong.append(table)
        record(not wrong, f"Rol {role}: permisos de escritura según el contrato", f"discrepancias: {wrong}" if wrong else "")
    can_read = [psql(f"SELECT has_table_privilege('observatory_api', '{t}', 'SELECT')") == "t" for t in API_READ_TABLES]
    record(all(can_read), "Rol observatory_api: puede leer current_event, country e ingest_run")


def check_api_write_is_rejected() -> None:
    """SC-006: la cuenta real de la API es rechazada al escribir."""
    code = ("import asyncio, asyncpg\n"
            "from common.config import load_database_settings\n"
            "from common.db import connect\n"
            "async def main():\n"
            "    c = await connect(load_database_settings())\n"
            "    try:\n"
            "        await c.execute(\"INSERT INTO ingest.ingest_run (run_at, url) VALUES (now(), 'x')\")\n"
            "        print('WRITE_ALLOWED')\n"
            "    except asyncpg.InsufficientPrivilegeError:\n"
            "        print('WRITE_DENIED')\n"
            "asyncio.run(main())\n")
    out = compose("exec", "-T", "api", "python", "-c", code, check=False).stdout.strip()
    record(out == "WRITE_DENIED", "La cuenta de la API no puede escribir (INSERT rechazado)", out)


def check_persistence_after_restart() -> None:
    """A5: un dato sobrevive a detener y volver a arrancar los contenedores sin borrar volúmenes."""
    token = uuid.uuid4().hex
    psql(f"DROP TABLE IF EXISTS {CHECK_TABLE}; CREATE TABLE {CHECK_TABLE} (token text); "
         f"INSERT INTO {CHECK_TABLE} VALUES ('{token}')")
    compose("down")
    compose("up", "-d")
    healthy = wait_all_healthy(HEALTHY_TIMEOUT_SECONDS)
    record(healthy, "Tras reiniciar, los cinco servicios vuelven a estar healthy")
    try:
        found = psql(f"SELECT token FROM {CHECK_TABLE}")
        record(found == token, "PostgreSQL conserva el dato tras reiniciar los contenedores")
    finally:
        psql(f"DROP TABLE IF EXISTS {CHECK_TABLE}")


def main() -> int:
    """Ejecuta las comprobaciones y devuelve el código de salida."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-restart", action="store_true", help="omite la prueba de persistencia")
    args = parser.parse_args()
    check_healthy()
    check_synthetic_event_in_consumer_log()
    check_api_health_endpoint()
    check_only_api_is_published()
    check_topics()
    check_role_privileges()
    check_api_write_is_rejected()
    if not args.skip_restart:
        check_persistence_after_restart()
        check_synthetic_event_in_consumer_log()
    failed = [name for passed, name in results if not passed]
    print(f"\n{len(results) - len(failed)}/{len(results)} comprobaciones superadas.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
