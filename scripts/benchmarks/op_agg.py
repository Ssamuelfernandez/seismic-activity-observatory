"""Operación c y E6: Q4, Q3 y Q2 sobre `bench` sin y con un índice, un índice cada vez (K1, K2, D8).

Datos SINTÉTICOS. Los índices salen de `pg_indexes` (se localizan por sus columnas, no por
nombre) y se crean y borran en `bench`. Cada consulta guarda su plan `EXPLAIN ANALYZE`.
"""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import asyncpg

from scripts.benchmarks.bench_load import (IndexDef, analyze, create_index, drop_index, explain, find_index,
                                           rewrite_index)
from scripts.benchmarks.measure_async import measure_time_async
from scripts.benchmarks.plans import summarize_plan
from scripts.benchmarks.records import Measurement, build_measurement
from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX
from scripts.benchmarks.verdicts import Verdict, judge

OPERATION = "agg"
UTC = timezone.utc
YEAR = (datetime(2025, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC))
P99 = 0.99
Q4_SQL = ("SELECT date_trunc('hour', event_time AT TIME ZONE 'UTC') AS hour, count(*) "
          "FROM bench.event_{size} {where} GROUP BY 1 ORDER BY 1")
Q3_SQL = "SELECT count(*) FROM bench.event_{size} WHERE mag >= $1"
Q2_SQL = ("SELECT country_id, count(*) FROM bench.event_{size} "
          "WHERE country_id = $1 AND event_time >= $2 AND event_time < $3 GROUP BY country_id")
Q4_WINDOW = "WHERE event_time >= $1 AND event_time < $2"


@dataclass(frozen=True)
class Query:
    """Una consulta medida: sentencia, índice que la sirve (columnas) y sus casos con parámetros."""

    name: str
    index_label: str
    index_columns: tuple[str, ...]
    sql: str
    cases: dict[str, tuple]
    selectivity: dict[str, float | None]


def busiest_day(rows: list[dict]) -> tuple[datetime, datetime]:
    """Ventana de un día UTC (inicio, fin) con más eventos: Q4 sobre «un día»."""
    day = Counter(r["event_time"].date() for r in rows).most_common(1)[0][0]
    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


def top_country(rows: list[dict]) -> str:
    """País con más eventos del tamaño (sin contar los nulos)."""
    return Counter(r["country_id"] for r in rows if r["country_id"]).most_common(1)[0][0]


