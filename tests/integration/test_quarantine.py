"""Cuarentena, contenido hostil y errores de base de datos contra PostgreSQL real (T042; prueba 6)."""
import asyncio
import copy
import hashlib
import json
import re

import asyncpg

from common.decode import decode_value
from common.kafka_topics import TOPIC_LIVE, TOPIC_REPLAY
from common.quarantine_row import build_quarantine_row
from common.records import MessageRef, ResultKind
from common.transform import build_event_rows
from common.validation import validate_message
from consumer.db_errors import is_content_error
from consumer.writer import write_event, write_quarantine
from tests.support import evidence
from tests.support.db_helpers import NOW, process_message, process_raw, to_raw
from tests.support.messages import (
    E1_TIME_MS,
    E1_UPDATED_1005,
    FAQ12_E1,
    build_message,
    build_real_looking_message,
    build_synthetic_message,
)
from tests.support.temp_database import TempDatabase

EVIDENCE_NAME = "bloque3_prueba6_cuarentena"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
UNION_SQL = (
    "SELECT 'live' AS schema, reason, kafka_topic, kafka_partition, kafka_offset, original_sha256 "
    "FROM live.quarantine UNION ALL "
    "SELECT 'replay', reason, kafka_topic, kafka_partition, kafka_offset, original_sha256 FROM replay.quarantine "
    "ORDER BY 1, 5"
)
REJECT_ID = "synthetic-reject-me"
DEFERRED_ID = "synthetic-reject-deferred"
# Niveles con los que json.loads lanza RecursionError en Python 3.12.16 (con 5000 aún no lo lanza).
NESTING_FOR_RECURSION_ERROR = 200_000
LONG_ID_OK = "synthetic-" + "x" * (512 - len("synthetic-"))


def _base() -> dict:
    return build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)


def _mutate(change) -> bytes:
    message = copy.deepcopy(_base())
    change(message)
    return to_raw(message)


def _replay_without_replay_at() -> bytes:
    return to_raw(build_message(_base()["event"], mode="replay", replay_at=None))


CASES = [
    ("invalid_json", b"{no json", TOPIC_LIVE),
    ("invalid_envelope", _mutate(lambda m: m.pop("source")), TOPIC_LIVE),
    ("mode_topic_mismatch", to_raw(build_message(_base()["event"], mode="replay", replay_at="2026-11-04T10:30:00Z")), TOPIC_LIVE),
    ("replay_at_missing", _replay_without_replay_at(), TOPIC_REPLAY),
    ("missing_id", _mutate(lambda m: m["event"].pop("id")), TOPIC_LIVE),
    ("missing_time", _mutate(lambda m: m["event"]["properties"].pop("time")), TOPIC_LIVE),
    ("missing_updated", _mutate(lambda m: m["event"]["properties"].pop("updated")), TOPIC_LIVE),
    ("invalid_geometry", _mutate(lambda m: m["event"]["geometry"].update(type="LineString")), TOPIC_LIVE),
    ("coordinates_out_of_range", _mutate(lambda m: m["event"]["geometry"]["coordinates"].__setitem__(1, 145)), TOPIC_LIVE),
    ("mag_out_of_range", _mutate(lambda m: m["event"]["properties"].update(mag=99)), TOPIC_LIVE),
    ("depth_out_of_range", _mutate(lambda m: m["event"]["geometry"]["coordinates"].__setitem__(2, 5000)), TOPIC_LIVE),
    ("invalid_field_type", _mutate(lambda m: m["event"]["properties"].update(place=42)), TOPIC_LIVE),
    ("value_out_of_range", _mutate(lambda m: m["event"]["properties"].update(sig=2**31)), TOPIC_LIVE),
    ("db_constraint_violation", _mutate(lambda m: m["event"]["properties"].update(dmin=float("nan"))), TOPIC_LIVE),
]


async def _with(db: TempDatabase, role: str, action):
    conn = await (db.consumer() if role == "consumer" else db.admin())
    try:
        return await action(conn)
    finally:
        await conn.close()


