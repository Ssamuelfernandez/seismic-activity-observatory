"""Consultas SQL de solo lectura de la API para salud y eventos."""
from dataclasses import dataclass

import asyncpg

from api.cursor import CursorPosition
from api.params import QueryFilters
from api.sql_filters import build_where, current_event_table, total_expression

# Q8 (db-schema.md): última consulta correcta a USGS; usa el índice parcial ix_ingest_run_last_ok.
LAST_INGESTION_SQL = """
SELECT (extract(epoch FROM max(run_at)) * 1000)::bigint
FROM ingest.ingest_run
WHERE error IS NULL AND status = 200
"""

# Q1: página de eventos con el nombre del país; la plantilla solo recibe el esquema (lista cerrada)
# y el WHERE ya parametrizado.
EVENTS_PAGE_SQL = """
SELECT e.event_id, e.lon, e.lat, e.depth_km, e.mag, e.mag_type, e.place, e.event_time_ms, e.updated_ms,
       e.country_id, c.name_es AS country_name, e.is_synthetic, e.status, e.url, e.sig
FROM {table} e
LEFT JOIN public.country c ON c.country_id = e.country_id
WHERE {where}
ORDER BY e.event_time DESC, e.event_id DESC
LIMIT ${limit_index}
"""

# Recuentos del rango y país sin `min_mag`: `total` aplica `min_mag` y `null_count` cuenta las magnitudes nulas.
COUNTS_SQL = """
SELECT {total} AS total, count(*) FILTER (WHERE e.mag IS NULL) AS null_count
FROM {table} e
WHERE {where}
"""


@dataclass(frozen=True)
class EventCounts:
    """Eventos que cumplen todos los filtros (`total`) y los de magnitud nula del mismo rango y país."""

    total: int
    null_count: int


async def fetch_last_ingestion_ms(executor: asyncpg.Pool | asyncpg.Connection) -> int | None:
    """Devuelve la última ingesta correcta en ms Unix UTC, o None si aún no hubo ninguna.

    Por qué existe:
        Es el campo `last_ingestion` de las respuestas (api.md §3.2 y §4); siempre es del modo en vivo.
        Acepta un pool o una conexión.
    """
    return await executor.fetchval(LAST_INGESTION_SQL)


async def fetch_events_page(connection: asyncpg.Connection, filters: QueryFilters,
                            cursor: CursorPosition | None, limit: int) -> tuple[list[asyncpg.Record], bool]:
    """Lee una página de eventos en orden `event_time` e `id` descendentes.

    Qué hace:
        Pide `limit + 1` filas para saber si hay más; devuelve como máximo `limit`.
    Recibe:
        connection: conexión dentro de la transacción de lectura; filters; cursor; limit (>= 1).
    Devuelve:
        (filas de la página, hay_más).
    Por qué existe:
        Paginación por clave sin repetir ni saltar eventos (F5, Q1).
    """
    where, params = build_where(filters, cursor)
    params.append(limit + 1)
    sql = EVENTS_PAGE_SQL.format(table=current_event_table(filters.mode), where=where, limit_index=len(params))
    rows = await connection.fetch(sql, *params)
    return rows[:limit], len(rows) > limit


async def fetch_counts(connection: asyncpg.Connection, filters: QueryFilters) -> EventCounts:
    """Cuenta los eventos del rango y país: `total` (con `min_mag`) y `null_count` (magnitud nula).

    Por qué existe:
        `total` y `null_mag_excluded` salen de la misma consulta y no pueden divergir (D9, FR-005).
    """
    where, params = build_where(filters, None, with_min_mag=False)
    total = total_expression(filters, params)
    sql = COUNTS_SQL.format(table=current_event_table(filters.mode), where=where, total=total)
    row = await connection.fetchrow(sql, *params)
    return EventCounts(total=row["total"], null_count=row["null_count"])


def null_mag_excluded(counts: EventCounts, filters: QueryFilters) -> int:
    """Eventos con magnitud nula excluidos por `min_mag`; 0 si no se envió `min_mag`."""
    return counts.null_count if filters.min_mag is not None else 0

