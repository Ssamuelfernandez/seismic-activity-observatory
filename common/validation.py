"""Validación de un mensaje Kafka en el orden de prevalencia de kafka-message.md §6.

`validate_message` es pura y total: devuelve el PRIMER motivo que falla (14 motivos) o un
`ValidEvent`, y nunca lanza por el contenido (FR-004, FR-014, C1, C5, C6). Cada paso es una
función que devuelve un motivo (`str`) o None si pasa.
"""
import math
from typing import Any

from common.records import DecodeResult, Rejection, ValidEvent
from common.storable import MAX_EVENT_ID_CHARS, is_storable_json
from common.transform import MAX_EPOCH_MS, MIN_EPOCH_MS
from common.validation_envelope import check_envelope, check_mode, parse_utc_timestamp

MAG_RANGE = (-10, 15)
DEPTH_RANGE = (-100, 1000)
LON_RANGE = (-180, 180)
LAT_RANGE = (-90, 90)
INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
TEXT_FIELDS = ("place", "url", "status", "magType")

INVALID_JSON = "invalid_json"
MISSING_ID = "missing_id"
MISSING_TIME = "missing_time"
MISSING_UPDATED = "missing_updated"
INVALID_GEOMETRY = "invalid_geometry"
COORDINATES_OUT_OF_RANGE = "coordinates_out_of_range"
MAG_OUT_OF_RANGE = "mag_out_of_range"
DEPTH_OUT_OF_RANGE = "depth_out_of_range"
INVALID_FIELD_TYPE = "invalid_field_type"
VALUE_OUT_OF_RANGE = "value_out_of_range"
DB_CONSTRAINT_VIOLATION = "db_constraint_violation"


def _is_number(value: Any) -> bool:
    """Número JSON de tipo exacto `int` o `float` (un `bool` no cuenta)."""
    return type(value) is int or type(value) is float


def _is_int(value: Any) -> bool:
    """Entero de tipo exacto (un `bool` no cuenta)."""
    return type(value) is int


def _out_of_range(value: Any, bounds: tuple[int, int]) -> bool:
    """True si un número no es finito o cae fuera de `bounds`. No usa `float()` sobre enteros."""
    if type(value) is float and not math.isfinite(value):
        return True
    return not bounds[0] <= value <= bounds[1]


def _check_identity(event: dict) -> str | None:
    """Pasos 4 a 6: `id`, `time` y `updated` presentes (enteros de tipo exacto)."""
    event_id = event.get("id")
    if event_id is None or event_id == "":
        return MISSING_ID
    props = event.get("properties")
    if not isinstance(props, dict) or not _is_int(props.get("time")):
        return MISSING_TIME
    if not _is_int(props.get("updated")):
        return MISSING_UPDATED
    return None


def _check_geometry(event: dict) -> str | None:
    """Paso 7: geometría `Point` con al menos dos coordenadas."""
    geometry = event.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return INVALID_GEOMETRY
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return INVALID_GEOMETRY
    return None


def _check_ranges(event: dict) -> str | None:
    """Pasos 8 a 10: coordenadas, magnitud y profundidad numéricas dentro de sus rangos."""
    coordinates = event["geometry"]["coordinates"]
    lon, lat = coordinates[0], coordinates[1]
    if (_is_number(lon) and _out_of_range(lon, LON_RANGE)) or (_is_number(lat) and _out_of_range(lat, LAT_RANGE)):
        return COORDINATES_OUT_OF_RANGE
    mag = event["properties"].get("mag")
    if _is_number(mag) and _out_of_range(mag, MAG_RANGE):
        return MAG_OUT_OF_RANGE
    depth = coordinates[2] if len(coordinates) > 2 else None
    if _is_number(depth) and _out_of_range(depth, DEPTH_RANGE):
        return DEPTH_OUT_OF_RANGE
    return None


