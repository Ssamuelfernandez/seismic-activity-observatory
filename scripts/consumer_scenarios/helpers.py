"""Auxiliares puros de `scripts/verify_consumer.py`: sin Docker ni red (T071, T073).

Lo que toca Docker vive en `stack.py`; aquí solo hay lectura de texto, comparaciones y rutas.
"""
import json
import re
from pathlib import Path
from typing import Any, Mapping

from consumer.counters import check_identities

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "docs" / "evidencias" / "consumidor-idempotente"
GEO_EVIDENCE_DIR = REPO_ROOT / "docs" / "evidencias" / "geografia-pais"
CONFIRM_VARIABLE = "VERIFY_CONSUMER_CONFIRM"
CONFIRM_VALUE = "yes"
COUNTERS_PATTERN = re.compile(r"COUNTERS (\{.*\})\s*$")
LAG_COLUMN = "LAG"
NO_VALUE = "-"


class CountersNotFound(ValueError):
    """El registro no contiene ninguna línea `COUNTERS {...}`."""


def extract_last_counters(log_text: str) -> dict:
    """Devuelve el diccionario de la última línea `COUNTERS {...}` de un registro.

    Qué hace:
        Recorre el texto línea a línea y se queda con la última que casa.
    Recibe:
        log_text: salida de `docker compose logs consumer`.
    Devuelve:
        Los contadores como diccionario.
    Por qué existe:
        Los contadores solo viven en memoria; el volcado final del registro es su única salida (C8).
    Lanza:
        CountersNotFound si no hay ninguna línea de contadores.
    """
    found = None
    for line in log_text.splitlines():
        match = COUNTERS_PATTERN.search(line)
        if match:
            found = match.group(1)
    if found is None:
        raise CountersNotFound("El registro no contiene ninguna línea COUNTERS {...}.")
    return json.loads(found)


def compare_counters(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> list[str]:
    """Compara las claves esperadas con las reales y devuelve las diferencias (vacía = coincide)."""
    problems = []
    for key, value in expected.items():
        if key not in actual:
            problems.append(f"falta el contador {key}")
        elif actual[key] != value:
            problems.append(f"{key}: real={actual[key]!r} esperado={value!r}")
    return problems


def compare_with_sql(counters: Mapping[str, Any], current_rows: int,
                     quarantine_by_reason: Mapping[str, int]) -> list[str]:
    """Concilia los contadores de una sesión con las cifras SQL y con las identidades de FR-023.

    Qué hace:
        Aplica `check_identities`; compara `new_events` con las filas de `current_event` y
        `quarantined[motivo]` con el recuento SQL por motivo (identidad 3 de data-model §4).
    Recibe:
        counters: diccionario de la línea `COUNTERS`; current_rows: `count(*)` de `current_event`;
        quarantine_by_reason: `count(*)` por motivo de la cuarentena.
    Devuelve:
        Lista de discrepancias; vacía si todo cuadra. Solo válida con base y grupo limpios.
    Por qué existe:
        SC-009: un contador manipulado o perdido no debe pasar inadvertido.
    """
    problems = list(check_identities(dict(counters)))
    if counters["new_events"] != current_rows:
        problems.append(f"new_events={counters['new_events']} != filas de current_event={current_rows}")
    for reason in sorted(set(counters["quarantined"]) | set(quarantine_by_reason)):
        counted, stored = counters["quarantined"].get(reason, 0), quarantine_by_reason.get(reason, 0)
        if counted != stored:
            problems.append(f"quarantined[{reason}]={counted} != filas SQL={stored}")
    return problems


def parse_group_lag(describe_output: str) -> int | None:
    """Calcula el *lag* del grupo a partir de la salida de `kafka-consumer-groups --describe`.

    Qué hace:
        Localiza la columna `LAG` por su cabecera y suma las filas.
    Recibe:
        describe_output: salida de texto del comando.
    Devuelve:
        El lag total; None si no hay filas o el grupo aún no ha confirmado ningún offset (`-`).
    Por qué existe:
        Los escenarios esperan a lag 0 antes de leer SQL: con lag 0 todo offset confirmado ya se guardó.
    """
    lines = [line.split() for line in describe_output.splitlines() if line.strip()]
    header = next((cells for cells in lines if LAG_COLUMN in cells), None)
    if header is None:
        return None
    index = header.index(LAG_COLUMN)
    rows = [cells for cells in lines[lines.index(header) + 1:] if len(cells) > index]
    values = [cells[index] for cells in rows]
    if not values or NO_VALUE in values:
        return None
    return sum(int(value) for value in values)


def check_crash_sequence(log_text: str, offset: int) -> list[str]:
    """Comprueba en el registro la secuencia de la prueba 8 para el offset del corte.

    Qué hace:
        Exige una sola línea `FAULT crash_after_db_commit offset=N`, ninguna decisión de ese
        offset antes de ella y una `decision=redelivery_ignored` de ese offset después.
    Recibe:
        log_text: registro del consumidor; offset: offset del corte.
    Devuelve:
        Lista de incumplimientos; vacía si la secuencia es la esperada.
    Por qué existe:
        SC-005: demuestra que el corte cayó entre ambos commits y que la reentrega no duplicó nada.
    """
    lines = log_text.splitlines()
    faults = [i for i, line in enumerate(lines) if f"FAULT crash_after_db_commit offset={offset}" in line]
    if len(faults) != 1:
        return [f"líneas FAULT del offset {offset}: {len(faults)} (se esperaba 1)"]
    decision = re.compile(rf"decision=\S+.*\boffset={offset}\b")
    before = [line for line in lines[:faults[0]] if decision.search(line)]
    after = [line for line in lines[faults[0] + 1:]
             if decision.search(line) and "decision=redelivery_ignored" in line]
    problems = [f"hay decisión del offset {offset} antes del FAULT"] if before else []
    return problems + ([] if after else [f"no hay decision=redelivery_ignored del offset {offset} tras el FAULT"])


def evidence_path(name: str, extension: str, directory: Path = EVIDENCE_DIR) -> Path:
    """Ruta de un archivo de evidencia (por defecto en `docs/evidencias/consumidor-idempotente/`)."""
    return directory / f"{name}.{extension}"


def confirm_destructive(args: Any, env: Mapping[str, str]) -> bool:
    """True solo con el flag `--yes` o con `VERIFY_CONSUMER_CONFIRM=yes` (exacto); si no, False.

    Por qué existe:
        `down -v` borra los volúmenes locales de Kafka y PostgreSQL: nunca debe ejecutarse por defecto.
    """
    return bool(getattr(args, "yes", False)) or env.get(CONFIRM_VARIABLE) == CONFIRM_VALUE
