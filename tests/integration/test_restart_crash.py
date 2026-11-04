"""Prueba 8 (SC-005): corte tras el commit de PostgreSQL y reinicio desde el último offset confirmado (T059).

Bucle real y PostgreSQL real; solo Kafka es simulado. El corte ocurre antes de la línea de decisión
y del commit del offset, así que el mensaje se reentrega y debe resultar en `redelivery_ignored`.
"""
import asyncio
import logging

import pytest

from consumer.counters import Counters
from tests.support import evidence
from tests.support.loop_harness import (
    ReplayConsumer, SimulatedCrash, crash_after_commit_at, open_pool, run_session,
)
from tests.support.messages import (
    E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message, faq12_sequence, to_bytes,
)
from tests.support.temp_database import TempDatabase

EVIDENCE_NAME = "bloque4_prueba8_corte_simulado"
TABLES = {
    "current_event": "SELECT * FROM live.current_event ORDER BY event_id",
    "event_version": "SELECT * FROM live.event_version ORDER BY event_id, updated_ms",
    "quarantine": "SELECT * FROM live.quarantine ORDER BY id",
}
INVALID_OFFSET = 5
RESET_SQL = (
    "TRUNCATE live.current_event, live.event_version, live.quarantine, "
    "replay.current_event, replay.event_version, replay.quarantine, public.date_dim RESTART IDENTITY"
)


def sequence() -> list[bytes]:
    """Los 5 mensajes de la FAQ 12 y, de sexto, un inválido (latitud 145) para cubrir la cuarentena."""
    invalid = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    invalid["event"]["geometry"]["coordinates"][1] = 145
    return [to_bytes(m) for m in faq12_sequence()] + [to_bytes(invalid)]


async def _snapshot(db: TempDatabase) -> dict[str, list[tuple]]:
    admin = await db.admin()
    try:
        return {name: [tuple(r.values()) for r in await admin.fetch(sql)] for name, sql in TABLES.items()}
    finally:
        await admin.close()


async def _reset(db: TempDatabase) -> None:
    admin = await db.admin()
    try:
        await admin.execute(RESET_SQL)
    finally:
        await admin.close()


async def _run_without_crash(db: TempDatabase, raws: list[bytes]) -> dict:
    pool = await open_pool(db)
    try:
        await run_session(pool, ReplayConsumer(raws, 0, asyncio.Event()), Counters())
    finally:
        await pool.close()
    return await _snapshot(db)


async def _run_with_crash(db: TempDatabase, raws: list[bytes], crash_offset: int) -> tuple[dict, int]:
    pool = await open_pool(db)
    try:
        first = ReplayConsumer(raws, 0, asyncio.Event())
        with pytest.raises(SimulatedCrash):
            await run_session(pool, first, Counters(), hook=crash_after_commit_at(crash_offset))
        restart_from = first.committed
        second = ReplayConsumer(raws, restart_from, asyncio.Event())
        await run_session(pool, second, Counters())
    finally:
        await pool.close()
    return await _snapshot(db), restart_from


@pytest.mark.parametrize("crash_offset", range(6))
def test_crash_after_the_postgres_commit_leaves_the_same_database_as_a_run_without_crash(
        db: TempDatabase, crash_offset: int, caplog):
    raws = sequence()
    expected = asyncio.run(_run_without_crash(db, raws))
    asyncio.run(_reset(db))
    with caplog.at_level(logging.INFO, logger="consumer.reporting"):
        actual, restart_from = asyncio.run(_run_with_crash(db, raws, crash_offset))
    assert restart_from == crash_offset, "el offset del mensaje cortado no se confirmó"
    assert actual == expected
    assert (len(actual["current_event"]), len(actual["event_version"]), len(actual["quarantine"])) == (2, 3, 1)
    crashed = [r.getMessage() for r in caplog.records
               if r.getMessage().startswith("decision=") and f"offset={crash_offset} " in r.getMessage() + " "]
    expected_decision = "quarantine_duplicate" if crash_offset == INVALID_OFFSET else "redelivery_ignored"
    assert len(crashed) == 1, "el corte ocurre antes de la línea de decisión: solo existe la de la reentrega"
    assert crashed[0].startswith(f"decision={expected_decision} ")


def test_record_evidence_of_the_crash_scenario(db: TempDatabase):
    raws = sequence()
    asyncio.run(_run_with_crash(db, raws, 2))

    async def record() -> None:
        admin = await db.admin()
        try:
            await evidence.record_query(admin, EVIDENCE_NAME,
                                        "SELECT event_id, updated_ms, mag, kafka_offset FROM live.event_version ORDER BY 1, 2",
                                        label="event_version tras corte en el offset 2 y reinicio")
            await evidence.record_query(admin, EVIDENCE_NAME,
                                        "SELECT event_id, mag, updated_ms FROM live.current_event ORDER BY 1",
                                        label="current_event tras corte en el offset 2 y reinicio")
        finally:
            await admin.close()

    asyncio.run(record())
