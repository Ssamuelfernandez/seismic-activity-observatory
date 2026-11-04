"""Secuencia de la FAQ 12 y versión antigua tardía contra PostgreSQL real (T039; pruebas 3 y 4)."""
import asyncio
from decimal import Decimal

from common.records import VersionOutcome
from tests.support import evidence
from tests.support.db_helpers import process_message
from tests.support.messages import (
    E1_UPDATED_1005,
    E1_UPDATED_1007,
    E1_UPDATED_1009,
    E2_UPDATED_1012,
    FAQ12_E1,
    FAQ12_E2,
    faq12_sequence,
    late_old_version_message,
)
from tests.support.temp_database import TempDatabase

# Las cuatro consultas de quickstart.md §5.
QUICKSTART_QUERIES = (
    "SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY event_id",
    "SELECT event_id, updated_ms, mag FROM live.event_version ORDER BY event_id, updated_ms",
    "SELECT count(*) AS current_rows FROM live.current_event",
    "SELECT count(*) AS version_rows FROM live.event_version",
)
EXPECTED_OUTCOMES = [
    VersionOutcome.NEW_EVENT,
    VersionOutcome.REDELIVERY,
    VersionOutcome.NEWER_VERSION,
    VersionOutcome.REDELIVERY,
    VersionOutcome.NEW_EVENT,
]
FAQ12_NAME = "bloque3_faq12"
VERSIONS_NAME = "bloque3_prueba3_4_versiones"


async def _record_all(db: TempDatabase, name: str, label: str) -> None:
    admin = await db.admin()
    try:
        for sql in QUICKSTART_QUERIES:
            await evidence.record_query(admin, name, sql, label=label)
    finally:
        await admin.close()


async def _write_sequence(db: TempDatabase, messages: list[dict]) -> list[VersionOutcome]:
    conn = await db.consumer()
    try:
        return [(await process_message(conn, m, offset)).outcome for offset, m in enumerate(messages)]
    finally:
        await conn.close()


async def _fetch(db: TempDatabase, sql: str) -> list[tuple]:
    admin = await db.admin()
    try:
        return [tuple(r.values()) for r in await admin.fetch(sql)]
    finally:
        await admin.close()


def test_faq12_sequence_gives_two_current_and_three_versions(db: TempDatabase) -> None:
    asyncio.run(_record_all(db, FAQ12_NAME, "antes"))
    outcomes = asyncio.run(_write_sequence(db, faq12_sequence()))
    asyncio.run(_record_all(db, FAQ12_NAME, "despues"))
    assert outcomes == EXPECTED_OUTCOMES
    current = asyncio.run(_fetch(db, "SELECT event_id, mag, updated_ms FROM live.current_event ORDER BY event_id"))
    assert current == [(FAQ12_E1, Decimal("4.6"), E1_UPDATED_1009), (FAQ12_E2, Decimal("3.1"), E2_UPDATED_1012)]
    versions = asyncio.run(_fetch(db, "SELECT event_id, updated_ms FROM live.event_version ORDER BY 1, 2"))
    assert versions == [(FAQ12_E1, E1_UPDATED_1005), (FAQ12_E1, E1_UPDATED_1009), (FAQ12_E2, E2_UPDATED_1012)]


def test_late_old_version_is_kept_in_history_but_not_current(db: TempDatabase) -> None:
    asyncio.run(_write_sequence(db, faq12_sequence()))
    asyncio.run(_record_all(db, VERSIONS_NAME, "antes"))
    outcomes = asyncio.run(_write_sequence_from(db, [late_old_version_message()], first_offset=5))
    asyncio.run(_record_all(db, VERSIONS_NAME, "despues"))
    assert outcomes == [VersionOutcome.LATE_OLD_VERSION]
    current = asyncio.run(_fetch(db, f"SELECT mag, updated_ms FROM live.current_event WHERE event_id = '{FAQ12_E1}'"))
    assert current == [(Decimal("4.6"), E1_UPDATED_1009)]
    versions = asyncio.run(_fetch(db, f"SELECT updated_ms FROM live.event_version WHERE event_id = '{FAQ12_E1}' ORDER BY 1"))
    assert versions == [(E1_UPDATED_1005,), (E1_UPDATED_1007,), (E1_UPDATED_1009,)]
    total = asyncio.run(_fetch(db, "SELECT count(*) FROM live.event_version"))
    assert total == [(4,)]


async def _write_sequence_from(db: TempDatabase, messages: list[dict], first_offset: int) -> list[VersionOutcome]:
    conn = await db.consumer()
    try:
        return [(await process_message(conn, m, first_offset + i)).outcome for i, m in enumerate(messages)]
    finally:
        await conn.close()
