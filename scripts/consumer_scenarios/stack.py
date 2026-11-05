"""Operaciones con Docker Compose, PostgreSQL y Kafka de los escenarios de `verify_consumer.py`.

Solo usa la biblioteca estándar. No lee ni muestra el `.env`: Compose lo interpola por su cuenta.
`print` está permitido (script de línea de comandos, CC-DOC).
"""
import json
import os
import subprocess
import time
from collections.abc import Mapping

from scripts.consumer_scenarios.helpers import REPO_ROOT, parse_group_lag

CONSUMER = "consumer"
FAULT_VARIABLE = "CONSUMER_FAULT_CRASH_AT_OFFSET"
HEALTHY_TIMEOUT_SECONDS = 240
LAG_TIMEOUT_SECONDS = 120
POLL_SECONDS = 2
PSQL = 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -X -v ON_ERROR_STOP=1'
KAFKA_GROUPS = "/opt/kafka/bin/kafka-consumer-groups.sh"
PUBLISH_MODULE = "tests.support.publish_messages"


def run(args: list[str], env: Mapping[str, str] | None = None, input_text: str | None = None,
        check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta un comando en la raíz del repositorio y devuelve su salida como texto UTF-8."""
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          input=input_text, env=dict(env) if env is not None else None, cwd=REPO_ROOT, check=check)


def clean_env(fault_offset: int | None = None) -> dict[str, str]:
    """Entorno del proceso para Compose: sin `CONSUMER_FAULT_CRASH_AT_OFFSET` salvo que se pida."""
    env = {key: value for key, value in os.environ.items() if key != FAULT_VARIABLE}
    env["MSYS_NO_PATHCONV"] = "1"
    if fault_offset is not None:
        env[FAULT_VARIABLE] = str(fault_offset)
    return env


def compose(*args: str, env: Mapping[str, str] | None = None, input_text: str | None = None,
            check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta `docker compose` con el entorno limpio por defecto (la variable del gancho nunca se hereda)."""
    return run(["docker", "compose", *args], env=clean_env() if env is None else env, input_text=input_text,
               check=check)


def build_images(needs_tests_image: bool) -> None:
    """Primer paso de todo escenario: imagen compartida al día y, si se publica, la del servicio `tests`."""
    compose("build", "producer")
    if needs_tests_image:
        compose("--profile", "test", "build", "tests")


def reset_stack() -> None:
    """`down -v` y arranque de Kafka, PostgreSQL y consumidor, sin productor. Borra volúmenes locales."""
    compose("down", "-v")
    compose("up", "-d", "kafka", "postgres", CONSUMER)
    wait_healthy(CONSUMER)


def service_health(service: str) -> str:
    """Estado de salud (o de ejecución) de un servicio según `docker compose ps`."""
    output = compose("ps", "--all", "--format", "json", service).stdout
    rows = [json.loads(line) for line in output.splitlines() if line.strip()]
    return (rows[0].get("Health") or rows[0].get("State", "")) if rows else ""


def wait_healthy(service: str, timeout: int = HEALTHY_TIMEOUT_SECONDS) -> bool:
    """Espera a que el servicio esté `healthy`; devuelve False si se agota el tiempo."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if service_health(service) == "healthy":
            return True
        time.sleep(POLL_SECONDS)
    return False


def psql_table(sql: str) -> str:
    """Resultado de una consulta como tabla de texto alineada, con el administrador de la base."""
    return compose("exec", "-T", "postgres", "sh", "-c", PSQL, input_text=sql).stdout.rstrip()


def psql_rows(sql: str) -> list[list[str]]:
    """Resultado de una consulta como filas de texto (separador `|`, sin cabecera)."""
    output = compose("exec", "-T", "postgres", "sh", "-c", f"{PSQL} -tA -F '|'", input_text=sql).stdout
    return [line.split("|") for line in output.splitlines() if line.strip()]


def psql_scalar(sql: str) -> str:
    """Primer valor de una consulta de una sola columna y una sola fila."""
    return psql_rows(sql)[0][0]


def publish(case: str) -> str:
    """Publica un caso de `tests/support/publish_messages.py` desde el servicio `tests`."""
    result = compose("--profile", "test", "run", "--rm", "-T", "tests", "python", "-m", PUBLISH_MODULE, case)
    return result.stdout.strip()


def consumer_group() -> str:
    """Grupo del consumidor (`KAFKA_GROUP_ID` del propio contenedor; no es secreto)."""
    return compose("exec", "-T", CONSUMER, "printenv", "KAFKA_GROUP_ID").stdout.strip()


def group_lag(group: str) -> int | None:
    """Lag actual del grupo según `kafka-consumer-groups`; None si aún no hay offsets confirmados."""
    result = compose("exec", "-T", "kafka", KAFKA_GROUPS, "--bootstrap-server", "kafka:9092", "--describe",
                     "--group", group, check=False)
    return parse_group_lag(result.stdout)


def wait_lag_zero(group: str, timeout: int = LAG_TIMEOUT_SECONDS) -> bool:
    """Espera a que el grupo tenga lag 0 (todo lo publicado está guardado y confirmado)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if group_lag(group) == 0:
            return True
        time.sleep(POLL_SECONDS)
    return False


def consumer_log() -> str:
    """Registro completo del consumidor sin prefijo de servicio."""
    return compose("logs", CONSUMER, "--no-log-prefix").stdout


def stop_consumer() -> None:
    """`docker compose stop consumer` (SIGTERM): el consumidor escribe su `COUNTERS` final."""
    compose("stop", CONSUMER)


def restart_consumer() -> bool:
    """`docker compose restart consumer` (parada limpia y arranque) y espera a que vuelva a estar sano."""
    compose("restart", CONSUMER)
    return wait_healthy(CONSUMER)


def start_consumer() -> bool:
    """`docker compose start consumer` y espera a que vuelva a estar sano."""
    compose("start", CONSUMER)
    return wait_healthy(CONSUMER)
