"""Operación a: búsqueda de un evento por id con lista, `dict` y PostgreSQL sin y con índice (K1, K2, K3).

Ids medidos: primero, medio, último y ausente. Todos los datos son SINTÉTICOS. La construcción
del `dict` se mide aparte; las consultas a `bench` solo leen (el único índice lo crea y borra
`bench_load`).
"""
from pathlib import Path

import asyncpg

from scripts.benchmarks.bench_load import (IndexDef, analyze, create_index, drop_index, explain, find_index,
                                           rewrite_index)
from scripts.benchmarks.measure import measure_peak_kib, measure_time
from scripts.benchmarks.measure_async import measure_time_async
from scripts.benchmarks.plans import summarize_plan, theory_note
from scripts.benchmarks.records import Measurement, build_measurement
from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX

OPERATION = "search"
CASES = ("first", "middle", "last", "absent")
ABSENT_ID = "synthetic-bench-absent"
THEORY = {"list": "O(n) medio y peor", "dict": "O(1) medio, O(n) peor teórico",
          "pg_seq": "O(n) (Seq Scan)", "pg_index": "O(log n) (B-tree)"}
SEARCH_SQL = "SELECT * FROM bench.event_{size} WHERE event_id = $1"
EVENT_ID_COLUMNS = ("event_id",)


def pick_ids(rows: list[dict]) -> dict[str, str]:
    """Ids de los cuatro casos: primero, medio, último y uno ausente."""
    return {"first": rows[0]["event_id"], "middle": rows[len(rows) // 2]["event_id"],
            "last": rows[-1]["event_id"], "absent": ABSENT_ID}


def find_in_list(rows: list[dict], event_id: str) -> dict | None:
    """Búsqueda secuencial por id: O(n). Devuelve el evento o `None` si está ausente."""
    for row in rows:
        if row["event_id"] == event_id:
            return row
    return None


def build_dict(rows: list[dict]) -> dict[str, dict]:
    """Construye el `dict` id -> evento (coste de construcción medido aparte)."""
    return {row["event_id"]: row for row in rows}


def measure_memory_strategies(rows: list[dict], size: int, n_max: int, budget: float) -> list[Measurement]:
    """Mide en memoria Python las búsquedas con lista y `dict` (4 ids cada una) y la construcción del `dict`."""
    ids, lookup, out = pick_ids(rows), build_dict(rows), []
    for strategy, fn in (("list", lambda i: find_in_list(rows, i)), ("dict", lambda i: lookup.get(i))):
        for case in CASES:
            call = (lambda f=fn, i=ids[case]: f(i))
            out.append(build_measurement(OPERATION, strategy, size, case, measure_time(call, n_max, budget),
                                         theory=THEORY[strategy]))
    result = measure_time(lambda: build_dict(rows), n_max, budget)
    out.append(build_measurement(OPERATION, "dict_build", size, "build", result,
                                 peak_kib=measure_peak_kib(lambda: build_dict(rows)), theory="O(n)"))
    return out


async def _measure_postgres(conn: asyncpg.Connection, strategy: str, size: int, ids: dict[str, str],
                            plans_dir: Path, n_max: int, budget: float) -> list[Measurement]:
    """Mide la búsqueda en `bench.event_<size>` para los 4 ids y guarda un plan por caso."""
    sql = SEARCH_SQL.format(size=size)
    out = []
    for case in CASES:
        async def query(i=ids[case]):
            return await conn.fetchrow(sql, i)
        result = await measure_time_async(query, n_max, budget)
        ref = plans_dir / f"{OPERATION}.{strategy}.{size}.{case}.json"
        info = summarize_plan(await explain(conn, sql, (ids[case],), ref))
        note = theory_note(info, expected_index=(strategy == "pg_index"))
        out.append(build_measurement(OPERATION, strategy, size, case, result, plan_ref=f"planes/{ref.name}",
                                     plan=info, notes=note, theory=THEORY[strategy]))
    return out


async def measure_postgres_strategies(conn: asyncpg.Connection, size: int, rows: list[dict],
                                      index_defs: list[IndexDef], plans_dir: Path,
                                      n_max: int = N_MAX, budget: float = BUDGET_SECONDS) -> list[Measurement]:
    """Mide PostgreSQL sin índice y con el índice de `event_id` (el real, leído de `pg_indexes`).

    Deja la tabla otra vez sin índice y con estadísticas al día.
    """
    ids, table = pick_ids(rows), f"event_{size}"
    out = await _measure_postgres(conn, "pg_seq", size, ids, plans_dir, n_max, budget)
    index = rewrite_index(find_index(index_defs, EVENT_ID_COLUMNS).defn, table, f"b{size}")
    await create_index(conn, index)
    try:
        await analyze(conn, table)
        out += await _measure_postgres(conn, "pg_index", size, ids, plans_dir, n_max, budget)
    finally:
        await drop_index(conn, index.name)
        await analyze(conn, table)
    return out


async def run_search(conn: asyncpg.Connection, size: int, rows: list[dict], index_defs: list[IndexDef],
                     plans_dir: Path, n_max: int = N_MAX, budget: float = BUDGET_SECONDS) -> list[Measurement]:
    """Operación a completa: 4 estrategias x 4 ids (16 mediciones) más la construcción del `dict`."""
    return (measure_memory_strategies(rows, size, n_max, budget)
            + await measure_postgres_strategies(conn, size, rows, index_defs, plans_dir, n_max, budget))
