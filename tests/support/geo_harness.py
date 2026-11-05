"""Ayudas de las pruebas de integración de geografía: pipeline real, catálogo real y base temporal.

Procesa mensajes con `process_record` (escritores reales del rol `observatory_consumer`) y el
localizador real ligado al índice del catálogo; cuenta las llamadas al localizador. Los mensajes
son SINTÉTICOS (`synthetic-geo-...`), de `tests/support/messages.py`.
"""
import asyncio
import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

from common.config import RetrySettings
from common.geo import CountryMatch, assign_country
from common.kafka_topics import TOPIC_LIVE
from common.records import ProcessingResult, RawRecord
from consumer.catalog_loader import load_country_catalog
from consumer.pipeline import PipelineDeps, bind_pool_writers, process_record
from consumer.resilience import RetryControl
from tests.support import evidence
from tests.support.messages import to_bytes
from tests.support.temp_database import TempDatabase

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "catalogo" / "paises.geojson"
FIXED_NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
RETRY = RetrySettings(1, 30)
PARTITION = 0
POOL_MAX = 2
VERSION_STEP_MS = 60_000


class LocatorSpy:
    """Localizador real que anota las coordenadas con las que se le llama."""

    def __init__(self, index: Any) -> None:
        self.index = index
        self.calls: list[tuple[float, float]] = []

    def __call__(self, lon: float, lat: float) -> CountryMatch:
        self.calls.append((lon, lat))
        return assign_country(self.index, lon, lat)


def to_raw(message: dict) -> bytes:
    """Serializa un mensaje como el productor (JSON UTF-8; admite NaN como Python)."""
    return to_bytes(message)


def newer_version(message: dict, lon: float, lat: float, steps: int = 1) -> dict:
    """Copia del mensaje con `updated` mayor (o menor si `steps < 0`) y otras coordenadas."""
    clone = copy.deepcopy(message)
    clone["event"]["properties"]["updated"] += steps * VERSION_STEP_MS
    clone["event"]["geometry"]["coordinates"][:2] = [lon, lat]
    return clone


async def process_raws(db: TempDatabase, raws: list[bytes | None], start_offset: int = 0
                       ) -> tuple[list[ProcessingResult], list[tuple[float, float]]]:
    """Carga el catálogo real y procesa cada valor con el pipeline real.

    Devuelve los resultados y las llamadas al localizador. La carga es repetible, así que
    se puede invocar varias veces en la misma prueba (`public.country` se vacía entre pruebas).
    """
    pool = await asyncpg.create_pool(host=db.host, port=db.port, database=db.name, user=db.consumer_user,
                                     password=db.consumer_password, min_size=1, max_size=POOL_MAX)
    try:
        index, _ = await load_country_catalog(pool, CATALOG_PATH)
        spy = LocatorSpy(index)
        write_event, write_quarantine = bind_pool_writers(pool)
        deps = PipelineDeps(write_event, write_quarantine, RetryControl(RETRY, asyncio.Event()), spy,
                            clock=lambda: FIXED_NOW)
        results = [await process_record(RawRecord(TOPIC_LIVE, PARTITION, start_offset + n, b"k", raw), deps)
                   for n, raw in enumerate(raws)]
        return results, spy.calls
    finally:
        await pool.close()


def process_messages(db: TempDatabase, messages: list[dict], start_offset: int = 0
                     ) -> tuple[list[ProcessingResult], list[tuple[float, float]]]:
    """Versión síncrona de `process_raws` para mensajes ya construidos."""
    return asyncio.run(process_raws(db, [to_raw(m) for m in messages], start_offset))


async def _fetch(db: TempDatabase, sql: str, args: tuple) -> list[tuple]:
    conn = await db.admin()
    try:
        return [tuple(r.values()) for r in await conn.fetch(sql, *args)]
    finally:
        await conn.close()


def admin_rows(db: TempDatabase, sql: str, *args: Any) -> list[tuple]:
    """Filas de una consulta ejecutada con el administrador."""
    return asyncio.run(_fetch(db, sql, args))


async def _record(db: TempDatabase, name: str, sql: str, label: str) -> list[tuple]:
    conn = await db.admin()
    try:
        return await evidence.record_query(conn, name, sql, label=label)
    finally:
        await conn.close()


def record_rows(db: TempDatabase, name: str, sql: str, label: str) -> list[tuple]:
    """Ejecuta la consulta, la guarda como evidencia (`.sql` y `.out`) y devuelve las filas."""
    return asyncio.run(_record(db, name, sql, label))