def busiest_month(rows: list[dict], country: str) -> tuple[datetime, datetime]:
    """Mes UTC (inicio, fin) con más eventos del país: Q2 sobre «un mes»."""
    month = Counter(r["event_time"].month for r in rows if r["country_id"] == country).most_common(1)[0][0]
    start = datetime(2025, month, 1, tzinfo=UTC)
    end = datetime(2025 + month // 12, month % 12 + 1, 1, tzinfo=UTC)
    return start, end


def percentile_mag(rows: list[dict], fraction: float = P99) -> float:
    """Umbral de magnitud que deja fuera el 1 % superior de las filas con magnitud (p99)."""
    mags = sorted(float(r["mag"]) for r in rows if r["mag"] is not None)
    return mags[min(len(mags) - 1, int(fraction * len(mags)))]


def _fraction(rows: list[dict], predicate) -> float:
    """Fracción de filas que cumplen el predicado (selectividad del filtro)."""
    return sum(1 for r in rows if predicate(r)) / len(rows)


def build_queries(rows: list[dict], size: int) -> list[Query]:
    """Q4, Q3 y Q2 con sus casos: Q4 día y tabla completa; Q3 `mag >= 4` y p99; Q2 mes y todo el rango."""
    day, country, p99 = busiest_day(rows), top_country(rows), percentile_mag(rows)
    month = busiest_month(rows, country)
    in_day = lambda r: day[0] <= r["event_time"] < day[1]
    in_month = lambda r: r["country_id"] == country and month[0] <= r["event_time"] < month[1]
    return [
        Query("q4", "time", ("event_time", "event_id"), Q4_SQL.format(size=size, where="{where}"),
              {"day": day, "all": ()}, {"day": _fraction(rows, in_day), "all": 1.0}),
        Query("q3", "mag", ("mag",), Q3_SQL.format(size=size), {"mag4": (Decimal("4"),), "p99": (Decimal(str(p99)),)},
              {"mag4": _fraction(rows, lambda r: r["mag"] is not None and r["mag"] >= 4),
               "p99": _fraction(rows, lambda r: r["mag"] is not None and r["mag"] >= p99)}),
        Query("q2", "country", ("country_id", "event_time"), Q2_SQL.format(size=size),
              {"month": (country, *month), "range": (country, *YEAR)},
              {"month": _fraction(rows, in_month), "range": _fraction(rows, lambda r: r["country_id"] == country)}),
    ]


def _statement(query: Query, case: str) -> str:
    """Sentencia concreta del caso (Q4 solo lleva `WHERE` en la ventana de un día)."""
    if query.name != "q4":
        return query.sql
    return query.sql.format(where=Q4_WINDOW if case == "day" else "")


async def _measure_cases(conn: asyncpg.Connection, query: Query, strategy: str, size: int, plans_dir: Path,
                         n_max: int, budget: float) -> list[Measurement]:
    """Mide los casos de una consulta con la configuración actual de índices y guarda cada plan."""
    out = []
    for case, params in query.cases.items():
        sql, params = _statement(query, case), tuple(params)
        async def run():
            return await conn.fetch(sql, *params)
        result = await measure_time_async(run, n_max, budget)
        ref = plans_dir / f"{OPERATION}.{strategy}.{size}.{case}.json"
        info = summarize_plan(await explain(conn, sql, params, ref))
        selectivity = query.selectivity[case]
        out.append(build_measurement(OPERATION, strategy, size, case, result, plan_ref=f"planes/{ref.name}",
                                     plan=info, notes=f"selectividad {selectivity:.4f}",
                                     theory="O(n) (Seq Scan, más ordenación o HashAggregate)"))
    return out


async def run_agg(conn: asyncpg.Connection, size: int, rows: list[dict], index_defs: list[IndexDef],
                  plans_dir: Path, n_max: int = N_MAX, budget: float = BUDGET_SECONDS
                  ) -> tuple[list[Measurement], list[Verdict]]:
    """Q4, Q3 y Q2 sin índice y con su índice (uno cada vez); devuelve mediciones y veredictos.

    Recibe:
        conn: administrador; size, rows: tabla `bench.event_<size>` ya cargada y analizada;
        index_defs: definiciones de `pg_indexes`; plans_dir: carpeta `planes/`.
    Devuelve:
        Mediciones (cada una con su plan, `Execution Time` del servidor y tiempo de cliente) y un
        veredicto por índice y caso. Deja la tabla sin índices y con estadísticas al día.
    Por qué existe:
        Justifica con medidas cada índice de la tabla real (E6, FR-004, FR-005).
    """
    table, queries, out, verdicts = f"event_{size}", build_queries(rows, size), [], []
    baseline = {q.name: await _measure_cases(conn, q, f"{q.name}_noindex", size, plans_dir, n_max, budget)
                for q in queries}
    for query in queries:
        definition = find_index(index_defs, query.index_columns)
        index = rewrite_index(definition.defn, table, f"b{size}")
        await create_index(conn, index)
        try:
            await analyze(conn, table)
            indexed = await _measure_cases(conn, query, f"{query.name}_{query.index_label}_index", size,
                                           plans_dir, n_max, budget)
        finally:
            await drop_index(conn, index.name)
            await analyze(conn, table)
        out += baseline[query.name] + indexed
        verdicts += [judge(definition.name, query.name, a, b, query.selectivity[a.case])
                     for a, b in zip(baseline[query.name], indexed, strict=True)]
    return out, verdicts
