"""Permisos del rol real `observatory_consumer` sobre la base temporal (T037).

Las aserciones (a)-(e) se registran en `roles_consumidor.out`. No se concede ningún permiso.
"""
import asyncio

import asyncpg

from common.records import QuarantineRow
from consumer import queries
from tests.support.temp_database import TempDatabase
from tests.support import evidence
from tests.support.db_helpers import NOW, process_message
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message

NAME = "roles_consumidor"
INSUFFICIENT_PRIVILEGE = "42501"
ROW = QuarantineRow(None, "invalid_json", None, "{x", "a" * 64, None, "earthquakes.live", 0, 1, NOW, True)
OTHER_HASH = "b" * 64
TARGETED_CONFLICT = queries.quarantine_insert("live").replace(
    "ON CONFLICT DO NOTHING", "ON CONFLICT (original_sha256, reason) DO NOTHING")


def _values(row: QuarantineRow) -> tuple:
    return (row.event_id, row.reason, row.original, row.raw_text, row.original_sha256, row.source,
            row.kafka_topic, row.kafka_partition, row.kafka_offset, row.received_at, row.is_synthetic)


async def _outcome(conn: asyncpg.Connection, sql: str, *args) -> str:
    """Ejecuta una sentencia y devuelve su etiqueta de estado o el SQLSTATE si falla."""
    try:
        return await conn.execute(sql, *args)
    except asyncpg.PostgresError as error:
        return error.sqlstate


async def _scenario(db: TempDatabase) -> dict[str, str]:
    results: dict[str, str] = {}
    conn = await db.consumer()
    try:
        results["a"] = await _outcome(conn, "SELECT count(*) FROM live.quarantine")
        results["b1"] = await _outcome(conn, queries.quarantine_insert("live"), *_values(ROW))
        results["b2"] = await _outcome(conn, queries.quarantine_insert("live"), *_values(ROW))
        other = _values(ROW)[:4] + (OTHER_HASH,) + _values(ROW)[5:]
        results["c"] = await _outcome(conn, TARGETED_CONFLICT, *other)
        results["d"] = await _outcome(
            conn, "INSERT INTO ingest.ingest_state (event_id, last_updated_ms, published_at) VALUES ('x', 1, now())")
        date_args = (NOW.date(), 2026, 11, 5, 4)
        results["date_1"] = await _outcome(conn, queries.DATE_DIM_INSERT, *date_args)
        results["date_2"] = await _outcome(conn, queries.DATE_DIM_INSERT, *date_args)
        results["country_1"] = await _outcome(conn, queries.COUNTRY_UPSERT, "ZZZ", "Pais", "Test", "Test", "Test")
        results["country_2"] = await _outcome(conn, queries.COUNTRY_UPSERT, "ZZZ", "Pais 2", "Test", "Test", "Test")
        await process_message(conn, build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2), 1)
        results["version_select"] = str(await conn.fetchval("SELECT count(*) FROM live.event_version"))
        results["version_update"] = await _outcome(conn, "UPDATE live.event_version SET mag = 1")
        results["current_update"] = await _outcome(conn, "UPDATE live.current_event SET place = 'otro'")
    finally:
        await conn.close()
    return results


def test_consumer_role_permissions(db: TempDatabase) -> None:
    r = asyncio.run(_scenario(db))
    record = evidence.record_text
    record(NAME, f"SELECT en live.quarantine -> sqlstate {r['a']}", "aserción (a)")
    record(NAME, f"sentencia de producción (sin destino): primera vez -> {r['b1']}; duplicado -> {r['b2']}",
           "aserción (b)")
    record(NAME, f"variante con destino (original_sha256, reason) -> {r['c']}", "aserción (c)")
    record(NAME, f"INSERT en ingest.ingest_state -> sqlstate {r['d']}", "aserción (d)")
    record(NAME, f"event_version: INSERT ok (filas leídas con SELECT: {r['version_select']}); "
                 f"UPDATE -> sqlstate {r['version_update']}; current_event UPDATE -> {r['current_update']}; "
                 f"date_dim INSERT -> {r['date_1']} y {r['date_2']}; country INSERT -> {r['country_1']}, "
                 f"UPDATE -> {r['country_2']}", "aserción (e)")
    assert r["a"] == INSUFFICIENT_PRIVILEGE
    assert (r["b1"], r["b2"]) == ("INSERT 0 1", "INSERT 0 0")
    assert r["c"] == INSUFFICIENT_PRIVILEGE
    assert r["d"] == INSUFFICIENT_PRIVILEGE
    assert r["version_select"] == "1" and r["version_update"] == INSUFFICIENT_PRIVILEGE
    assert r["current_update"] == "UPDATE 1"
    assert (r["date_1"], r["date_2"]) == ("INSERT 0 1", "INSERT 0 0")
    assert (r["country_1"], r["country_2"]) == ("INSERT 0 1", "INSERT 0 1")
