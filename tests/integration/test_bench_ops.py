"""Carga, índices y operaciones a y c de las mediciones contra PostgreSQL real (T079, T080, T082).

Corre sobre la base temporal de la sesión (fixture `db`), que tiene el esquema real; todo lo
que se carga en `bench` es SINTÉTICO y `bench` se elimina al terminar cada prueba.
"""
import asyncio
import json
from pathlib import Path

import pytest

from common.geo import assign_country, build_country_index, parse_country_catalog
from scripts.benchmarks.bench_load import (analyze, create_index, drop_index, explain, load_table,
                                           read_index_definitions, rewrite_index)
from scripts.benchmarks.bench_schema import bench_session
from scripts.benchmarks.op_agg import run_agg
from scripts.benchmarks.op_search import CASES, run_search
from scripts.benchmarks.plans import summarize_plan
from scripts.benchmarks.seed import load_seed
from scripts.benchmarks.synth import build_rows
from tests.support.temp_database import TempDatabase

ROOT = Path(__file__).resolve().parents[2]
SIZE = 1000
FAST = {"n_max": 3, "budget": 5}


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    catalog = parse_country_catalog(json.loads((ROOT / "data" / "catalogo" / "paises.geojson").read_text("utf-8")))
    index = build_country_index(catalog)
    seed = load_seed(ROOT / "data" / "historical").events
    return build_rows(seed, SIZE, lambda lon, lat: assign_country(index, lon, lat).country_id)


def run_with_bench(db: TempDatabase, rows: list[dict], body):
    """Crea `bench`, carga `event_1000`, ejecuta `body(admin, defs)` y elimina `bench` siempre."""
    async def main():
        api, admin = await db.api_pool(), await db.admin()
        try:
            async with api.acquire() as api_conn:
                defs = await read_index_definitions(api_conn)
            async with bench_session(admin, [SIZE]):
                assert await load_table(admin, SIZE, rows) == SIZE
                await analyze(admin, f"event_{SIZE}")
                return await body(admin, defs)
        finally:
            await api.close()
            await admin.close()
    result = asyncio.run(main())
    return result


def test_load_four_real_indexes_one_at_a_time_and_saved_plan(db: TempDatabase, rows: list[dict], tmp_path: Path) -> None:
    async def body(conn, defs):
        count = await conn.fetchval(f"SELECT count(*) FROM bench.event_{SIZE}")
        sizes = []
        for definition in defs:
            index = rewrite_index(definition.defn, f"event_{SIZE}", "t")
            await create_index(conn, index)
            sizes.append(await conn.fetchval("SELECT count(*) FROM pg_indexes WHERE schemaname = 'bench'"))
            await drop_index(conn, index.name)
        left = await conn.fetchval("SELECT count(*) FROM pg_indexes WHERE schemaname = 'bench'")
        path = tmp_path / "planes" / "plan.json"
        plan = await explain(conn, f"SELECT count(*) FROM bench.event_{SIZE} WHERE mag >= $1", (4,), path)
        return count, [d.name for d in defs], sizes, left, plan, path
    count, names, sizes, left, plan, path = run_with_bench(db, rows, body)
    assert count == SIZE and len(names) == 4 and sizes == [1, 1, 1, 1] and left == 0
    assert json.loads(path.read_text("utf-8")) == plan and summarize_plan(plan).execution_ms is not None


def test_search_gives_sixteen_plus_build_with_plan_nodes(db: TempDatabase, rows: list[dict], tmp_path: Path) -> None:
    async def body(conn, defs):
        return await run_search(conn, SIZE, rows, defs, tmp_path / "planes", **FAST)
    result = run_with_bench(db, rows, body)
    by_case = [m for m in result if m.case in CASES]
    assert len(by_case) == 16 and {m.strategy for m in by_case} == {"list", "dict", "pg_seq", "pg_index"}
    seq = [m for m in by_case if m.strategy == "pg_seq"]
    indexed = [m for m in by_case if m.strategy == "pg_index"]
    assert all("Seq Scan" in m.nodes and m.index_used is False for m in seq)
    assert all(m.index_used is True and "Index" in " ".join(m.nodes) for m in indexed)
    assert all((tmp_path / m.plan_ref).is_file() and m.server_ms is not None for m in seq + indexed)
    assert all(m.notes == "" for m in seq + indexed) or all("teoría" in m.notes for m in seq + indexed if m.notes)


def test_aggregation_measures_q2_q3_q4_without_and_with_index(db: TempDatabase, rows: list[dict],
                                                              tmp_path: Path) -> None:
    async def body(conn, defs):
        result = await run_agg(conn, SIZE, rows, defs, tmp_path / "planes", **FAST)
        left = await conn.fetchval("SELECT count(*) FROM pg_indexes WHERE schemaname = 'bench'")
        return result, left
    (measurements, verdicts), left = run_with_bench(db, rows, body)
    assert left == 0 and len(measurements) == 12 and len(verdicts) == 6
    for query in ("q2", "q3", "q4"):
        mine = [m for m in measurements if m.strategy.startswith(query)]
        assert {m.strategy.endswith("noindex") for m in mine} == {True, False}
    assert all((tmp_path / m.plan_ref).is_file() and m.server_ms is not None and m.median_ms > 0
               for m in measurements)
    assert all(len(v.measurement_ids) == 2 and v.verdict for v in verdicts)