def _check_types(event: dict) -> str | None:
    """Paso 11: tipos exactos de los campos que se guardan."""
    props = event["properties"]
    coordinates = event["geometry"]["coordinates"]
    depth = coordinates[2] if len(coordinates) > 2 else None
    if not isinstance(event["id"], str):
        return INVALID_FIELD_TYPE
    if any(props.get(name) is not None and not isinstance(props.get(name), str) for name in TEXT_FIELDS):
        return INVALID_FIELD_TYPE
    if props.get("sig") is not None and not _is_int(props.get("sig")):
        return INVALID_FIELD_TYPE
    optional_numbers = (props.get("mag"), depth)
    if any(v is not None and not _is_number(v) for v in optional_numbers):
        return INVALID_FIELD_TYPE
    if not (_is_number(coordinates[0]) and _is_number(coordinates[1])):
        return INVALID_FIELD_TYPE
    return None


def _check_value_ranges(event: dict) -> str | None:
    """Paso 12: `sig` en `int32`, `time`/`updated` dentro del rango y `id` de hasta 512 caracteres."""
    props = event["properties"]
    sig = props.get("sig")
    if sig is not None and not INT32_MIN <= sig <= INT32_MAX:
        return VALUE_OUT_OF_RANGE
    if any(not MIN_EPOCH_MS <= props[name] < MAX_EPOCH_MS for name in ("time", "updated")):
        return VALUE_OUT_OF_RANGE
    return VALUE_OUT_OF_RANGE if len(event["id"]) > MAX_EVENT_ID_CHARS else None


def _check_storable(event: dict) -> str | None:
    """Paso 13: el `event` debe poder guardarse como `jsonb` sin tocar la base."""
    return None if is_storable_json(event) else DB_CONSTRAINT_VIOLATION


def _first_event_failure(event: dict) -> str | None:
    """Ejecuta los pasos 4 a 13 sobre el `event` y devuelve el primer motivo, si lo hay."""
    for check in (
        _check_identity,
        _check_geometry,
        _check_ranges,
        _check_types,
        _check_value_ranges,
        _check_storable,
    ):
        reason = check(event)
        if reason is not None:
            return reason
    return None


def _build_valid_event(envelope: dict) -> ValidEvent:
    """Arma el `ValidEvent` con los campos ya comprobados."""
    event = envelope["event"]
    props = event["properties"]
    coordinates = event["geometry"]["coordinates"]
    return ValidEvent(
        source=envelope["source"],
        mode=envelope["mode"],
        ingested_at=parse_utc_timestamp(envelope["ingested_at"]),
        replay_at=parse_utc_timestamp(envelope.get("replay_at")),
        is_synthetic=envelope["is_synthetic"],
        event=event,
        event_id=event["id"],
        time_ms=props["time"],
        updated_ms=props["updated"],
        mag=props.get("mag"),
        depth=coordinates[2] if len(coordinates) > 2 else None,
        lon=coordinates[0],
        lat=coordinates[1],
        place=props.get("place"),
        status=props.get("status"),
        url=props.get("url"),
        sig=props.get("sig"),
        mag_type=props.get("magType"),
    )


def validate_message(decoded: DecodeResult, topic: str) -> ValidEvent | Rejection:
    """Valida un mensaje decodificado y devuelve el primer motivo de cuarentena que falle.

    Qué hace:
        Aplica los 14 motivos de kafka-message.md §6 en su orden de prevalencia, con
        comprobación de tipo exacto y sin lanzar excepciones por el contenido.
    Recibe:
        decoded: resultado de `decode_value`; topic: tema de origen (decide el modo esperado).
    Devuelve:
        `ValidEvent` si pasa los 14 pasos; `Rejection(reason)` con el primer fallo si no.
    Por qué existe:
        Ninguna escritura debe fallar por contenido: lo inválido se detecta aquí, antes de la
        base (C1, C5, C6, FR-004, FR-014, FR-015, FR-017).
    """
    if not decoded.ok:
        return Rejection(INVALID_JSON)
    reason = check_envelope(decoded.obj) or check_mode(decoded.obj, topic)
    reason = reason or _first_event_failure(decoded.obj["event"])
    if reason is not None:
        return Rejection(reason)
    return _build_valid_event(decoded.obj)
