"""Validación de los parámetros de consulta (api.md §3.1). Puro: no importa `fastapi` ni `asyncpg`.

Recibe los parámetros crudos como pares `(nombre, valor)` y devuelve estructuras ya validadas.
Un valor no válido lanza `ApiError` con el nombre del parámetro en el mensaje.
"""
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from api.cursor import CursorPosition, decode_cursor
from api.errors import CODE_INVALID_PARAMETER, STATUS_BAD_REQUEST, ApiError
from api.timeutil import MS_PER_HOUR, RECENT_WINDOW_HOURS, parse_iso_to_ms

RawParams = Sequence[tuple[str, str]]

MODE_LIVE = "live"
MODE_REPLAY = "replay"
VALID_MODES = (MODE_LIVE, MODE_REPLAY)
COUNTRY_NONE = "none"
COUNTRY_PATTERN = re.compile(r"[A-Z]{3}")
FILTER_PARAMS = ("start", "end", "min_mag", "country_id", "mode")
PAGE_PARAMS = ("limit", "cursor")


@dataclass(frozen=True)
class QueryFilters:
    """Filtros ya validados; el rango es `[start_ms, end_ms)` y `country_id` va normalizado."""

    start_ms: int
    end_ms: int
    min_mag: float | None
    country_id: str | None
    mode: str


@dataclass(frozen=True)
class PageRequest:
    """Tamaño de página y posición de reanudación (solo `/api/eventos`)."""

    limit: int
    cursor: CursorPosition | None


def _invalid(name: str, expected: str, received: str) -> ApiError:
    return ApiError(STATUS_BAD_REQUEST, CODE_INVALID_PARAMETER,
                    f"El parámetro '{name}' debe ser {expected}; se recibió '{received}'.")


def _single_values(raw_params: RawParams, names: Sequence[str]) -> dict[str, str]:
    """Devuelve el valor de cada parámetro conocido presente; uno repetido es un error."""
    values: dict[str, str] = {}
    for name, value in raw_params:
        if name not in names:
            continue
        if name in values:
            raise ApiError(STATUS_BAD_REQUEST, CODE_INVALID_PARAMETER,
                           f"El parámetro '{name}' solo puede indicarse una vez.")
        values[name] = value
    return values


def _parse_time(name: str, text: str) -> int:
    try:
        return parse_iso_to_ms(text)
    except (ValueError, OverflowError) as error:
        raise _invalid(name, "una fecha ISO 8601", text) from error


def _parse_min_mag(text: str) -> float:
    try:
        value = float(text)
    except ValueError as error:
        raise _invalid("min_mag", "un número finito", text) from error
    if not math.isfinite(value):
        raise _invalid("min_mag", "un número finito", text)
    return value


def _parse_country(text: str) -> str:
    upper = text.upper()
    if upper == COUNTRY_NONE.upper():
        return COUNTRY_NONE
    if not COUNTRY_PATTERN.fullmatch(upper):
        raise _invalid("country_id", "un código ADM0_A3 de tres letras o 'none'", text)
    return upper


def _parse_mode(text: str) -> str:
    if text not in VALID_MODES:
        raise _invalid("mode", "'live' o 'replay'", text)
    return text


def _effective_range(start_ms: int | None, end_ms: int | None, now_ms: int) -> tuple[int, int]:
    """Aplica el rango por defecto de api.md §3.1 cuando falta `start` o `end`."""
    window_ms = RECENT_WINDOW_HOURS * MS_PER_HOUR
    if start_ms is None and end_ms is None:
        return now_ms - window_ms, now_ms
    if end_ms is None:
        return start_ms, now_ms
    if start_ms is None:
        return end_ms - window_ms, end_ms
    return start_ms, end_ms


def parse_filters(raw_params: RawParams, now_ms: int) -> QueryFilters:
    """Valida los filtros comunes de eventos y estadísticas.

    Qué hace:
        Lee `start`, `end`, `min_mag`, `country_id` y `mode`; ignora el resto; aplica el rango por defecto.
    Recibe:
        raw_params: pares (nombre, valor) de la URL; now_ms: instante «ahora» de la petición.
    Devuelve:
        QueryFilters con `start_ms < end_ms`, `country_id` normalizado y `mode` válido.
    Por qué existe:
        Evita el 422 de FastAPI y da mensajes propios en español (D1, F3, F5).
    """
    values = _single_values(raw_params, FILTER_PARAMS)
    start_ms = _parse_time("start", values["start"]) if "start" in values else None
    end_ms = _parse_time("end", values["end"]) if "end" in values else None
    start_ms, end_ms = _effective_range(start_ms, end_ms, now_ms)
    if start_ms >= end_ms:
        raise ApiError(STATUS_BAD_REQUEST, CODE_INVALID_PARAMETER,
                       "El parámetro 'start' debe ser anterior a 'end'.")
    return QueryFilters(
        start_ms=start_ms,
        end_ms=end_ms,
        min_mag=_parse_min_mag(values["min_mag"]) if "min_mag" in values else None,
        country_id=_parse_country(values["country_id"]) if "country_id" in values else None,
        mode=_parse_mode(values["mode"]) if "mode" in values else MODE_LIVE,
    )


def _parse_limit(text: str, max_events: int) -> int:
    expected = f"un entero entre 1 y {max_events}"
    try:
        value = int(text)
    except ValueError as error:
        raise _invalid("limit", expected, text) from error
    if not 1 <= value <= max_events:
        raise _invalid("limit", expected, text)
    return value


def parse_page(raw_params: RawParams, max_events: int) -> PageRequest:
    """Valida `limit` y `cursor` de `/api/eventos`.

    Qué hace:
        `limit` por defecto es `max_events`; `cursor` se decodifica si está presente.
    Recibe:
        raw_params: pares (nombre, valor) de la URL; max_events: máximo configurado.
    Devuelve:
        PageRequest validada.
    Por qué existe:
        Paginación por clave con tope configurable (F5, api.md §3.1).
    """
    values = _single_values(raw_params, PAGE_PARAMS)
    limit = _parse_limit(values["limit"], max_events) if "limit" in values else max_events
    cursor = decode_cursor(values["cursor"]) if "cursor" in values else None
    return PageRequest(limit=limit, cursor=cursor)
