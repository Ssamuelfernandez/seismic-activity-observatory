"""Serialización de eventos y del `metadata` de `/api/eventos` (api.md §3.2-§3.4).

Puro: no importa `fastapi` ni `asyncpg`. Una fila es cualquier objeto con acceso por nombre
(`dict` o `asyncpg.Record`).
"""
import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

Row = Mapping[str, Any]

GEOMETRY_TYPE = "Point"
FEATURE_TYPE = "Feature"
COLLECTION_TYPE = "FeatureCollection"


def to_json_number(value: Decimal | float | None) -> float | None:
    """Convierte un `numeric` a `float` finito; el desconocido o no finito pasa a `None`.

    Por qué existe:
        `null` nunca se sustituye por 0 ni por NaN/Infinity (constitución §5, api.md §1).
    """
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _build_properties(row: Row) -> dict[str, Any]:
    return {
        "mag": to_json_number(row["mag"]),
        "magType": row["mag_type"],
        "place": row["place"],
        "time": row["event_time_ms"],
        "updated": row["updated_ms"],
        "country_id": row["country_id"],
        "country_name": row["country_name"],
        "is_synthetic": row["is_synthetic"],
        "status": row["status"],
        "url": row["url"],
        "sig": row["sig"],
    }


def build_feature(row: Row) -> dict[str, Any]:
    """Convierte una fila de `current_event` (con el nombre del país) en una `Feature` GeoJSON.

    Qué hace:
        Pone `[lon, lat, depth_km]` en la geometría y los once campos en `properties`.
    Recibe:
        row: columnas `event_id`, `lon`, `lat`, `depth_km`, `mag`, `mag_type`, `place`, `event_time_ms`,
        `updated_ms`, `country_id`, `country_name`, `is_synthetic`, `status`, `url` y `sig`.
    Devuelve:
        Diccionario listo para `json.dumps(allow_nan=False)`.
    Por qué existe:
        Forma única de cada evento en la respuesta (F1, F2, F4).
    """
    return {
        "type": FEATURE_TYPE,
        "id": row["event_id"],
        "geometry": {
            "type": GEOMETRY_TYPE,
            "coordinates": [row["lon"], row["lat"], to_json_number(row["depth_km"])],
        },
        "properties": _build_properties(row),
    }


def build_metadata(*, generated: int, last_ingestion: int | None, mode: str, count: int, total: int,
                   next_cursor: str | None, null_mag_excluded: int) -> dict[str, Any]:
    """Construye el `metadata` de ocho campos de `/api/eventos`.

    Qué hace:
        Copia los valores y calcula `truncated` como `count < total`.
    Recibe:
        generated y last_ingestion en ms; mode; count (eventos de esta página); total (con los filtros);
        next_cursor (None en la última página); null_mag_excluded.
    Devuelve:
        Diccionario con los ocho campos del contrato.
    Por qué existe:
        `truncated` es true en cada página que no contiene todos los eventos, también en la última (F5).
    """
    return {
        "generated": generated,
        "last_ingestion": last_ingestion,
        "mode": mode,
        "count": count,
        "total": total,
        "truncated": count < total,
        "next_cursor": next_cursor,
        "null_mag_excluded": null_mag_excluded,
    }


def build_collection(features: Sequence[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    """Une el `metadata` y las `Feature` en el `FeatureCollection` de la respuesta."""
    return {"type": COLLECTION_TYPE, "metadata": metadata, "features": list(features)}
