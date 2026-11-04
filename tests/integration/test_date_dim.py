"""Base temporal `public.date_dim` contra PostgreSQL real, ejercitando el escritor (T068, FR-019)."""
import asyncio
import dataclasses
from datetime import date, datetime, timezone

import asyncpg

from common.decode import decode_value
from common.records import MessageRef
from common.transform import build_event_rows
from common.validation import validate_message
from consumer.writer import write_event
from common.kafka_topics import TOPIC_LIVE
from tests.support.db_helpers import NOW, process_message, to_raw
from tests.support.messages import (
    E1_TIME_MS,
    E1_UPDATED_1005,
    E2_TIME_MS,
    E2_UPDATED_1012,
    FAQ12_E1,
    FAQ12_E2,
    build_synthetic_message,
)
from tests.support.temp_database import TempDatabase

NEW_DAY_ID = "synthetic-date-new-day"
OLD_DAY_ID = "synthetic-date-1999"
ROLLBACK_ID = "synthetic-date-rollback"
NEXT_DAY_MS = E1_TIME_MS + 24 * 3600 * 1000
FIRST_ISO_DAY_MS = int(datetime(1999, 12, 31, 12, 0, tzinfo=timezone.utc).timestamp() * 1000)
FRIDAY_ISO = 5
WEDNESDAY_ISO = 3
DATE_SQL = "SELECT date_id, year, month, day, dow FROM public.date_dim ORDER BY date_id"


async def _run(db: TempDatabase, action):
    conn = await db.consumer()
    try:
        return await action(conn)
    finally:
        await conn.close()


async def _admin(db: TempDatabase, sql: str) -> list[tuple]:
    admin = await db.admin()
    try:
        return [tuple(r.values()) for r in await admin.fetch(sql)]
    finally:
        await admin.close()


async def _write_same_day(conn) -> None:
    await process_message(conn, build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2), 0)
    await process_message(conn, build_synthetic_message(FAQ12_E2, E2_TIME_MS, E2_UPDATED_1012, 3.1), 1)


def test_same_utc_day_leaves_one_date_row(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_same_day))
    assert asyncio.run(_admin(db, DATE_SQL)) == [(date(2026, 11, 4), 2026, 11, 4, WEDNESDAY_ISO)]
    assert asyncio.run(_admin(db, "SELECT count(*) FROM live.current_event")) == [(2,)]


async def _write_new_day(conn) -> None:
    await process_message(conn, build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2), 0)
    await process_message(conn, build_synthetic_message(NEW_DAY_ID, NEXT_DAY_MS, NEXT_DAY_MS, 4.2), 1)


def test_new_utc_day_creates_its_row_with_the_event(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_new_day))
    rows = asyncio.run(_admin(db, "SELECT c.event_id, c.date_id, d.date_id FROM live.current_event c "
                                  "JOIN public.date_dim d ON d.date_id = c.date_id ORDER BY c.event_id"))
    assert rows == [(NEW_DAY_ID, date(2026, 11, 5), date(2026, 11, 5)),
                    (FAQ12_E1, date(2026, 11, 4), date(2026, 11, 4))]
    assert asyncio.run(_admin(db, "SELECT count(*) FROM public.date_dim")) == [(2,)]


async def _write_known_dates(conn) -> None:
    await process_message(conn, build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2), 0)
    await process_message(conn, build_synthetic_message(OLD_DAY_ID, FIRST_ISO_DAY_MS, FIRST_ISO_DAY_MS, 1.0), 1)


def test_year_month_day_and_iso_weekday(db: TempDatabase) -> None:
    asyncio.run(_run(db, _write_known_dates))
    assert asyncio.run(_admin(db, DATE_SQL)) == [
        (date(1999, 12, 31), 1999, 12, 31, FRIDAY_ISO),
        (date(2026, 11, 4), 2026, 11, 4, WEDNESDAY_ISO),
    ]


async def _write_failing_event(conn) -> type[Exception] | None:
    message = build_synthetic_message(ROLLBACK_ID, FIRST_ISO_DAY_MS, FIRST_ISO_DAY_MS, 1.0)
    valid = validate_message(decode_value(to_raw(message)), TOPIC_LIVE)
    rows = build_event_rows(valid, MessageRef(TOPIC_LIVE, 0, 0), NOW)
    broken = dataclasses.replace(rows, current={**rows.current, "event_time": None})
    try:
        await write_event(conn, broken, "live")
    except asyncpg.PostgresError as error:
        return type(error)
    return None


def test_rollback_leaves_the_day_uncreated(db: TempDatabase) -> None:
    error_type = asyncio.run(_run(db, _write_failing_event))
    assert error_type is asyncpg.NotNullViolationError
    assert asyncio.run(_admin(db, "SELECT count(*) FROM public.date_dim")) == [(0,)]
    assert asyncio.run(_admin(db, "SELECT count(*) FROM live.event_version")) == [(0,)]
    assert asyncio.run(_admin(db, "SELECT count(*) FROM live.current_event")) == [(0,)]
