"""Ciclo de vida del esquema `bench` contra PostgreSQL real (T078, K4, FR-012, FR-016, FR-017).

Corre sobre la base temporal de la sesión de pruebas (fixture `db`), no sobre la del stack.
"""
import asyncio
import os
import signal

import pytest

from scripts.benchmarks.bench_schema import (BenchSchemaError, SCHEMA_COMMENT, bench_session, bench_state,
                                             clean_if_marked, connect_admin, create_bench, drop_bench,
                                             take_snapshot, verify_isolation)
from tests.support.temp_database import TempDatabase

SIZES = [1000, 10000]


def run(db: TempDatabase, coro_factory):
    """Ejecuta una corrutina con la conexión del administrador de la base temporal."""
    async def main():
        conn = await db.admin()
        try:
            return await coro_factory(conn)
        finally:
            await conn.close()
    return asyncio.run(main())


def exists(db: TempDatabase) -> bool:
    return run(db, lambda conn: conn.fetchval("SELECT to_regnamespace('bench') IS NOT NULL"))


def test_create_and_drop_bench(db: TempDatabase) -> None:
    async def body(conn):
        await create_bench(conn, SIZES)
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'bench'")
        comment = (await bench_state(conn))[1]
        await drop_bench(conn)
        return sorted(r["table_name"] for r in tables), comment
    tables, comment = run(db, body)
    assert tables == ["event_1000", "event_10000"]
    assert comment == SCHEMA_COMMENT
    assert not exists(db)


def test_table_structure_comes_from_live_without_constraints(db: TempDatabase) -> None:
    async def body(conn):
        await create_bench(conn, [1000])
        try:
            cols = await conn.fetch("SELECT column_name FROM information_schema.columns "
                                    "WHERE table_schema = 'bench' ORDER BY ordinal_position")
            live = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE "
                                    "table_schema = 'live' AND table_name = 'current_event' ORDER BY ordinal_position")
            checks = await conn.fetchval("SELECT count(*) FROM pg_constraint WHERE connamespace = 'bench'::regnamespace")
            return cols == live, checks
        finally:
            await drop_bench(conn)
    same, checks = run(db, body)
    assert same and checks == 0


def test_foreign_bench_aborts_untouched_and_clean_refuses(db: TempDatabase) -> None:
    async def body(conn):
        await conn.execute("CREATE SCHEMA bench")
        await conn.execute("CREATE TABLE bench.ajena (x int)")
        errors = []
        for clean in (False, True):
            try:
                await create_bench(conn, SIZES, clean=clean)
            except BenchSchemaError as error:
                errors.append(str(error))
        survives = await conn.fetchval("SELECT to_regclass('bench.ajena') IS NOT NULL")
        await conn.execute("DROP SCHEMA bench CASCADE")
        return errors, survives
    errors, survives = run(db, body)
    assert len(errors) == 2 and "marca" in errors[1]
    assert survives is True


def test_marked_bench_needs_clean_and_clean_removes_only_it(db: TempDatabase) -> None:
    async def body(conn):
        await create_bench(conn, [1000])
        try:
            await create_bench(conn, SIZES)
            refused = False
        except BenchSchemaError:
            refused = True
        await create_bench(conn, SIZES, clean=True)
        tables = await conn.fetchval("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'bench'")
        removed = await clean_if_marked(conn)
        again = await clean_if_marked(conn)
        return refused, tables, removed, again
    assert run(db, body) == (True, 2, True, False)
    assert not exists(db)


def test_exception_midway_leaves_no_bench(db: TempDatabase) -> None:
    async def body(conn):
        with pytest.raises(RuntimeError, match="a mitad"):
            async with bench_session(conn, SIZES):
                assert (await bench_state(conn))[0]
                raise RuntimeError("fallo a mitad")
    run(db, body)
    assert not exists(db)


def test_sigterm_cancels_and_drops_bench(db: TempDatabase) -> None:
    async def body(conn):
        async with bench_session(conn, SIZES):
            os.kill(os.getpid(), signal.SIGTERM)
            await asyncio.sleep(5)
    with pytest.raises(asyncio.CancelledError):
        run(db, body)
    assert not exists(db)


def test_isolation_counts_unchanged_and_violations_detected(db: TempDatabase) -> None:
    async def body(conn):
        before = await take_snapshot(conn)
        async with bench_session(conn, SIZES):
            during = await take_snapshot(conn)
        after = await take_snapshot(conn)
        return before, during, after
    before, during, after = run(db, body)
    assert verify_isolation(before, after) == []
    assert during["bench_exists"] is True
    assert any("sigue existiendo" in p for p in verify_isolation(before, during))
    tampered = {**after, "usgs_historical": 5, "bench_rows_outside": {"live.current_event": 2}}
    assert len(verify_isolation(before, tampered)) == 2


def test_missing_variables_fail_before_connecting() -> None:
    with pytest.raises(BenchSchemaError, match="DB_HOST"):
        asyncio.run(connect_admin({}))
    with pytest.raises(BenchSchemaError, match="no se pudo conectar"):
        asyncio.run(connect_admin({"DB_HOST": "no-existe.invalid", "DB_PORT": "5432", "DB_NAME": "x",
                                   "POSTGRES_USER": "x", "POSTGRES_PASSWORD": "x"}))
