"""Consultas SQL de solo lectura de la API."""
import asyncpg

# Q8 (db-schema.md): última consulta correcta a USGS; usa el índice parcial ix_ingest_run_last_ok.
LAST_INGESTION_SQL = """
SELECT (extract(epoch FROM max(run_at)) * 1000)::bigint
FROM ingest.ingest_run
WHERE error IS NULL AND status = 200
"""


async def fetch_last_ingestion_ms(pool: asyncpg.Pool) -> int | None:
    """Devuelve la última ingesta correcta en ms Unix UTC, o None si aún no hubo ninguna.

    Por qué existe:
        Es el campo `last_ingestion` de `/api/salud` (api.md §4) y prueba que la API lee la base.
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(LAST_INGESTION_SQL)
