"""Idempotencia, conflictos, nulos y atomicidad del escritor (T040; prueba 2)."""
import asyncio
from decimal import Decimal

import asyncpg

from common.records import VersionOutcome
from tests.support import evidence
from tests.support.db_helpers import process_message
from tests.support.messages import (
    E1_TIME_MS,
    E1_UPDATED_1005,
    E1_UPDATED_1009,
    E2_TIME_MS,
    E2_UPDATED_1012,
    FAQ12_E1,
    FAQ12_E2,
    build_synthetic_message,
    faq12_sequence,
)
from tests.support.temp_database import TempDatabase

REPEATS = 100
EVIDENCE_NAME = "bloque3_prueba2_reenvio"
COUNTS_SQL = (
    "SELECT 'current_event' AS tabla, count(*) AS filas FROM live.current_event "
    "UNION ALL SELECT 'event_version', count(*) FROM live.event_version "
    "UNION ALL SELECT 'quarantine', count(*) FROM live.quarantine "
    "UNION ALL SELECT 'date_dim', count(*) FROM public.date_dim ORDER BY 1"
)
STATE_SQL = "SELECT * FROM live.current_event ORDER BY event_id"
ATOMIC_ID = "synthetic-atomic"
TEMP_CHECK = "tmp_reject_atomic_id"


async def _with_consumer(db: TempDatabase, action):
    conn = await db.consumer()
    try:
        return await action(conn)
    finally:
        await conn.close()


async def _admin_fetch(db: TempDatabase, sql: str, *args) -> list[tuple]:
    admin = await db.admin()
    try:
        return [tuple(r.values()) for r in await admin.fetch(sql, *args)]
    finally:
        await admin.close()


async def _first_pass_and_repeats(db: TempDatabase) -> tuple[list, list, list, list]:
    admin = await db.admin()
    try:
        async def first_pass(conn):
            for offset, message in enumerate(faq12_sequence()):
                await process_message(conn, message, offset)
        await _with_consumer(db, first_pass)
        before = await evidence.record_query(admin, EVIDENCE_NAME, COUNTS_SQL, label="antes de las 100 repeticiones")
        state_before = [tuple(r.values()) for r in await admin.fetch(STATE_SQL)]

        async def repeats(conn):
            offset = 100
            for _ in range(REPEATS):
                for message in faq12_sequence():
                    result = await process_message(conn, message, offset)
                    assert result.outcome is VersionOutcome.REDELIVERY
                    offset += 1
        await _with_consumer(db, repeats)
        after = await evidence.record_query(admin, EVIDENCE_NAME, COUNTS_SQL, label="despues de las 100 repeticiones")
        state_after = [tuple(r.values()) for r in await admin.fetch(STATE_SQL)]
        return before, after, state_before, state_after
    finally:
        await admin.close()


def test_hundred_resends_change_nothing(db: TempDatabase) -> None:
    before, after, state_before, state_after = asyncio.run(_first_pass_and_repeats(db))
    assert before == after
    assert dict(before) == {"current_event": 2, "date_dim": 1, "event_version": 3, "quarantine": 0}
    assert state_before == state_after


async def _conflict(db: TempDatabase) -> tuple[VersionOutcome, list, list]:
    original = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    different = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.3)

    async def write(conn):
        await process_message(conn, original, 0)
        return (await process_message(conn, different, 1)).outcome
    outcome = await _with_consumer(db, write)
    stored = await _admin_fetch(db, "SELECT original->'properties'->>'mag' FROM live.event_version")
    counts = await _admin_fetch(db, "SELECT count(*) FROM live.event_version")
    return outcome, stored, counts


def test_same_updated_different_content_keeps_first(db: TempDatabase) -> None:
    outcome, stored, counts = asyncio.run(_conflict(db))
    assert outcome is VersionOutcome.SAME_UPDATED_CONFLICT
    assert stored == [("4.2",)]
    assert counts == [(1,)]


async def _null_mag_flow(db: TempDatabase) -> list[tuple]:
    async def write(conn):
        await process_message(conn, build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, None), 0)
        await process_message(conn, build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1009, 4.6), 1)
        await process_message(conn, build_synthetic_message(FAQ12_E2, E2_TIME_MS, E2_UPDATED_1012, 3.1), 2)
        await process_message(conn, build_synthetic_message(FAQ12_E2, E2_TIME_MS, E2_UPDATED_1012 + 1, None), 3)
    await _with_consumer(db, write)
    return await _admin_fetch(db, "SELECT event_id, mag FROM live.current_event ORDER BY event_id")


def test_null_then_value_and_reverse_follow_updated(db: TempDatabase) -> None:
    rows = asyncio.run(_null_mag_flow(db))
    assert rows == [(FAQ12_E1, Decimal("4.6")), (FAQ12_E2, None)]


async def _atomic_failure(db: TempDatabase) -> tuple[BaseException | None, list, list]:
    admin = await db.admin()
    try:
        await admin.execute(f"ALTER TABLE live.current_event ADD CONSTRAINT {TEMP_CHECK} CHECK (event_id <> '{ATOMIC_ID}')")
        try:
            async def write(conn):
                try:
                    await process_message(conn, build_synthetic_message(ATOMIC_ID, E1_TIME_MS, E1_UPDATED_1005, 4.0), 0)
                except asyncpg.PostgresError as error:
                    return error
                return None
            error = await _with_consumer(db, write)
        finally:
            await admin.execute(f"ALTER TABLE live.current_event DROP CONSTRAINT IF EXISTS {TEMP_CHECK}")
        versions = [tuple(r.values()) for r in await admin.fetch("SELECT * FROM live.event_version")]
        dates = [tuple(r.values()) for r in await admin.fetch("SELECT * FROM public.date_dim")]
        return error, versions, dates
    finally:
        await admin.close()


def test_failure_in_current_event_rolls_back_version(db: TempDatabase) -> None:
    error, versions, dates = asyncio.run(_atomic_failure(db))
    assert isinstance(error, asyncpg.CheckViolationError)
    assert versions == []
    assert dates == []
