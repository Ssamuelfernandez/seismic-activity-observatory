"""Escritura en PostgreSQL: transacción de un evento y fila de cuarentena (C2, C3, C4, C5).

No captura excepciones de contenido (las clasifica el llamador con `is_content_error`) y no
reintenta (los reintentos viven en `consumer/resilience.py`). Todo el SQL está en `queries.py`.
"""
import logging
from typing import Any

from common.processing import decide_version_outcome, is_inconsistent_state
from common.records import EventRows, QuarantineRow, VersionOutcome
from consumer import queries

logger = logging.getLogger(__name__)

INSERT_ONE_ROW_TAG = "INSERT 0 1"
ISOLATION_LEVEL = "read_committed"
WRITES_CURRENT = frozenset({VersionOutcome.NEW_EVENT, VersionOutcome.NEWER_VERSION})


def _row_values(row: dict, columns: tuple[str, ...]) -> tuple:
    """Valores de un diccionario de fila en el orden de columnas de la sentencia."""
    return tuple(row[column] for column in columns)


async def _insert_version(conn: Any, rows: EventRows, mode: str) -> bool:
    """Inserta la versión y dice si es nueva, leyendo la etiqueta de estado de la sentencia."""
    tag = await conn.execute(queries.event_version_insert(mode), *_row_values(rows.version, queries.VERSION_COLUMNS))
    return tag == INSERT_ONE_ROW_TAG


async def _content_differs(conn: Any, rows: EventRows, mode: str) -> bool:
    """Compara (jsonb) el `original` guardado con el recibido para la misma versión."""
    event_id, updated_ms = rows.version["event_id"], rows.version["updated_ms"]
    return bool(await conn.fetchval(queries.version_content_differs(mode), rows.original, event_id, updated_ms))


async def _write_event_steps(conn: Any, rows: EventRows, mode: str) -> VersionOutcome:
    """Pasos 1 a 6 de plan §4 dentro de la transacción ya abierta."""
    date = rows.date
    await conn.execute(queries.DATE_DIM_INSERT, date.date_id, date.year, date.month, date.day, date.dow)
    event_id, incoming = rows.version["event_id"], rows.version["updated_ms"]
    stored = await conn.fetchval(queries.select_stored_updated(mode), event_id)
    inserted = await _insert_version(conn, rows, mode)
    differs = False if inserted else await _content_differs(conn, rows, mode)
    if is_inconsistent_state(stored, incoming, inserted):
        logger.warning("inconsistent_state event_id=%s", event_id)
    outcome = decide_version_outcome(stored, incoming, inserted, differs)
    if outcome in WRITES_CURRENT:
        await conn.execute(queries.current_event_upsert(mode), *_row_values(rows.current, queries.CURRENT_COLUMNS))
    return outcome


async def write_event(conn: Any, rows: EventRows, mode: str) -> VersionOutcome:
    """Escribe un evento válido en una única transacción `READ COMMITTED`.

    Qué hace:
        `date_dim` -> estado previo con `FOR UPDATE` -> versión (`ON CONFLICT DO NOTHING`) ->
        comparación jsonb si no era nueva -> decisión -> `current_event` solo si es nuevo o más
        reciente. La salida del bloque es el COMMIT, que puede lanzar por la FK diferida.
    Recibe:
        conn: conexión de `asyncpg` del rol del consumidor; rows: filas de `build_event_rows`;
        mode: `live` o `replay` (el esquema sale de una lista cerrada).
    Devuelve:
        El VersionOutcome de la versión; registra un WARNING si el estado es inconsistente.
    Por qué existe:
        Garantiza idempotencia y que una versión antigua nunca pise a la reciente
        (C2, C3, C4, FR-005, FR-009, FR-010).
    """
    async with conn.transaction(isolation=ISOLATION_LEVEL):
        return await _write_event_steps(conn, rows, mode)


async def write_quarantine(conn: Any, row: QuarantineRow, mode: str) -> bool:
    """Guarda una fila de cuarentena sin leer la tabla (el rol no tiene `SELECT`).

    Qué hace:
        Ejecuta `INSERT ... ON CONFLICT DO NOTHING` sin destino ni `RETURNING` y lee la
        etiqueta de estado.
    Recibe:
        conn: conexión del rol del consumidor; row: fila saneada; mode: `live` o `replay`.
    Devuelve:
        True si la fila es nueva (`INSERT 0 1`); False si era un duplicado (`INSERT 0 0`).
    Por qué existe:
        Idempotencia de la cuarentena por (hash, motivo) con permisos mínimos (C5, FR-012, FR-027).
    """
    values = (
        row.event_id, row.reason, row.original, row.raw_text, row.original_sha256, row.source,
        row.kafka_topic, row.kafka_partition, row.kafka_offset, row.received_at, row.is_synthetic,
    )
    tag = await conn.execute(queries.quarantine_insert(mode), *values)
    return tag == INSERT_ONE_ROW_TAG
