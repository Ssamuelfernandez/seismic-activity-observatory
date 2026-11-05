"""Banco de pruebas de la API: el rol real `observatory_api` lee lo sembrado en `live` y `replay` (T005)."""
import asyncio

from tests.support.api_seed import BASE_TIME_MS, seed_countries, seed_events, synthetic_event
from tests.support.temp_database import TempDatabase

READ_SQL = """
SELECT e.event_id, e.mag, e.depth_km, e.is_synthetic, c.name_es
FROM {schema}.current_event e LEFT JOIN public.country c ON c.country_id = e.country_id
ORDER BY e.event_id
"""


async def _scenario(db: TempDatabase) -> dict[str, list]:
    admin = await db.admin()
    try:
        await seed_countries(admin, {"ESP": "España"})
        await seed_events(admin, "live", [
            synthetic_event(1, country_id="ESP"),
            synthetic_event(2, mag=None, depth_km=None, time_ms=BASE_TIME_MS + 1000),
        ])
        await seed_events(admin, "replay", [synthetic_event(3, mag=-0.06, depth_km=-1.5)])
    finally:
        await admin.close()
    pool = await db.api_pool()
    try:
        async with pool.acquire() as conn:
            return {schema: [tuple(r.values()) for r in await conn.fetch(READ_SQL.format(schema=schema))]
                    for schema in ("live", "replay")}
    finally:
        await pool.close()


def test_api_role_reads_seeded_events_in_both_modes(db: TempDatabase):
    rows = asyncio.run(_scenario(db))
    assert [r[0] for r in rows["live"]] == ["synthetic-1", "synthetic-2"]
    assert [r[0] for r in rows["replay"]] == ["synthetic-3"]
    first, second = rows["live"]
    assert (first[3], first[4]) == (True, "España")
    assert (second[1], second[2], second[4]) == (None, None, None)
    assert float(rows["replay"][0][1]) == -0.06
    assert all(row[3] is True for mode_rows in rows.values() for row in mode_rows)
