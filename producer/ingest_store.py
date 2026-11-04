"""Almacén de ingesta en PostgreSQL con el rol `observatory_producer` (B3-B6, B9, FR-002 a FR-007)."""
import logging
from datetime import datetime

import asyncpg

from producer import ingest_queries as queries
from producer.usgs_client import FeedResponse

logger = logging.getLogger(__name__)

DELETE_TAG_PREFIX = "DELETE "


async def last_ok_hash(conn: asyncpg.Pool | asyncpg.Connection) -> str | None:
    """Devuelve el hash de la última consulta correcta, o None si no hay ninguna."""
    return await conn.fetchval(queries.LAST_OK_HASH)


async def record_success(pool: asyncpg.Pool, url: str, response: FeedResponse,
                         event_count: int, sha256: str) -> bool:
    """Guarda el original (si es distinto) y registra la consulta correcta, en una transacción.

    Qué hace:
        Inserta en `raw_response` solo si el hash difiere del de la última consulta correcta e
        inserta siempre la fila de `ingest_run` con estado 200.
    Recibe:
        url: feed consultado; response: respuesta; event_count: elementos de `features`;
        sha256: hash canónico de `features`.
    Devuelve:
        True si se guardó un original nuevo.
    Por qué existe:
        Guardar el original antes de transformar (B4) sin dejar una consulta sin su original (research §2).
    """
    async with pool.acquire() as conn, conn.transaction():
        is_new = sha256 != await last_ok_hash(conn)
        if is_new:
            await conn.execute(queries.RAW_RESPONSE_INSERT, response.received_at, sha256,
                               response.body.decode("utf-8"))
        await conn.execute(queries.INGEST_RUN_INSERT, response.received_at, url, response.status,
                           response.latency_ms, event_count, sha256, None)
    return is_new


async def record_failure(pool: asyncpg.Pool, url: str, run_at: datetime, status: int | None,
                         latency_ms: int, error: str) -> None:
    """Registra una consulta fallida: sin `sha256` ni `event_count` (data-model.md §2)."""
    await pool.execute(queries.INGEST_RUN_INSERT, run_at, url, status, latency_ms, None, None, error)


async def insert_exclusions(pool: asyncpg.Pool, rows: list[dict]) -> None:
    """Anota los elementos excluidos; repetirlos no duplica filas."""
    if not rows:
        return
    await pool.executemany(queries.EXCLUSION_INSERT, [
        (r["event_id"], r["updated_ms"], r["kind"], r["reason"], r["observed_type"],
         r["fetched_at"], r["is_synthetic"]) for r in rows
    ])


async def load_state(pool: asyncpg.Pool, event_ids: list[str]) -> dict[str, int]:
    """Lee el último `updated` publicado de cada `id` pedido, en una sola consulta."""
    records = await pool.fetch(queries.STATE_SELECT, event_ids)
    return {r["event_id"]: r["last_updated_ms"] for r in records}


async def mark_published(pool: asyncpg.Pool, event_id: str, updated_ms: int, published_at: datetime) -> None:
    """Marca un evento como publicado tras el ack de Kafka; nunca retrocede el estado (B9)."""
    await pool.execute(queries.STATE_UPSERT, event_id, updated_ms, published_at)


async def purge_raw_responses(pool: asyncpg.Pool, retention_days: int) -> int:
    """Borra los originales más antiguos que la retención, conservando siempre el más reciente.

    Devuelve:
        Número de filas borradas.
    """
    tag = await pool.execute(queries.RAW_RESPONSE_PURGE, retention_days)
    deleted = int(tag.removeprefix(DELETE_TAG_PREFIX))
    logger.info("Purga de raw_response: %d filas", deleted)
    return deleted


class PoolIngestStore:
    """Almacén ligado a un pool: las mismas operaciones sin pasar el pool en cada llamada."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def record_success(self, url: str, response: FeedResponse, event_count: int, sha256: str) -> bool:
        return await record_success(self._pool, url, response, event_count, sha256)

    async def record_failure(self, url: str, run_at: datetime, status: int | None,
                             latency_ms: int, error: str) -> None:
        await record_failure(self._pool, url, run_at, status, latency_ms, error)

    async def insert_exclusions(self, rows: list[dict]) -> None:
        await insert_exclusions(self._pool, rows)

    async def load_state(self, event_ids: list[str]) -> dict[str, int]:
        return await load_state(self._pool, event_ids)

    async def mark_published(self, event_id: str, updated_ms: int, published_at: datetime) -> None:
        await mark_published(self._pool, event_id, updated_ms, published_at)

    async def purge_raw_responses(self, retention_days: int) -> int:
        return await purge_raw_responses(self._pool, retention_days)