async def _admin_rows(db: TempDatabase, sql: str, *args) -> list[tuple]:
    return await _with(db, "admin", lambda c: _fetch(c, sql, *args))


async def _fetch(conn, sql: str, *args) -> list[tuple]:
    return [tuple(r.values()) for r in await conn.fetch(sql, *args)]


async def _write_cases(db: TempDatabase) -> list:
    async def action(conn):
        return [await process_raw(conn, raw, offset, topic) for offset, (_, raw, topic) in enumerate(CASES)]
    results = await _with(db, "consumer", action)
    await _with(db, "admin", lambda c: evidence.record_query(c, EVIDENCE_NAME, UNION_SQL, label="un caso por motivo"))
    return results


def test_one_case_per_contract_reason(db: TempDatabase) -> None:
    results = asyncio.run(_write_cases(db))
    for (reason, _, _), result in zip(CASES, results):
        assert result.kind is ResultKind.QUARANTINE and result.reason == reason and result.inserted is True
    rows = asyncio.run(_admin_rows(db, UNION_SQL))
    assert sorted(r[1] for r in rows) == sorted(reason for reason, _, _ in CASES)
    assert all(re.fullmatch(r"[0-9a-f]{64}", r[5]) for r in rows)
    assert asyncio.run(_admin_rows(db, "SELECT (SELECT count(*) FROM live.current_event) + "
                                       "(SELECT count(*) FROM live.event_version)")) == [(0,)]


async def _latitude_145(db: TempDatabase) -> None:
    raw = _mutate(lambda m: m["event"]["geometry"]["coordinates"].__setitem__(1, 145))
    await _with(db, "consumer", lambda c: process_raw(c, raw, 7))
    await _with(db, "admin", lambda c: evidence.record_query(
        c, EVIDENCE_NAME, "SELECT reason, event_id, kafka_topic, kafka_partition, kafka_offset, original_sha256 "
                          "FROM live.quarantine", label="latitud 145 (prueba 6)"))


def test_latitude_145_goes_to_quarantine_only(db: TempDatabase) -> None:
    asyncio.run(_latitude_145(db))
    rows = asyncio.run(_admin_rows(db, "SELECT reason, kafka_topic, kafka_partition, kafka_offset, "
                                       "length(original_sha256) FROM live.quarantine"))
    assert rows == [("coordinates_out_of_range", TOPIC_LIVE, 0, 7, 64)]
    events = asyncio.run(_admin_rows(db, "SELECT (SELECT count(*) FROM live.current_event WHERE event_id = $1) + "
                                         "(SELECT count(*) FROM live.event_version WHERE event_id = $1)", FAQ12_E1))
    assert events == [(0,)]


async def _write_twice(db: TempDatabase, first: bytes | None, second: bytes | None) -> list:
    async def action(conn):
        return [(await process_raw(conn, first, 1)).inserted, (await process_raw(conn, second, 2)).inserted]
    return await _with(db, "consumer", action)


def test_duplicate_hash_and_reason_inserts_once(db: TempDatabase) -> None:
    raw = _mutate(lambda m: m["event"]["properties"].update(mag=99))
    assert asyncio.run(_write_twice(db, raw, raw)) == [True, False]
    assert asyncio.run(_admin_rows(db, "SELECT count(*) FROM live.quarantine")) == [(1,)]


def test_tombstone_and_empty_share_one_invalid_json_row(db: TempDatabase) -> None:
    assert asyncio.run(_write_twice(db, None, b"")) == [True, False]
    rows = asyncio.run(_admin_rows(db, "SELECT reason, raw_text, original, original_sha256 FROM live.quarantine"))
    assert rows == [("invalid_json", "", None, EMPTY_SHA256)]


