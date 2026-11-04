"""Nulos, negativos, tiempos UTC y campos copiados del sobre contra PostgreSQL real (T041)."""
import asyncio
import json
from datetime import date, datetime, timezone
from decimal import Decimal

from common.kafka_topics import TOPIC_REPLAY
from common.transform import MAX_EPOCH_MS, MIN_EPOCH_MS
from tests.support.db_helpers import process_message
from tests.support.messages import (
    E1_TIME_MS,
    E1_UPDATED_1005,
    E2_TIME_MS,
    E2_UPDATED_1012,
    FAQ12_E1,
    FAQ12_E2,
    INGESTED_AT,
    REPLAY_AT,
    build_event,
    build_message,
    build_real_looking_message,
    build_synthetic_message,
)
from tests.support.temp_database import TempDatabase

REAL_ID = "test-real-looking-not-published"
MIN_ID = "synthetic-min-time"
MAX_ID = "synthetic-max-time"
REPLAY_ID = "synthetic-replay"
LAST_VALID_MS = MAX_EPOCH_MS - 1
INGESTED = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
REPLAYED = datetime(2026, 11, 4, 10, 30, 0, tzinfo=timezone.utc)
COHERENCE_SQL = {
    "current_event": "SELECT bool_and(event_time = to_timestamp(event_time_ms / 1000.0) "
                     "AND updated_at = to_timestamp(updated_ms / 1000.0)) FROM live.current_event",
    # event_version no guarda event_time_ms: su coherencia con el original se comprueba con updated_ms.
    "event_version": "SELECT bool_and(updated_at = to_timestamp(updated_ms / 1000.0)) FROM live.event_version",
}


async def _run(db: TempDatabase, action):
    conn = await db.consumer()
    try:
        return await action(conn)
    finally:
        await conn.close()


async def _admin(db: TempDatabase, sql: str, *args) -> list[tuple]:
    admin = await db.admin()
    try:
        return [tuple(r.values()) for r in await admin.fetch(sql, *args)]
    finally:
        await admin.close()


async def _write_null_and_negative(conn) -> None:
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, None)
    message["event"]["properties"].update({"place": None, "status": None, "url": None, "sig": None, "magType": None})
    message["event"]["geometry"]["coordinates"] = [10.5, -20.25, None]
    await process_message(conn, message, 0)
    negative = build_synthetic_message(FAQ12_E2, E1_TIME_MS, E1_UPDATED_1005, -0.06)
    negative["event"]["geometry"]["coordinates"] = [10.5, -20.25, -0.18]
    await process_message(conn, negative, 1)


def test_null_magnitude_is_null_and_negatives_are_kept(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_null_and_negative))
    for table in ("current_event", "event_version"):
        rows = asyncio.run(_admin(db, f"SELECT event_id, mag, depth_km FROM live.{table} ORDER BY event_id"))
        assert rows == [(FAQ12_E1, None, None), (FAQ12_E2, Decimal("-0.06"), Decimal("-0.18"))]
    nulls = asyncio.run(_admin(db, "SELECT place, status, url, sig, mag_type FROM live.current_event "
                                   f"WHERE event_id = '{FAQ12_E1}'"))
    assert nulls == [(None, None, None, None, None)]


async def _write_extremes(conn) -> None:
    await process_message(conn, build_synthetic_message(MIN_ID, MIN_EPOCH_MS, MIN_EPOCH_MS, 1.0), 0)
    await process_message(conn, build_synthetic_message(MAX_ID, LAST_VALID_MS, LAST_VALID_MS, 1.0), 1)


def test_time_range_extremes_are_accepted_by_the_ddl_check(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_extremes))
    for table in ("current_event", "event_version"):
        assert asyncio.run(_admin(db, COHERENCE_SQL[table])) == [(True,)]
    rows = asyncio.run(_admin(db, "SELECT event_id, event_time, date_id FROM live.current_event ORDER BY event_id"))
    assert rows == [
        (MAX_ID, datetime(2999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc), date(2999, 12, 31)),
        (MIN_ID, datetime(1000, 1, 1, tzinfo=timezone.utc), date(1000, 1, 1)),
    ]
    assert asyncio.run(_admin(db, "SELECT count(*) FROM public.date_dim")) == [(2,)]


async def _write_one(conn) -> None:
    # E2 ocurre a las 10:11, distinta de la ingesta (10:00) y de la recepción (2026-11-05).
    await process_message(conn, build_synthetic_message(FAQ12_E2, E2_TIME_MS, E2_UPDATED_1012, 3.1), 0)


def test_date_country_and_reception_times(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_one))
    row = asyncio.run(_admin(db, "SELECT c.country_id, c.date_id, d.date_id, d.dow, c.event_time <> c.ingested_at, "
                                 "v.received_at <> v.event_time, v.received_at <> c.ingested_at "
                                 "FROM live.current_event c JOIN live.event_version v USING (event_id) "
                                 "LEFT JOIN public.date_dim d ON d.date_id = c.date_id"))
    assert row == [(None, date(2026, 11, 4), date(2026, 11, 4), 3, True, True, True)]


async def _write_envelope_cases(conn) -> None:
    event = build_event(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    await process_message(conn, build_message(event), 0)
    replay = build_message(build_event(REPLAY_ID, E1_TIME_MS, E1_UPDATED_1005, 4.2), mode="replay", replay_at=REPLAY_AT)
    await process_message(conn, replay, 1, topic=TOPIC_REPLAY)
    real = build_real_looking_message(REAL_ID, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    await process_message(conn, real, 2)


def test_envelope_fields_and_original_are_copied(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_envelope_cases))
    live = asyncio.run(_admin(db, "SELECT event_id, source, ingested_at, replay_at, is_synthetic "
                                  "FROM live.current_event ORDER BY event_id"))
    assert live == [
        (FAQ12_E1, "replay_demo", INGESTED, None, True),
        (REAL_ID, "usgs_feed", INGESTED, None, False),
    ]
    replay = asyncio.run(_admin(db, "SELECT source, ingested_at, replay_at, is_synthetic FROM replay.current_event"))
    assert replay == [("replay_demo", INGESTED, REPLAYED, True)]
    versions = asyncio.run(_admin(db, "SELECT event_id, source, is_synthetic FROM live.event_version ORDER BY 1"))
    assert versions == [(FAQ12_E1, "replay_demo", True), (REAL_ID, "usgs_feed", False)]
    expected = json.dumps(build_event(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2))
    equal = asyncio.run(_admin(db, "SELECT original = $1::jsonb FROM live.event_version WHERE event_id = $2",
                               expected, FAQ12_E1))
    assert equal == [(True,)]
    assert INGESTED_AT.endswith("Z")
