"""Ayudas de las pruebas de integración: procesar un mensaje con las funciones reales de `common/`.

Hace lo que hará `pipeline.process_record` (bloque 4) pero sin reintentos ni hook, para probar
el escritor contra PostgreSQL real. No clasifica errores: si la base lanza, la excepción sube.
"""
import json
from datetime import datetime, timezone
from typing import Any

from common.decode import decode_value
from common.kafka_topics import TOPIC_LIVE, topic_mode
from common.quarantine_row import build_quarantine_row
from common.records import MessageRef, ProcessingResult, Rejection, ResultKind
from common.transform import build_event_rows
from common.validation import validate_message
from consumer.writer import write_event, write_quarantine

NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
PARTITION = 0


def to_raw(message: dict) -> bytes:
    """Serializa un mensaje como lo haría el productor."""
    return json.dumps(message).encode("utf-8")


async def process_raw(conn: Any, raw: bytes | None, offset: int, topic: str = TOPIC_LIVE,
                      now: datetime = NOW) -> ProcessingResult:
    """Decodifica, valida, transforma y escribe un mensaje; devuelve su `ProcessingResult`."""
    mode = topic_mode(topic)
    ref = MessageRef(topic, PARTITION, offset)
    decoded = decode_value(raw)
    verdict = validate_message(decoded, topic)
    if isinstance(verdict, Rejection):
        row = build_quarantine_row(decoded, verdict.reason, ref, now)
        inserted = await write_quarantine(conn, row, mode)
        return ProcessingResult(ResultKind.QUARANTINE, ref, reason=verdict.reason, inserted=inserted,
                                event_id=row.event_id, is_synthetic=row.is_synthetic)
    rows = build_event_rows(verdict, ref, now)
    outcome = await write_event(conn, rows, mode)
    return ProcessingResult(ResultKind.EVENT, ref, outcome=outcome, converted=True, nulls=rows.nulls,
                            event_id=verdict.event_id, is_synthetic=verdict.is_synthetic,
                            updated_ms=verdict.updated_ms)


async def process_message(conn: Any, message: dict, offset: int, topic: str = TOPIC_LIVE) -> ProcessingResult:
    """Igual que `process_raw` para un mensaje ya construido como diccionario."""
    return await process_raw(conn, to_raw(message), offset, topic)
