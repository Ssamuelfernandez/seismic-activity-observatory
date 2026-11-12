"""Carga de filas sintéticas en `bench`, índices leídos del esquema real y planes `EXPLAIN` (E6, K3).

Solo escribe en `bench.` (carga con `COPY`, `ANALYZE`, índices). Las definiciones de índice se
leen de `pg_indexes` de `live.current_event` con el rol de solo lectura y se reescriben para
`bench`: no se teclea ni se copia ningún nombre de índice (constitución §15).
"""
import json
import re
from pathlib import Path
from typing import NamedTuple

import asyncpg

from scripts.benchmarks.synth import COLUMNS, row_values

TABLE_PATTERN = re.compile(r"^event_\d+$")
IDENTIFIER_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
INDEX_DEFINITION = re.compile(r"^(CREATE (?:UNIQUE )?INDEX )(\S+)( ON )live\.current_event( USING \w+ \()(.*)(\).*)$")
READ_INDEXES_SQL = ("SELECT indexname, indexdef FROM pg_indexes "
                    "WHERE schemaname = 'live' AND tablename = 'current_event' ORDER BY indexname")
EXPLAIN_PREFIX = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "


class IndexDef(NamedTuple):
    """Definición leída de `pg_indexes`: nombre real, sentencia original y columnas (sin orden)."""

    name: str
    defn: str
    columns: tuple[str, ...]


class BenchIndex(NamedTuple):
    """Índice reescrito para `bench`: nombre nuevo y sentencia de creación."""

    name: str
    create_sql: str


def _bench_table(table: str) -> str:
    """Valida el nombre de tabla de `bench` (`event_<N>`) antes de usarlo en una sentencia."""
    if not TABLE_PATTERN.match(table):
        raise ValueError(f"nombre de tabla no válido para bench: {table!r}")
    return table


def index_columns(defn: str) -> tuple[str, ...]:
    """Columnas de una definición de índice, sin `DESC`/`ASC`: `(event_time DESC, event_id DESC)` da dos."""
    match = INDEX_DEFINITION.match(defn)
    if match is None:
        raise ValueError(f"definición de índice no reconocida: {defn!r}")
    return tuple(part.split()[0] for part in match.group(5).split(","))


async def read_index_definitions(api_conn: asyncpg.Connection) -> list[IndexDef]:
    """Lee de `pg_indexes` los índices de `live.current_event` con el rol de solo lectura.

    Recibe:
        api_conn: conexión de `observatory_api` (el rol que ya consulta la tabla real).
    Devuelve:
        Lista de `IndexDef`, ordenada por nombre.
    Por qué existe:
        Los índices a medir salen del esquema real, no de nombres tecleados (E6, D5).
    """
    async with api_conn.transaction(readonly=True):
        rows = await api_conn.fetch(READ_INDEXES_SQL)
    return [IndexDef(r["indexname"], r["indexdef"], index_columns(r["indexdef"])) for r in rows]


def find_index(definitions: list[IndexDef], columns: tuple[str, ...]) -> IndexDef:
    """Localiza la definición cuyo conjunto de columnas coincide exactamente (en orden)."""
    for definition in definitions:
        if definition.columns == columns:
            return definition
    raise LookupError(f"no hay un índice de live.current_event con columnas {columns}")


def rewrite_index(defn: str, table: str, suffix: str) -> BenchIndex:
    """Reescribe la definición de un índice real para una tabla de `bench`.

    Qué hace:
        Sustituye el esquema y la tabla (`live.current_event` por `bench.<table>`) y añade
        `_<suffix>` al nombre del índice; el resto (columnas, orden, tipo) queda como se leyó.
    Recibe:
        defn: `indexdef` de `pg_indexes`; table: `event_<N>`; suffix: sufijo en minúsculas.
    Devuelve:
        `BenchIndex` sin ninguna referencia a `live.`.
    Por qué existe:
        Crea en `bench` exactamente los mismos índices que la tabla real (E6, FR-005).
    """
    match = INDEX_DEFINITION.match(defn)
    if match is None:
        raise ValueError(f"definición de índice no reconocida: {defn!r}")
    name = f"{match.group(2)}_{suffix}"
    if not IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"nombre de índice no válido: {name!r}")
    head, on, using, columns, tail = match.group(1), match.group(3), match.group(4), match.group(5), match.group(6)
    return BenchIndex(name, f"{head}{name}{on}bench.{_bench_table(table)}{using}{columns}{tail}")


async def load_table(conn: asyncpg.Connection, size: int, rows: list[dict]) -> int:
    """Carga las filas sintéticas en `bench.event_<size>` con `COPY` y devuelve cuántas entraron."""
    table = _bench_table(f"event_{int(size)}")
    await conn.copy_records_to_table(table, records=[row_values(row) for row in rows],
                                     columns=list(COLUMNS), schema_name="bench")
    return len(rows)


async def analyze(conn: asyncpg.Connection, table: str) -> None:
    """Actualiza las estadísticas de una tabla de `bench` (tras cargar y tras cada cambio de índice)."""
    await conn.execute(f"ANALYZE bench.{_bench_table(table)}")


async def create_index(conn: asyncpg.Connection, index: BenchIndex) -> None:
    """Crea un índice ya reescrito para `bench`."""
    await conn.execute(index.create_sql)


async def drop_index(conn: asyncpg.Connection, name: str) -> None:
    """Elimina un índice de `bench` por su nombre reescrito."""
    if not IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"nombre de índice no válido: {name!r}")
    await conn.execute(f"DROP INDEX bench.{name}")


async def explain(conn: asyncpg.Connection, sql: str, params: tuple = (), plan_path: Path | None = None) -> list[dict]:
    """Ejecuta `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` de una consulta y guarda el plan.

    Recibe:
        conn: conexión; sql: la consulta (solo lectura) con `$1`...; params: sus valores;
        plan_path: archivo `planes/<id>.json` donde guardar el JSON (opcional).
    Devuelve:
        El plan ya parseado (lista de un elemento).
    Por qué existe:
        Cada consulta de PostgreSQL deja su plan como evidencia (E6, SC-001).
    """
    text = await conn.fetchval(EXPLAIN_PREFIX + sql, *params)
    plan = json.loads(text) if isinstance(text, str) else text
    if plan_path is not None:
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return plan
