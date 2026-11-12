"""Replay contra PostgreSQL real: 26 mensajes dan 22/24/0 en el esquema `replay` (T048; J3, J5, J6).

Los 20 eventos reales salen de `data/historical/` (zona `chile-norte`); el bloque controlado
son 6 mensajes SINTÉTICOS. Sin Kafka: cada mensaje pasa por las funciones reales del consumidor.
"""
import asyncio
from collections import Counter
from datetime import datetime, timezone

from common.kafka_topics import TOPIC_REPLAY
from common.records import VersionOutcome
from tests.support.db_helpers import process_raw, to_raw
from tests.support.replay_harness import SYNTHETIC_PREFIX, build_replay_messages, process_messages

E1 = "synthetic-replay-e1"


async def _counts(conn) -> dict[str, int]:
    """Filas de cada tabla de eventos y de cuarentena en ambos esquemas."""
    tables = ("live.current_event", "live.event_version", "live.quarantine",
              "replay.current_event", "replay.event_version", "replay.quarantine")
    return {table: await conn.fetchval(f"SELECT count(*) FROM {table}") for table in tables}


async def _run_replay(db, passes: int = 1):
    """Procesa los 26 mensajes `passes` veces y devuelve resultados, recuentos y filas del esquema replay."""
    messages = build_replay_messages()
    consumer = await db.consumer()
    admin = await db.admin()
    try:
        results = []
        for number in range(passes):
            results.append(await process_messages(consumer, messages, first_offset=number * len(messages)))
        rows = await admin.fetch("SELECT event_id, source, replay_at, is_synthetic, updated_ms "
                                 "FROM replay.current_event ORDER BY event_id")
        return messages, results, await _counts(admin), rows
    finally:
        await consumer.close()
        await admin.close()


def test_26_messages_give_22_24_0_in_replay_and_nothing_in_live(db):
    messages, results, counts, rows = asyncio.run(_run_replay(db))
    assert len(messages) == 26
    assert counts["replay.current_event"] == 22
    assert counts["replay.event_version"] == 24
    assert counts["replay.quarantine"] == 0
    assert counts["live.current_event"] == counts["live.event_version"] == counts["live.quarantine"] == 0
    outcomes = Counter(result.outcome for result in results[0])
    assert outcomes[VersionOutcome.REDELIVERY] == 2
    assert outcomes[VersionOutcome.NEWER_VERSION] == 1
    assert outcomes[VersionOutcome.LATE_OLD_VERSION] == 1


def test_e1_keeps_the_greatest_updated_and_every_row_has_replay_at_and_source(db):
    _, _, _, rows = asyncio.run(_run_replay(db))
    e1 = next(row for row in rows if row["event_id"] == E1)
    assert e1["updated_ms"] == max(row["updated_ms"] for row in rows if row["event_id"] == E1)
    assert e1["updated_ms"] == 1738231740000  # 2025-01-30T10:09:00Z
    assert all(row["replay_at"] is not None for row in rows)
    assert all(row["source"] == "replay_demo" for row in rows)
    synthetic = {row["event_id"] for row in rows if row["is_synthetic"]}
    assert synthetic == {"synthetic-replay-e1", "synthetic-replay-e2"}
    assert all(row["event_id"].startswith(SYNTHETIC_PREFIX) == row["is_synthetic"] for row in rows)


def test_repeating_the_26_messages_keeps_counts_and_replay_at(db):
    _, first, counts_once, rows_once = asyncio.run(_run_replay(db))
    db_counts_after_two, rows_twice = _repeat(db)
    assert db_counts_after_two == counts_once
    assert [(r["event_id"], r["replay_at"]) for r in rows_twice] == [(r["event_id"], r["replay_at"]) for r in rows_once]
    assert Counter(r.outcome for r in first[0])[VersionOutcome.NEW_EVENT] == 22


def _repeat(db):
    """Vuelve a procesar los 26 mensajes con `replay_at` posteriores sobre la base ya poblada."""
    later = build_replay_messages(started_at=datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc))

    async def scenario():
        consumer = await db.consumer()
        admin = await db.admin()
        try:
            await process_messages(consumer, later, first_offset=100)
            rows = await admin.fetch("SELECT event_id, replay_at FROM replay.current_event ORDER BY event_id")
            return await _counts(admin), rows
        finally:
            await consumer.close()
            await admin.close()

    return asyncio.run(scenario())


def test_live_mode_message_in_the_replay_topic_goes_to_replay_quarantine(db):
    message = {**build_replay_messages()[0], "mode": "live"}

    async def scenario():
        consumer = await db.consumer()
        admin = await db.admin()
        try:
            result = await process_raw(consumer, to_raw(message), 0, TOPIC_REPLAY)
            reasons = [r["reason"] for r in await admin.fetch("SELECT reason FROM replay.quarantine")]
            return result, reasons, await _counts(admin)
        finally:
            await consumer.close()
            await admin.close()

    result, reasons, counts = asyncio.run(scenario())
    assert result.reason == "mode_topic_mismatch" and reasons == ["mode_topic_mismatch"]
    assert counts["replay.current_event"] == 0 and counts["live.quarantine"] == 0
