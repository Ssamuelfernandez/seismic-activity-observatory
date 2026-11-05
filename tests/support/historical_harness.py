"""Ayudas de las pruebas de integración del histórico: carga real en una base temporal.

Cada llamada abre un pool nuevo con el rol `observatory_consumer` (equivale a reiniciar la
conexión), carga el catálogo real y ejecuta `load_historical` con el pipeline real. Datos SINTÉTICOS.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import asyncpg

from common.config import RetrySettings
from common.geo import assign_country
from consumer.catalog_loader import load_country_catalog
from consumer.pipeline import PipelineDeps, bind_pool_writers
from consumer.resilience import RetryControl
from historical.loader import LoadSummary, load_historical
from consumer import queries
from historical.verify import VerifyResult, verify_load
from tests.support.geo_harness import CATALOG_PATH
from tests.support.temp_database import TempDatabase

FIXED_NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
RETRY = RetrySettings(1, 30)
POOL_MAX = 2


@dataclass(frozen=True)
class LoadOutcome:
    """Resumen de la carga, verificación y huella de las tres tablas tras ella."""

    summary: LoadSummary
    verify: VerifyResult
    fingerprint: dict[str, tuple[int, str]]


async def _admin_fingerprint(db: TempDatabase) -> dict[str, tuple[int, str]]:
    """Huella de las tres tablas con el administrador (el consumidor no lee la cuarentena)."""
    statements = {"current_event": queries.FINGERPRINT_CURRENT, "event_version": queries.FINGERPRINT_VERSION,
                  "quarantine": queries.FINGERPRINT_QUARANTINE}
    conn = await db.admin()
    try:
        return {name: tuple((await conn.fetchrow(sql))[:2]) for name, sql in statements.items()}
    finally:
        await conn.close()


async def _load(db: TempDatabase, directory: Path, is_synthetic: bool) -> LoadOutcome:
    pool = await asyncpg.create_pool(host=db.host, port=db.port, database=db.name, user=db.consumer_user,
                                     password=db.consumer_password, min_size=1, max_size=POOL_MAX)
    try:
        index, _ = await load_country_catalog(pool, CATALOG_PATH)
        write_event, write_quarantine = bind_pool_writers(pool)
        deps = PipelineDeps(write_event, write_quarantine, RetryControl(RETRY, asyncio.Event()),
                            lambda lon, lat: assign_country(index, lon, lat), clock=lambda: FIXED_NOW)
        summary = await load_historical(directory, deps, is_synthetic)
        return LoadOutcome(summary, await verify_load(pool, summary.event_ids, summary.quarantined_ids),
                           await _admin_fingerprint(db))
    finally:
        await pool.close()


def load_directory(db: TempDatabase, directory: Path, is_synthetic: bool = True) -> LoadOutcome:
    """Carga el directorio con un pool nuevo y devuelve resumen, verificación y huella."""
    return asyncio.run(_load(db, directory, is_synthetic))
