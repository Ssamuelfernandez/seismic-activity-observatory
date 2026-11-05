"""Transformación de un evento válido en filas de base de datos (data-model.md §2, C6, C7).

Lógica pura: no usa `asyncpg` ni `aiokafka`. El `country_id` lo calcula quien llama (geometría,
`common/geo.py`) y solo viaja en `current`; la versión no lo guarda.
"""
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from common.records import DateRow, EventRows, MessageRef, ValidEvent

# Rango admitido de `time`/`updated` (research.md §6): 1000-01-01T00:00:00Z <= instante < 3000-01-01T00:00:00Z.
MIN_EPOCH_MS = -30610224000000
MAX_EPOCH_MS = 32503680000000
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
NULLABLE_FIELDS = ("mag", "depth_km", "place", "status", "url", "sig", "mag_type")


def ms_to_utc(ms: int) -> datetime:
    """Convierte milisegundos Unix en un `datetime` UTC.

    Qué hace:
        Suma los milisegundos a la época con aritmética entera (sin `float`).
    Recibe:
        ms: instante en milisegundos Unix.
    Devuelve:
        `datetime` con zona UTC, sin pérdida de milisegundos.
    Por qué existe:
        La base guarda el instante convertido junto al original en ms (C6, constitución §3).
    """
    return EPOCH + timedelta(milliseconds=ms)


def _to_decimal(value: int | float | None) -> Decimal | None:
    """Convierte con `Decimal(str(x))` para no arrastrar la expansión binaria del float."""
    return None if value is None else Decimal(str(value))


def _serialize_event(event: dict) -> str:
    """Serializa el `event` como JSON compacto, sin escapar Unicode y rechazando no finitos."""
    return json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _build_date_row(event_time: datetime) -> DateRow:
    """Fila de `date_dim` del día UTC del evento (`dow` ISO: 1 = lunes ... 7 = domingo)."""
    day = event_time.date()
    return DateRow(date_id=day, year=day.year, month=day.month, day=day.day, dow=day.isoweekday())


def _find_nulls(valid: ValidEvent) -> tuple[str, ...]:
    """Lista los campos opcionales cuyo valor es nulo (C8: valores nulos conservados)."""
    values = {
        "mag": valid.mag,
        "depth_km": valid.depth,
        "place": valid.place,
        "status": valid.status,
        "url": valid.url,
        "sig": valid.sig,
        "mag_type": valid.mag_type,
    }
    return tuple(name for name in NULLABLE_FIELDS if values[name] is None)


def _build_current(valid: ValidEvent, times: tuple[datetime, datetime, date],
                   country_id: str | None) -> dict:
    """Columnas de `current_event`; `times` = (event_time, updated_at, date_id)."""
    event_time, updated_at, date_id = times
    return {
        "event_id": valid.event_id,
        "event_time": event_time,
        "event_time_ms": valid.time_ms,
        "updated_at": updated_at,
        "updated_ms": valid.updated_ms,
        "mag": _to_decimal(valid.mag),
        "mag_type": valid.mag_type,
        "depth_km": _to_decimal(valid.depth),
        "lon": float(valid.lon),
        "lat": float(valid.lat),
        "place": valid.place,
        "status": valid.status,
        "url": valid.url,
        "sig": valid.sig,
        "date_id": date_id,
        "country_id": country_id,
        "source": valid.source,
        "is_synthetic": valid.is_synthetic,
        "ingested_at": valid.ingested_at,
        "replay_at": valid.replay_at,
    }


def _build_version(valid: ValidEvent, current: dict, original: str, ref: MessageRef, now: datetime) -> dict:
    """Columnas de `event_version`; `received_at` es el reloj del consumidor, no el del evento."""
    return {
        "event_id": valid.event_id,
        "updated_ms": valid.updated_ms,
        "updated_at": current["updated_at"],
        "event_time": current["event_time"],
        "mag": current["mag"],
        "depth_km": current["depth_km"],
        "original": original,
        "source": valid.source,
        "is_synthetic": valid.is_synthetic,
        "received_at": now,
        "kafka_topic": ref.topic,
        "kafka_partition": ref.partition,
        "kafka_offset": ref.offset,
    }


def build_event_rows(valid: ValidEvent, ref: MessageRef, now: datetime,
                     country_id: str | None = None) -> EventRows:
    """Construye las filas de `current_event`, `event_version` y `date_dim` de un evento.

    Qué hace:
        Convierte ms a UTC, los números a `Decimal(str(x))`, calcula el día UTC y el día de
        la semana ISO, lista los campos nulos y serializa el `event` original.
    Recibe:
        valid: evento ya validado; ref: referencia Kafka del mensaje; now: reloj inyectado (UTC);
        country_id: país asignado por geometría (`None` = sin país).
    Devuelve:
        EventRows listo para escribir (`country_id` solo en `current`).
    Por qué existe:
        Aísla la transformación del I/O para que consumidor, histórico y replay la reutilicen
        (C6, C7, FR-016 a FR-021, constitución §3 y §5).
    """
    event_time = ms_to_utc(valid.time_ms)
    updated_at = ms_to_utc(valid.updated_ms)
    date_row = _build_date_row(event_time)
    original = _serialize_event(valid.event)
    current = _build_current(valid, (event_time, updated_at, date_row.date_id), country_id)
    version = _build_version(valid, current, original, ref, now)
    return EventRows(current=current, version=version, date=date_row, nulls=_find_nulls(valid), original=original)
