"""Construcción de la fila de cuarentena de un mensaje rechazado (research.md §4, C5, C13).

Lógica pura: se decide todo antes del `INSERT`, inspeccionando el contenido y nunca el
SQLSTATE devuelto por la base.
"""
import hashlib
import json
from datetime import datetime
from typing import Any

from common.records import DecodeResult, MessageRef, QuarantineRow, kafka_columns
from common.storable import MAX_EVENT_ID_CHARS, is_storable_json, is_storable_text, sanitize_raw_text

ALLOWED_SOURCES = frozenset({"usgs_feed", "usgs_historical", "replay_demo"})


def _serialize_original(decoded: DecodeResult) -> str | None:
    """Devuelve el sobre completo como texto JSON si es almacenable; si no, None."""
    if not decoded.ok or not is_storable_json(decoded.obj):
        return None
    return json.dumps(decoded.obj, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _copy_event_id(obj: Any) -> str | None:
    """Copia `event.id` solo si es una cadena almacenable de hasta 512 caracteres."""
    event = obj.get("event") if isinstance(obj, dict) else None
    event_id = event.get("id") if isinstance(event, dict) else None
    if isinstance(event_id, str) and len(event_id) <= MAX_EVENT_ID_CHARS and is_storable_text(event_id):
        return event_id
    return None


def _copy_source(obj: Any) -> str | None:
    """Copia `source` solo si es uno de los tres valores permitidos por el `CHECK`."""
    source = obj.get("source") if isinstance(obj, dict) else None
    return source if isinstance(source, str) and source in ALLOWED_SOURCES else None


def _copy_is_synthetic(obj: Any) -> bool:
    """Copia `is_synthetic` solo si es un booleano exacto; si no, False."""
    flag = obj.get("is_synthetic") if isinstance(obj, dict) else None
    return flag if isinstance(flag, bool) else False


def build_quarantine_row(decoded: DecodeResult, reason: str, ref: MessageRef, now: datetime) -> QuarantineRow:
    """Construye la fila de `quarantine` de un mensaje rechazado.

    Qué hace:
        Calcula el SHA-256 de los bytes recibidos; guarda el sobre completo en `original`
        solo si es almacenable y, si no, un `raw_text` saneado (nunca ambos nulos ni ambos
        rellenos); copia `event_id`, `source` e `is_synthetic` solo si son seguros.
    Recibe:
        decoded: resultado de `decode_value` (incluye los bytes recibidos en `raw`).
        reason: motivo decidido por la validación (nunca sale del mensaje).
        ref: referencia Kafka; now: reloj inyectado (UTC).
    Devuelve:
        QuarantineRow lista para el `INSERT ... ON CONFLICT DO NOTHING`.
    Por qué existe:
        Garantiza que ninguna cuarentena falle por contenido y que sea idempotente por
        (hash, motivo) (C5, C13, FR-011, FR-012, FR-014, FR-022).
    """
    original = _serialize_original(decoded)
    obj = decoded.obj if decoded.ok else None
    kafka_topic, kafka_partition, kafka_offset = kafka_columns(ref)
    return QuarantineRow(
        event_id=_copy_event_id(obj),
        reason=reason,
        original=original,
        raw_text=None if original is not None else sanitize_raw_text(decoded.raw),
        original_sha256=hashlib.sha256(decoded.raw).hexdigest(),
        source=_copy_source(obj),
        kafka_topic=kafka_topic,
        kafka_partition=kafka_partition,
        kafka_offset=kafka_offset,
        received_at=now,
        is_synthetic=_copy_is_synthetic(obj),
    )
