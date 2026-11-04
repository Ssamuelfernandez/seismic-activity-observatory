"""Ayudas de las pruebas de integración del productor: ciclo real contra PostgreSQL y el mock de USGS.

Datos sintéticos (`synthetic-...`): el publicador es falso y nada llega a Kafka ni a una base real.
"""
import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

import asyncpg
from aiokafka.errors import KafkaConnectionError

from common.config import FeedSettings
from producer.cycle import CycleDeps, CycleResult, run_cycle
from producer.ingest_store import PoolIngestStore
from producer.usgs_client import fetch_feed
from tests.support.temp_database import TempDatabase

TIMEOUT_SECONDS = 1
SNAPSHOT_QUERIES = {
    "ingest_state": "SELECT event_id, last_updated_ms, published_at FROM ingest.ingest_state ORDER BY event_id",
    "raw_response": "SELECT id, sha256, fetched_at FROM ingest.raw_response ORDER BY id",
    "exclusion": "SELECT event_id, updated_ms, observed_type FROM live.exclusion ORDER BY event_id, updated_ms",
}


def feed_settings(url: str) -> FeedSettings:
    """Configuración del ciclo apuntando al mock."""
    return FeedSettings(url=url, poll_seconds=60, timeout_seconds=TIMEOUT_SECONDS, raw_retention_days=7)


class RecordingPublisher:
    """Publicador falso: guarda (clave, mensaje) y, si `fail` está activo, falla como un broker caído."""

    def __init__(self) -> None:
        self.sent: list[tuple[str | None, dict]] = []
        self.fail = False

    async def __call__(self, key: str | None, message: dict) -> None:
        if self.fail:
            raise KafkaConnectionError("simulado")
        self.sent.append((key, message))


class FlakyMarkStore(PoolIngestStore):
    """Almacén cuyo `mark_published` falla `failures` veces: reproduce el corte entre el ack y la marca."""

    def __init__(self, pool: asyncpg.Pool, failures: int) -> None:
        super().__init__(pool)
        self.failures = failures

    async def mark_published(self, event_id: str, updated_ms: int, published_at: datetime) -> None:
        if self.failures > 0:
            self.failures -= 1
            raise asyncpg.InterfaceError("corte simulado entre el ack y la marca")
        await super().mark_published(event_id, updated_ms, published_at)


def make_deps(pool: asyncpg.Pool, publisher: RecordingPublisher, store: PoolIngestStore | None = None) -> CycleDeps:
    """Dependencias reales (cliente HTTP y PostgreSQL) con publicador falso."""
    return CycleDeps(fetch=fetch_feed, store=store or PoolIngestStore(pool), publish=publisher,
                     now=lambda: datetime.now(timezone.utc))


def run_with_pool(db: TempDatabase, scenario: Callable[[asyncpg.Pool], Awaitable[Any]]) -> Any:
    """Ejecuta `scenario(pool)` con un pool del rol `observatory_producer`."""
    async def main() -> Any:
        pool = await db.producer_pool()
        try:
            return await scenario(pool)
        finally:
            await pool.close()
    return asyncio.run(main())


async def cycle(deps: CycleDeps, url: str) -> CycleResult:
    """Un ciclo contra el mock."""
    return await run_cycle(deps, feed_settings(url))


async def snapshot(db: TempDatabase) -> dict[str, list[tuple]]:
    """Contenido de `ingest_state`, `raw_response` y `exclusion`, leído con el administrador."""
    conn = await db.admin()
    try:
        return {name: [tuple(r.values()) for r in await conn.fetch(sql)] for name, sql in SNAPSHOT_QUERIES.items()}
    finally:
        await conn.close()


async def scalar(db: TempDatabase, sql: str, *args: Any) -> Any:
    """Un valor leído con el administrador."""
    conn = await db.admin()
    try:
        return await conn.fetchval(sql, *args)
    finally:
        await conn.close()