def _hostile_cases() -> list[tuple[str, bytes, str, str | None]]:
    """(nombre, bytes, motivo esperado, event_id esperado en la fila)."""
    nan_mag = _mutate(lambda m: m["event"]["properties"].update(mag=float("nan")))
    huge_mag = json.dumps(_base()).replace('"mag": 4.2', '"mag": 1e400').encode()
    deep = _mutate(lambda m: m["event"]["properties"].update(deep=_nested(100)))
    return [
        ("mag NaN", nan_mag, "mag_out_of_range", FAQ12_E1),
        ("mag 1e400", huge_mag, "mag_out_of_range", FAQ12_E1),
        ("place con NUL", _mutate(lambda m: m["event"]["properties"].update(place="a\u0000b")),
         "db_constraint_violation", FAQ12_E1),
        ("entero de 4301 dígitos", b'{"x": ' + b"1" * 4301 + b"}", "invalid_json", None),
        ("bytes no UTF-8", b"\xff\xfe{", "invalid_json", None),
        ("sustituto suelto", _mutate(lambda m: m["event"]["properties"].update(place="\ud800")),
         "db_constraint_violation", FAQ12_E1),
        ("anidamiento extremo (RecursionError)", b"[" * NESTING_FOR_RECURSION_ERROR + b"]" * NESTING_FOR_RECURSION_ERROR,
         "invalid_json", None),
        ("anidamiento de 100 niveles en event", deep, "db_constraint_violation", FAQ12_E1),
    ]


def _nested(levels: int) -> dict:
    node: dict = {}
    for _ in range(levels):
        node = {"n": node}
    return node


async def _write_hostile(db: TempDatabase) -> list:
    cases = _hostile_cases()

    async def action(conn):
        return [await process_raw(conn, raw, offset) for offset, (_, raw, _, _) in enumerate(cases)]
    return await _with(db, "consumer", action)


def test_hostile_content_is_sanitized_and_never_fails(db: TempDatabase) -> None:
    cases = _hostile_cases()
    results = asyncio.run(_write_hostile(db))
    rows = asyncio.run(_admin_rows(db, "SELECT kafka_offset, reason, event_id, original IS NULL, raw_text IS NOT NULL "
                                       "FROM live.quarantine ORDER BY kafka_offset"))
    for offset, ((name, _, reason, event_id), result) in enumerate(zip(cases, results)):
        assert result.reason == reason and result.inserted, name
        assert rows[offset] == (offset, reason, event_id, True, True), name


async def _write_long_ids(db: TempDatabase) -> list:
    async def action(conn):
        ok = await process_message(conn, build_synthetic_message(LONG_ID_OK, E1_TIME_MS, E1_UPDATED_1005, 4.2), 0)
        long_id = build_synthetic_message("y" * 600, E1_TIME_MS, E1_UPDATED_1005, 4.2)
        return [ok, await process_message(conn, long_id, 1)]
    return await _with(db, "consumer", action)


def test_event_id_of_512_chars_is_stored_and_600_is_quarantined(db: TempDatabase) -> None:
    ok, rejected = asyncio.run(_write_long_ids(db))
    assert ok.kind is ResultKind.EVENT and rejected.reason == "value_out_of_range"
    assert asyncio.run(_admin_rows(db, "SELECT length(event_id) FROM live.current_event")) == [(512,)]
    rows = asyncio.run(_admin_rows(db, "SELECT event_id, original IS NOT NULL FROM live.quarantine"))
    assert rows == [(None, True)]


async def _write_bad_real_and_synthetic(db: TempDatabase) -> None:
    real = to_raw(build_real_looking_message("test-real-looking-not-published", E1_TIME_MS, E1_UPDATED_1005, 99))
    synthetic = _mutate(lambda m: m["event"]["properties"].update(mag=99))

    async def action(conn):
        await process_raw(conn, real, 0)
        await process_raw(conn, synthetic, 1)
    await _with(db, "consumer", action)


def test_is_synthetic_is_copied_to_quarantine_including_false(db: TempDatabase) -> None:
    asyncio.run(_write_bad_real_and_synthetic(db))
    rows = asyncio.run(_admin_rows(db, "SELECT source, is_synthetic FROM live.quarantine ORDER BY kafka_offset"))
    assert rows == [("usgs_feed", False), ("replay_demo", True)]


