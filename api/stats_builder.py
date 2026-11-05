"""Construcción pura del cuerpo de `/api/estadisticas` (api.md §5). No importa `fastapi` ni `asyncpg`.

Recibe filas ya agregadas por SQL (objetos con acceso por nombre: `dict` o `asyncpg.Record`) y
las convierte en los bloques del contrato: horas con cero, tramos de histograma y comparación.
"""
from collections.abc import Mapping, Sequence
from typing import Any

from api.timeutil import MS_PER_HOUR, RECENT_WINDOW_HOURS

Row = Mapping[str, Any]

# Tramos de histograma (api.md §5.1): el umbral inferior de cada tramo es inclusivo.
MAGNITUDE_THRESHOLDS = (1, 2, 3, 4, 5, 6, 7)
DEPTH_THRESHOLDS = (10, 35, 70, 300)

# Comparación con el histórico de 2025 (api.md §5.1).
COMPARISON_MIN_MAG = 4.0
REFERENCE_START_MS = 1_735_689_600_000  # 2025-01-01T00:00Z
REFERENCE_END_MS = 1_767_225_600_000  # 2026-01-01T00:00Z
REFERENCE_DAYS = 365
PERCENT = 100
PERCENT_DECIMALS = 2

UNIT_EVENTS = "events"
UNIT_MAGNITUDE = "dimensionless"
UNIT_DEPTH = "km"


def build_hour_buckets(rows: Sequence[Row], start_ms: int, end_ms: int) -> list[dict[str, int]]:
    """Una entrada por hora UTC fija que se solapa con `[start_ms, end_ms)`, con cero si no hay eventos.

    Recibe:
        rows: filas con `hour_start` (ms) y `count`; start_ms y end_ms: rango efectivo.
    Devuelve:
        Lista `{"hour_start", "count"}` desde la hora de `start` hasta la de `end - 1 ms`.
    """
    counts = {row["hour_start"]: row["count"] for row in rows}
    first = start_ms // MS_PER_HOUR * MS_PER_HOUR
    last = (end_ms - 1) // MS_PER_HOUR * MS_PER_HOUR
    return [{"hour_start": hour, "count": counts.get(hour, 0)} for hour in range(first, last + 1, MS_PER_HOUR)]


def build_by_hour(rows: Sequence[Row], start_ms: int, end_ms: int) -> dict[str, Any]:
    """Bloque `by_hour`; `no_value` es 0 porque `event_time` no admite nulo."""
    return {"unit": UNIT_EVENTS, "no_value": 0, "buckets": build_hour_buckets(rows, start_ms, end_ms)}


def build_by_country(rows: Sequence[Row]) -> dict[str, Any]:
    """Bloque `by_country`: los eventos sin país forman un elemento propio y `no_value` repite su recuento.

    Recibe:
        rows: filas con `country_id`, `country_name`, `subregion` y `count`, ya ordenadas por el SQL.
    """
    items = [{"country_id": row["country_id"], "country_name": row["country_name"],
              "subregion": row["subregion"], "count": row["count"]} for row in rows]
    no_value = sum(item["count"] for item in items if item["country_id"] is None)
    return {"unit": UNIT_EVENTS, "no_value": no_value, "items": items}


def build_bins(rows: Sequence[Row], thresholds: Sequence[int]) -> list[dict[str, Any]]:
    """Tramos de un histograma a partir de filas `width_bucket` (`bucket` 0..N y `count`).

    El tramo 0 no tiene límite inferior y el último no tiene límite superior; los tramos sin filas valen 0.
    """
    counts = {row["bucket"]: row["count"] for row in rows if row["bucket"] is not None}
    bounds: list[int | None] = [None, *thresholds, None]
    return [{"lower": bounds[index], "upper": bounds[index + 1], "count": counts.get(index, 0)}
            for index in range(len(thresholds) + 1)]


def count_without_bucket(rows: Sequence[Row]) -> int:
    """Eventos sin valor: las filas cuyo `bucket` es nulo (`width_bucket` de un valor nulo)."""
    return sum(row["count"] for row in rows if row["bucket"] is None)


def build_histogram(rows: Sequence[Row], thresholds: Sequence[int], unit: str, no_value: int) -> dict[str, Any]:
    """Bloque de histograma con su unidad, los tramos y el recuento de eventos sin valor."""
    return {"unit": unit, "no_value": no_value, "bins": build_bins(rows, thresholds)}


def _variation_pct(diff_abs: float, daily_mean: float) -> float | None:
    """Variación porcentual a 2 decimales, o None si la media es 0 (no hay base de comparación)."""
    if daily_mean == 0:
        return None
    return round(diff_abs / daily_mean * PERCENT, PERCENT_DECIMALS)


def effective_comparison_min_mag(min_mag: float | None) -> float:
    """Magnitud mínima efectiva de la comparación: `max(min_mag, 4.0)`."""
    return COMPARISON_MIN_MAG if min_mag is None else max(min_mag, COMPARISON_MIN_MAG)


def recent_period(generated_ms: int) -> dict[str, int]:
    """Últimas 24 h hasta `generated`."""
    return {"start": generated_ms - RECENT_WINDOW_HOURS * MS_PER_HOUR, "end": generated_ms}


def build_comparison(n_recent: int, n_2025: int, min_mag: float | None, generated_ms: int) -> dict[str, Any]:
    """Bloque `comparison`: últimas 24 h frente a la media diaria de 2025 (api.md §5.1).

    Recibe:
        n_recent y n_2025: recuentos con los filtros pedidos salvo las fechas; min_mag: el solicitado
        (o None); generated_ms: instante de la respuesta.
    """
    daily_mean = n_2025 / REFERENCE_DAYS
    diff_abs = n_recent - daily_mean
    return {
        "unit": UNIT_EVENTS,
        "min_mag_applied": effective_comparison_min_mag(min_mag),
        "recent_period": recent_period(generated_ms),
        "reference_period": {"start": REFERENCE_START_MS, "end": REFERENCE_END_MS},
        "n_recent": n_recent,
        "n_2025": n_2025,
        "daily_mean_2025": daily_mean,
        "diff_abs": diff_abs,
        "variation_pct": _variation_pct(diff_abs, daily_mean),
        "recent_incomplete": True,
    }
