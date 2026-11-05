"""Consultas SQL de solo lectura de `/api/estadisticas`: todo se agrega en la base (constitución §8).

Reutilizan `build_where` de los eventos, de modo que `total`, horas, países e histogramas ven
exactamente los mismos filtros. Los valores del cliente viajan como parámetros `$n`.
"""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Sequence

import asyncpg

from api.params import QueryFilters
from api.sql_filters import build_where, current_event_table
from api.stats_builder import REFERENCE_END_MS, REFERENCE_START_MS, effective_comparison_min_mag, recent_period
from api.timeutil import MS_PER_HOUR, ms_to_datetime

# Columnas que admiten histograma: lista cerrada, el nombre solo se inserta desde aquí.
HISTOGRAM_COLUMNS = {"magnitude": "mag", "depth": "depth_km"}

# Q4: recuento por hora UTC fija según `event_time_ms` (los tiempos son positivos).
HOURS_SQL = """
SELECT (e.event_time_ms / {ms_per_hour}) * {ms_per_hour} AS hour_start, count(*) AS count
FROM {table} e
WHERE {where}
GROUP BY 1
"""

# Q2: recuento por país con nombre y subregión; el elemento sin país (NULL) va incluido.
COUNTRIES_SQL = """
SELECT e.country_id, c.name_es AS country_name, c.subregion, count(*) AS count
FROM {table} e
LEFT JOIN public.country c ON c.country_id = e.country_id
WHERE {where}
GROUP BY e.country_id, c.name_es, c.subregion
ORDER BY count(*) DESC, e.country_id ASC NULLS LAST
"""

# Histograma: `width_bucket` con la lista de umbrales da el tramo 0..N; un valor nulo da `bucket` nulo.
HISTOGRAM_SQL = """
SELECT width_bucket(e.{column}, ${thresholds_index}::numeric[]) AS bucket, count(*) AS count
FROM {table} e
WHERE {where}
GROUP BY 1
"""

# Comparación: dos recuentos en una pasada sobre el rango que cubre ambos periodos.
COMPARISON_SQL = """
SELECT count(*) FILTER (WHERE e.event_time >= ${recent_start} AND e.event_time < ${recent_end}) AS n_recent,
       count(*) FILTER (WHERE e.event_time >= ${ref_start} AND e.event_time < ${ref_end}) AS n_2025
FROM {table} e
WHERE {where}
"""

COMPARISON_MODE = "live"


@dataclass(frozen=True)
class ComparisonCounts:
    """Eventos de las últimas 24 h y de 2025 con los mismos filtros salvo las fechas."""

    n_recent: int
    n_2025: int


async def fetch_hour_counts(connection: asyncpg.Connection, filters: QueryFilters) -> list[asyncpg.Record]:
    """Recuento por hora UTC fija de los eventos que cumplen los filtros (solo las horas con eventos)."""
    where, params = build_where(filters, None)
    sql = HOURS_SQL.format(ms_per_hour=MS_PER_HOUR, table=current_event_table(filters.mode), where=where)
    return await connection.fetch(sql, *params)


async def fetch_country_counts(connection: asyncpg.Connection, filters: QueryFilters) -> list[asyncpg.Record]:
    """Recuento por país, con el elemento sin país, por `count` descendente y `country_id` ascendente."""
    where, params = build_where(filters, None)
    sql = COUNTRIES_SQL.format(table=current_event_table(filters.mode), where=where)
    return await connection.fetch(sql, *params)


async def fetch_histogram(connection: asyncpg.Connection, filters: QueryFilters, name: str,
                          thresholds: Sequence[int]) -> list[asyncpg.Record]:
    """Filas `bucket`/`count` de `width_bucket` sobre la columna del histograma `name`.

    Recibe:
        name: `magnitude` o `depth` (lista cerrada); thresholds: umbrales ascendentes (N umbrales, N+1 tramos).
    Devuelve:
        Una fila por tramo con eventos; `bucket` nulo agrupa los eventos sin valor.
    """
    where, params = build_where(filters, None)
    params.append([Decimal(threshold) for threshold in thresholds])
    sql = HISTOGRAM_SQL.format(column=HISTOGRAM_COLUMNS[name], table=current_event_table(filters.mode),
                               where=where, thresholds_index=len(params))
    return await connection.fetch(sql, *params)


def comparison_filters(filters: QueryFilters, now_ms: int) -> QueryFilters:
    """Filtros de la comparación: modo en vivo, `min_mag` efectivo y un rango que cubre 2025 y las últimas 24 h."""
    recent = recent_period(now_ms)
    return replace(filters, mode=COMPARISON_MODE, min_mag=effective_comparison_min_mag(filters.min_mag),
                   start_ms=min(REFERENCE_START_MS, recent["start"]), end_ms=max(REFERENCE_END_MS, now_ms))


async def fetch_comparison_counts(connection: asyncpg.Connection, filters: QueryFilters,
                                  now_ms: int) -> ComparisonCounts:
    """Cuenta los eventos de las últimas 24 h y de 2025 con el país pedido y `max(min_mag, 4.0)`.

    Por qué existe:
        Base de `comparison` (api.md §5.1); ambos lados usan los mismos filtros salvo las fechas.
    """
    where, params = build_where(comparison_filters(filters, now_ms), None)
    recent = recent_period(now_ms)
    bounds = [recent["start"], recent["end"], REFERENCE_START_MS, REFERENCE_END_MS]
    first_index = len(params) + 1
    params.extend(ms_to_datetime(bound) for bound in bounds)
    sql = COMPARISON_SQL.format(table=current_event_table(COMPARISON_MODE), where=where,
                                recent_start=first_index, recent_end=first_index + 1,
                                ref_start=first_index + 2, ref_end=first_index + 3)
    row = await connection.fetchrow(sql, *params)
    return ComparisonCounts(n_recent=row["n_recent"], n_2025=row["n_2025"])
