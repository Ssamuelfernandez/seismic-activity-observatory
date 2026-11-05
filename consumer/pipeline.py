"""Procesamiento de un mensaje: decodificar, validar, transformar y escribir (C1, C2, C3, C5).

`process_record` no confirma offsets, no toca contadores y no escribe la línea de decisión: eso
lo hace el bucle (plan §1, pasos 7 a 9). Termina en el gancho `after_db_commit`.
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import asyncpg

from common.decode import decode_value
from common.geo import CountryMatch
from common.kafka_topics import topic_mode
from common.quarantine_row import build_quarantine_row
from common.records import (
    DecodeResult, EventRows, MessageRef, ProcessingResult, QuarantineRow, RawRecord, Rejection,
    ResultKind, ValidEvent, VersionOutcome,
)
from common.transform import build_event_rows
from common.validation import DB_CONSTRAINT_VIOLATION, validate_message
from consumer import writer
from consumer.db_errors import is_content_error
from consumer.fault_hook import AfterDbCommit
from consumer.resilience import OpContext, RetryControl, retry_db_operation

logger = logging.getLogger(__name__)

NO_VALUE = "-"
OP_WRITE_EVENT = "write_event"
OP_WRITE_QUARANTINE = "write_quarantine"
CONTENT_ERROR_TYPES = (asyncpg.PostgresError, UnicodeError)

EventWriter = Callable[[EventRows, str], Awaitable[VersionOutcome]]
QuarantineWriter = Callable[[QuarantineRow, str], Awaitable[bool]]


def utc_now() -> datetime:
    """Reloj del consumidor (UTC); se inyecta en las pruebas."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PipelineDeps:
    """Dependencias de `process_record`: escritores, reintento, localizador de país, reloj y gancho."""

    write_event: EventWriter
    write_quarantine: QuarantineWriter
    control: RetryControl
    locate: Callable[[float, float], CountryMatch]
    clock: Callable[[], datetime] = utc_now
    after_db_commit: AfterDbCommit | None = None


def bind_pool_writers(pool: Any) -> tuple[EventWriter, QuarantineWriter]:
    """Devuelve los escritores de `writer.py` ligados a un pool de `asyncpg`.

    Cada escritura toma una conexión del pool: si la base cae, el reintento pide otra.
    """
    async def write_event(rows: EventRows, mode: str) -> VersionOutcome:
        async with pool.acquire() as conn:
            return await writer.write_event(conn, rows, mode)

    async def write_quarantine(row: QuarantineRow, mode: str) -> bool:
        async with pool.acquire() as conn:
            return await writer.write_quarantine(conn, row, mode)

    return write_event, write_quarantine


def _finish(result: ProcessingResult, deps: PipelineDeps) -> ProcessingResult:
    """Invoca el gancho de prueba tras el commit de PostgreSQL y devuelve el resultado."""
    if deps.after_db_commit is not None:
        deps.after_db_commit(result.ref, result.is_synthetic)
    return result


async def _quarantine(decoded: DecodeResult, reason: str, ref: MessageRef, deps: PipelineDeps) -> ProcessingResult:
    """Escribe la fila de cuarentena (con reintento, sin recursión) y arma el resultado."""
    row = build_quarantine_row(decoded, reason, ref, deps.clock())
    context = OpContext(OP_WRITE_QUARANTINE, row.event_id, ref)
    mode = topic_mode(ref.topic)
    inserted = await retry_db_operation(lambda: deps.write_quarantine(row, mode), context, deps.control,
                                        retry_content=True)
    # `db_constraint_violation` ya superó la validación del contrato: su conversión cuenta (FR-023).
    return ProcessingResult(ResultKind.QUARANTINE, ref, reason=reason, inserted=inserted,
                            converted=reason == DB_CONSTRAINT_VIOLATION, event_id=row.event_id,
                            is_synthetic=row.is_synthetic)


def _log_validation_gap(valid: ValidEvent, ref: MessageRef, error: BaseException) -> None:
    """Un error de clase 22/23 llegó a la base: la validación previa tiene un hueco (consumer-runtime §4)."""
    logger.error("validation_gap event_id=%s sqlstate=%s topic=%s partition=%d offset=%d error=%s",
                 valid.event_id, getattr(error, "sqlstate", None) or NO_VALUE, ref.topic, ref.partition,
                 ref.offset, type(error).__name__)


def _locate_country(valid: ValidEvent, deps: PipelineDeps) -> str | None:
    """Asigna el país por geometría (nunca por `place`) y anota los empates (C11)."""
    match = deps.locate(valid.lon, valid.lat)
    if len(match.candidates) > 1:
        logger.info("country_tie event_id=%s candidates=%s chosen=%s", valid.event_id,
                    ",".join(match.candidates), match.country_id)
    return match.country_id


async def _write_valid(valid: ValidEvent, decoded: DecodeResult, ref: MessageRef,
                       deps: PipelineDeps) -> ProcessingResult:
    """Transforma y escribe un evento válido; un error de contenido de la base va a cuarentena."""
    rows = build_event_rows(valid, ref, deps.clock(), _locate_country(valid, deps))
    context = OpContext(OP_WRITE_EVENT, valid.event_id, ref)
    mode = topic_mode(ref.topic)
    try:
        outcome = await retry_db_operation(lambda: deps.write_event(rows, mode), context, deps.control)
    except CONTENT_ERROR_TYPES as error:
        if not is_content_error(error):
            raise
        _log_validation_gap(valid, ref, error)
        return await _quarantine(decoded, DB_CONSTRAINT_VIOLATION, ref, deps)
    return ProcessingResult(ResultKind.EVENT, ref, outcome=outcome, converted=True, nulls=rows.nulls,
                            event_id=valid.event_id, is_synthetic=valid.is_synthetic, updated_ms=valid.updated_ms)


async def process_record(record: RawRecord, deps: PipelineDeps) -> ProcessingResult:
    """Procesa un mensaje de Kafka hasta dejarlo guardado en PostgreSQL.

    Qué hace:
        Decodifica, valida y, si es válido, asigna el país por geometría, transforma (ms a UTC) y escribe el evento en una
        transacción; si no, escribe una fila de cuarentena. Las escrituras se reintentan sin
        límite ante fallos de la base; un error de contenido de la base manda el mensaje a
        cuarentena como `db_constraint_violation`. Después invoca `after_db_commit`.
    Recibe:
        record: mensaje leído de Kafka; deps: escritores, reintentos, localizador, reloj y gancho.
    Devuelve:
        ProcessingResult con el destino, el resultado de la versión y los datos del registro.
        Si la escritura no puede completarse no devuelve nada (el bucle no avanza).
    Por qué existe:
        Separa la decisión y la escritura de un mensaje de Kafka y de los contadores, de modo
        que el offset solo se confirme después de este commit (C1, C2, C3, C5, constitución §1).
    """
    ref = record.ref
    decoded = decode_value(record.value)
    verdict = validate_message(decoded, record.topic)
    if isinstance(verdict, Rejection):
        result = await _quarantine(decoded, verdict.reason, ref, deps)
    else:
        result = await _write_valid(verdict, decoded, ref, deps)
    return _finish(result, deps)