def _prepared_rows(event_id: str):
    message = build_synthetic_message(event_id, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    valid = validate_message(decode_value(to_raw(message)), TOPIC_LIVE)
    return build_event_rows(valid, MessageRef(TOPIC_LIVE, 0, 3), NOW)


async def _forced_nul(db: TempDatabase) -> BaseException | None:
    rows = _prepared_rows(FAQ12_E1)
    rows.current["place"] = "a\u0000b"

    async def action(conn):
        try:
            await write_event(conn, rows, "live")
        except (asyncpg.PostgresError, ValueError, UnicodeError) as error:
            return error
        return None
    return await _with(db, "consumer", action)


def test_forced_nul_gives_content_error_class_22(db: TempDatabase) -> None:
    error = asyncio.run(_forced_nul(db))
    assert error is not None and is_content_error(error)
    evidence.record_text(EVIDENCE_NAME, f"NUL forzado en place -> {type(error).__name__} "
                                        f"sqlstate={getattr(error, 'sqlstate', None)}", "NUL forzado")
    assert asyncio.run(_admin_rows(db, "SELECT count(*) FROM live.event_version")) == [(0,)]


DEFERRED_FUNCTION = (
    "CREATE FUNCTION public.tmp_reject_deferred() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
    f"IF NEW.event_id = '{DEFERRED_ID}' THEN RAISE EXCEPTION 'rechazado en COMMIT' USING ERRCODE = '23514'; END IF; "
    "RETURN NULL; END $$"
)
DEFERRED_TRIGGER = (
    "CREATE CONSTRAINT TRIGGER tmp_reject_deferred AFTER INSERT ON live.current_event "
    "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.tmp_reject_deferred()"
)


async def _post_base_violation(db: TempDatabase, setup: list[str], teardown: list[str], event_id: str):
    admin = await db.admin()
    try:
        for statement in setup:
            await admin.execute(statement)
        try:
            async def action(conn):
                try:
                    await write_event(conn, _prepared_rows(event_id), "live")
                except asyncpg.PostgresError as error:
                    return error
                return None
            error = await _with(db, "consumer", action)
        finally:
            for statement in teardown:
                await admin.execute(statement)
        counts = await _fetch(admin, "SELECT (SELECT count(*) FROM live.current_event), "
                                     "(SELECT count(*) FROM live.event_version)")
        return error, counts
    finally:
        await admin.close()


def test_immediate_check_violation_rolls_back_everything(db: TempDatabase) -> None:
    setup = [f"ALTER TABLE live.current_event ADD CONSTRAINT tmp_reject_id CHECK (event_id <> '{REJECT_ID}')"]
    teardown = ["ALTER TABLE live.current_event DROP CONSTRAINT IF EXISTS tmp_reject_id"]
    error, counts = asyncio.run(_post_base_violation(db, setup, teardown, REJECT_ID))
    assert isinstance(error, asyncpg.CheckViolationError) and is_content_error(error)
    assert counts == [(0, 0)]
    row = build_quarantine_row(decode_value(b"{}"), "db_constraint_violation", MessageRef(TOPIC_LIVE, 0, 3), NOW)
    inserted = asyncio.run(_with(db, "consumer", lambda c: write_quarantine(c, row, "live")))
    assert inserted is True


def test_deferred_trigger_violation_at_commit_rolls_back_everything(db: TempDatabase) -> None:
    setup = [DEFERRED_FUNCTION, DEFERRED_TRIGGER]
    teardown = ["DROP TRIGGER IF EXISTS tmp_reject_deferred ON live.current_event",
                "DROP FUNCTION IF EXISTS public.tmp_reject_deferred()"]
    error, counts = asyncio.run(_post_base_violation(db, setup, teardown, DEFERRED_ID))
    assert isinstance(error, asyncpg.CheckViolationError) and is_content_error(error)
    assert counts == [(0, 0)]
