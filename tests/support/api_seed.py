"""Datos SINTÉTICOS para las pruebas de la API: eventos `synthetic-…` y países de prueba.

Se insertan como administrador en `live.current_event` o `replay.current_event` (la API solo lee).
Todo evento sembrado lleva `is_synthetic = true`; ninguno es un dato real.
"""
from dataclasses import dataclass
from decimal import Decimal

import asyncpg

# Lista cerrada de esquemas: el nombre solo se inserta en el SQL desde este diccionario.
SCHEMAS = {"live": "live", "replay": "replay"}
SYNTHETIC_PREFIX = "synthetic-"
BASE_TIME_MS = 1_793_536_750_000
UPDATE_DELAY_MS = 1_000
SEED_SOURCE = "usgs_feed"

DATE_DIM_SQL = """
INSERT INTO public.date_dim (date_id, year, month, day, dow)
SELECT d, extract(year FROM d), extract(month FROM d), extract(day FROM d), extract(isodow FROM d)
FROM (SELECT ((timestamptz 'epoch' + $1::bigint * interval '1 millisecond') AT TIME ZONE 'UTC')::date AS d) AS t
ON CONFLICT (date_id) DO NOTHING
"""

COUNTRY_SQL = """
INSERT INTO public.country (country_id, name_es, admin, continent, subregion)
VALUES ($1, $2, $2, 'Test', $3)
ON CONFLICT (country_id) DO NOTHING
"""

EVENT_SQL = """
INSERT INTO {schema}.current_event (
    event_id, event_time, event_time_ms, updated_at, updated_ms, mag, mag_type, depth_km, lon, lat,
    place, status, url, sig, country_id, date_id, source, is_synthetic, ingested_at)
VALUES (
    $1, timestamptz 'epoch' + $2::bigint * interval '1 millisecond', $2,
    timestamptz 'epoch' + $3::bigint * interval '1 millisecond', $3,
    $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
    ((timestamptz 'epoch' + $2::bigint * interval '1 millisecond') AT TIME ZONE 'UTC')::date,
    $14, true, now())
"""


@dataclass(frozen=True)
class SeedEvent:
    """Un evento sintético a sembrar; `None` en mag, profundidad o país es un valor desconocido."""

    event_id: str
    time_ms: int = BASE_TIME_MS
    updated_ms: int | None = None
    mag: float | None = 2.5
    depth_km: float | None = 10.0
    country_id: str | None = None
    lon: float = 0.0
    lat: float = 0.0
    mag_type: str | None = "ml"
    place: str | None = "SINTÉTICO: lugar de prueba"
    status: str | None = "automatic"
    url: str | None = "https://example.invalid/synthetic"
    sig: int | None = 10


def synthetic_event(number: int, **overrides) -> SeedEvent:
    """Crea `synthetic-<number>`; los campos se sobrescriben por nombre."""
    return SeedEvent(event_id=f"{SYNTHETIC_PREFIX}{number}", **overrides)


def _decimal(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


async def seed_countries(conn: asyncpg.Connection, countries: dict[str, str]) -> None:
    """Inserta países de prueba (`ADM0_A3` -> nombre en español); la subregión es «Subregión <ADM0_A3>»."""
    for country_id, name in countries.items():
        await conn.execute(COUNTRY_SQL, country_id, name, f"Subregión {country_id}")


async def seed_events(conn: asyncpg.Connection, mode: str, events: list[SeedEvent]) -> None:
    """Inserta los eventos en `{mode}.current_event` (con su fila de `date_dim`) en una transacción."""
    sql = EVENT_SQL.format(schema=SCHEMAS[mode])
    async with conn.transaction():
        for event in events:
            updated_ms = event.updated_ms if event.updated_ms is not None else event.time_ms + UPDATE_DELAY_MS
            await conn.execute(DATE_DIM_SQL, event.time_ms)
            await conn.execute(sql, event.event_id, event.time_ms, updated_ms, _decimal(event.mag),
                               event.mag_type, _decimal(event.depth_km), event.lon, event.lat, event.place,
                               event.status, event.url, event.sig, event.country_id, SEED_SOURCE)
