"""Construcción del WHERE de las consultas de eventos (D5, D7, FR-014). Puro: sin `fastapi` ni `asyncpg`.

Todo valor del cliente viaja como parámetro posicional `$n`; el único texto que se inserta en el SQL
es el nombre del esquema, y sale de la lista cerrada `SCHEMAS`.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any

from api.cursor import CursorPosition
from api.params import COUNTRY_NONE, QueryFilters
from api.timeutil import ms_to_datetime

# Lista cerrada de esquemas: `mode` ya validado -> nombre de esquema.
SCHEMAS = {"live": "live", "replay": "replay"}
EVENT_TABLE = "current_event"
EVENT_ALIAS = "e"


def current_event_table(mode: str) -> str:
    """Devuelve `<esquema>.current_event` para un modo válido (`KeyError` si no está en la lista cerrada)."""
    return f"{SCHEMAS[mode]}.{EVENT_TABLE}"


def _placeholder(params: list[Any], value: Any) -> str:
    """Añade el valor a los parámetros y devuelve su marcador `$n`."""
    params.append(value)
    return f"${len(params)}"


def _to_decimal(value: float) -> Decimal:
    return Decimal(repr(value))


def total_expression(filters: QueryFilters, params: list[Any]) -> str:
    """Expresión de recuento que aplica `min_mag` sin perder el recuento de nulos (D9).

    Añade el valor de `min_mag` a `params` si hace falta y devuelve el `count(*)` correspondiente.
    """
    if filters.min_mag is None:
        return "count(*)"
    return f"count(*) FILTER (WHERE {EVENT_ALIAS}.mag >= {_placeholder(params, _to_decimal(filters.min_mag))})"


def build_where(filters: QueryFilters, cursor: CursorPosition | None,
                with_min_mag: bool = True) -> tuple[str, list[Any]]:
    """Arma el fragmento WHERE (sin la palabra WHERE) y sus parámetros posicionales.

    Qué hace:
        Siempre filtra el rango `[start, end)`; añade `min_mag`, país y cursor solo si se piden.
    Recibe:
        filters: filtros validados; cursor: posición de reanudación o None;
        with_min_mag: False para los recuentos, que aplican `min_mag` aparte para contar los nulos (D9).
    Devuelve:
        (fragmento SQL sobre el alias `e`, lista de parámetros en el orden de `$1`, `$2`…).
    Por qué existe:
        Eventos, recuentos y estadísticas comparten los mismos filtros sin concatenar valores (F3, F10).
    """
    params: list[Any] = []
    start: datetime = ms_to_datetime(filters.start_ms)
    end: datetime = ms_to_datetime(filters.end_ms)
    conditions = [f"{EVENT_ALIAS}.event_time >= {_placeholder(params, start)}",
                  f"{EVENT_ALIAS}.event_time < {_placeholder(params, end)}"]
    if with_min_mag and filters.min_mag is not None:
        conditions.append(f"{EVENT_ALIAS}.mag >= {_placeholder(params, _to_decimal(filters.min_mag))}")
    if filters.country_id == COUNTRY_NONE:
        conditions.append(f"{EVENT_ALIAS}.country_id IS NULL")
    elif filters.country_id is not None:
        conditions.append(f"{EVENT_ALIAS}.country_id = {_placeholder(params, filters.country_id)}")
    if cursor is not None:
        time_marker = _placeholder(params, ms_to_datetime(cursor.time_ms))
        id_marker = _placeholder(params, cursor.event_id)
        conditions.append(f"({EVENT_ALIAS}.event_time, {EVENT_ALIAS}.event_id) < ({time_marker}, {id_marker})")
    return " AND ".join(conditions), params
