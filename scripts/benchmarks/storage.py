"""Referencia REAL de índices, recuentos y almacenamiento de la base, solo lectura (E6, K6, FR-005, FR-016, FR-019).

Lo que lee es dato real del stack, no sintético: se usa el rol `observatory_api` dentro de una
transacción de solo lectura. Si el rol no tiene permiso sobre una tabla, se informa como
«no disponible» en vez de escalar privilegios.
"""
from dataclasses import dataclass
from pathlib import Path

import asyncpg

from scripts.benchmarks.bench_load import IndexDef, create_index, drop_index, rewrite_index
from scripts.benchmarks.labels import SYNTHETIC_LABEL, UNAVAILABLE

BYTES_PER_KIB = 1024
INDEX_REFERENCE_SQL = (
    "SELECT s.indexrelname AS name, i.indexdef AS definition, pg_relation_size(s.indexrelid) AS size_bytes, "
    "s.idx_scan FROM pg_stat_user_indexes s JOIN pg_indexes i "
    "ON i.schemaname = s.schemaname AND i.indexname = s.indexrelname "
    "WHERE s.schemaname = 'live' AND s.relname = 'current_event' ORDER BY s.indexrelname")
COUNT_TABLES = ("replay.current_event", "replay.event_version", "replay.quarantine", "replay.exclusion")
HISTORICAL_SQL = "SELECT count(*) FROM live.current_event WHERE source = 'usgs_historical'"


@dataclass(frozen=True)
class IndexReference:
    """Un índice real de `live.current_event`: definición, tamaño y escaneos acumulados."""

    name: str
    definition: str
    size_bytes: int
    idx_scan: int


@dataclass(frozen=True)
class RealReference:
    """Lectura real: índices, recuentos (`None` = sin permiso) y si la transacción era de solo lectura."""

    indexes: list[IndexReference]
    counts: dict[str, int | None]
    usgs_historical: int
    read_only: bool


async def _count(conn: asyncpg.Connection, table: str) -> int | None:
    """Recuento de una tabla con punto de guardado; `None` si el rol no puede leerla."""
    try:
        async with conn.transaction():
            return await conn.fetchval(f"SELECT count(*) FROM {table}")
    except asyncpg.InsufficientPrivilegeError:
        return None


async def read_real_reference(api_conn: asyncpg.Connection) -> RealReference:
    """Lee índices, tamaños, `idx_scan` y recuentos reales con el rol `observatory_api`.

    Recibe:
        api_conn: conexión del rol de solo lectura de la API.
    Devuelve:
        `RealReference`; todo se lee dentro de una transacción de solo lectura (`read_only` lo confirma).
    Por qué existe:
        Acompaña la medición sintética con el estado real de los índices (tamaño y uso) y
        demuestra que las lecturas reales no escriben (E6, FR-016).
    """
    async with api_conn.transaction(readonly=True):
        read_only = (await api_conn.fetchval("SHOW transaction_read_only")) == "on"
        rows = await api_conn.fetch(INDEX_REFERENCE_SQL)
        counts = {table: await _count(api_conn, table) for table in COUNT_TABLES}
        historical = await api_conn.fetchval(HISTORICAL_SQL)
    indexes = [IndexReference(r["name"], r["definition"], r["size_bytes"], r["idx_scan"]) for r in rows]
    return RealReference(indexes, counts, historical, read_only)


def render_real_reference(reference: RealReference) -> str:
    """Sección de `indices.md` con la referencia REAL (lectura de solo lectura), en Markdown."""
    lines = ["## Referencia REAL de `live.current_event` (solo lectura, rol `observatory_api`)", "",
             "| Índice | Definición | Tamaño (KiB) | idx_scan |", "|---|---|---|---|"]
    for index in reference.indexes:
        lines.append(f"| {index.name} | `{index.definition}` | {index.size_bytes / BYTES_PER_KIB:.1f} | {index.idx_scan} |")
    lines += ["", "| Recuento real | Filas |", "|---|---|",
              f"| live.current_event con source = usgs_historical | {reference.usgs_historical} |"]
    lines += [f"| {table} | {UNAVAILABLE if count is None else count} |" for table, count in reference.counts.items()]
    return "\n".join(lines) + "\n"

# --- Almacenamiento medido (T084, K6, FR-019): tablas reales con índices, archivos y `bench` (SINTÉTICO) ---
REAL_SCHEMAS = ("live", "replay", "ingest", "quarantine", "public")
TABLES_SQL = (
    "SELECT n.nspname AS schema, c.relname AS name, "
    "quote_ident(n.nspname) || '.' || quote_ident(c.relname) AS qualified, "
    "pg_total_relation_size(c.oid) AS total_bytes, pg_indexes_size(c.oid) AS index_bytes "
    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE c.relkind = 'r' AND n.nspname = ANY($1::text[]) ORDER BY n.nspname, c.relname")
DATABASE_SIZE_SQL = "SELECT pg_database_size(current_database())"
BENCH_SIZE_SQL = "SELECT pg_total_relation_size('bench.event_{size}'::regclass)"
BENCH_HEAP_SQL = "SELECT pg_relation_size('bench.event_{size}'::regclass)"
BENCH_INDEX_SQL = "SELECT pg_relation_size('bench.{name}'::regclass)"
DOCKER_VOLUME_NOTE = f"{UNAVAILABLE} (el volumen de Docker no se lee desde el contenedor `tests`)"


@dataclass(frozen=True)
class TableStorage:
    """Tamaño total, de índices y filas reales de una tabla; `bytes_per_row` ya derivado."""

    schema: str
    name: str
    rows: int
    total_bytes: int
    index_bytes: int
    bytes_per_row: float | None


@dataclass(frozen=True)
class StorageReport:
    """Almacenamiento medido: tablas, tamaño de la base y tamaño de los directorios de datos."""

    tables: list[TableStorage]
    database_bytes: int
    directories: dict[str, int | None]

    def schema_totals(self) -> dict[str, int]:
        """Suma de `pg_total_relation_size` por esquema."""
        totals: dict[str, int] = {}
        for table in self.tables:
            totals[table.schema] = totals.get(table.schema, 0) + table.total_bytes
        return totals


def bytes_per_row(size_bytes: int, rows: int) -> float | None:
    """Bytes por fila = tamaño / filas; `None` si no hay filas (no se divide por cero)."""
    return size_bytes / rows if rows > 0 else None


def directory_size(path: Path) -> int | None:
    """Suma de bytes de los archivos de un directorio (recursivo); `None` si no existe."""
    if not path.is_dir():
        return None
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


async def read_storage(conn: asyncpg.Connection, directories: dict[str, Path]) -> StorageReport:
    """Lee tamaños de tablas reales (con índices), recuentos y tamaño de los directorios.

    Recibe:
        conn: conexión de lectura (la transacción se abre de solo lectura); directories:
        nombre -> ruta de `data/historical/` y `data/catalogo/`.
    Devuelve:
        `StorageReport` con bytes por fila derivados del recuento real (`count(*)`).
    Por qué existe:
        El almacenamiento del coste y del razonamiento a 100 M se mide, no se supone (K6, FR-019).
    """
    tables = []
    async with conn.transaction(readonly=True):
        for row in await conn.fetch(TABLES_SQL, list(REAL_SCHEMAS)):
            rows = await conn.fetchval(f"SELECT count(*) FROM {row['qualified']}")
            tables.append(TableStorage(row["schema"], row["name"], rows, row["total_bytes"],
                                       row["index_bytes"], bytes_per_row(row["total_bytes"], rows)))
        database_bytes = await conn.fetchval(DATABASE_SIZE_SQL)
    return StorageReport(tables, database_bytes, {name: directory_size(path) for name, path in directories.items()})


async def read_bench_size(conn: asyncpg.Connection, size: int, index_names: list[str]) -> dict:
    """Tamaño SINTÉTICO de `bench.event_<size>`: montón (sin índices) y cada índice creado.

    Recibe:
        index_names: nombres de los índices de `bench` ya creados sobre esa tabla.
    Devuelve:
        `{"rows", "heap_bytes", "total_bytes", "indexes": {nombre: bytes}}`.
    """
    sized = {name: await conn.fetchval(BENCH_INDEX_SQL.format(name=name)) for name in index_names}
    return {"rows": size, "heap_bytes": await conn.fetchval(BENCH_HEAP_SQL.format(size=size)),
            "total_bytes": await conn.fetchval(BENCH_SIZE_SQL.format(size=size)), "indexes": sized}


async def measure_bench_storage(conn: asyncpg.Connection, size: int, definitions: list[IndexDef]) -> dict:
    """Crea los índices reales sobre `bench.event_<size>`, mide los tamaños y los borra (SINTÉTICO).

    Deja la tabla otra vez sin índices; los índices se crean con el sufijo `s<size>`.
    """
    created = [rewrite_index(d.defn, f"event_{size}", f"s{size}") for d in definitions]
    for index in created:
        await create_index(conn, index)
    try:
        return await read_bench_size(conn, size, [i.name for i in created])
    finally:
        for index in created:
            await drop_index(conn, index.name)


def _cell(value: float | None) -> str:
    """Celda numérica: formato con miles o «no disponible»."""
    return UNAVAILABLE if value is None else f"{value:,.1f}"


def render_storage_md(report: StorageReport, bench_sizes: list[dict] | None = None) -> str:
    """Genera `almacenamiento.md`: tablas reales y de `bench` (SINTÉTICO), directorios y volumen Docker."""
    lines = ["# Almacenamiento medido", "",
             "Tablas REALES: `pg_total_relation_size` (incluye índices y TOAST) y `pg_indexes_size`, con recuento "
             "real `count(*)`; bytes por fila = tamaño total / filas. Unidades: bytes (KiB = 1024 B).", "",
             "| Esquema | Tabla | Filas | Total (bytes) | Índices (bytes) | Bytes por fila |", "|---|---|---|---|---|---|"]
    for t in report.tables:
        lines.append(f"| {t.schema} | {t.name} | {t.rows} | {t.total_bytes} | {t.index_bytes} | {_cell(t.bytes_per_row)} |")
    lines += ["", "| Esquema | Total (bytes) |", "|---|---|"]
    lines += [f"| {schema} | {total} |" for schema, total in report.schema_totals().items()]
    lines += ["", f"Tamaño de la base completa (`pg_database_size`): {report.database_bytes} bytes.", "",
              "| Directorio | Bytes |", "|---|---|"]
    lines += [f"| {name} | {UNAVAILABLE if size is None else size} |" for name, size in report.directories.items()]
    lines += ["", f"Volumen de Docker de Postgres/Kafka: {DOCKER_VOLUME_NOTE}.", ""]
    if bench_sizes:
        lines += [f"## Tablas de `bench` ({SYNTHETIC_LABEL})", "",
                  "| Filas | Montón (bytes) | Con los 4 índices (bytes) | Bytes por fila (con índices) | Índice: bytes |",
                  "|---|---|---|---|---|"]
        for s in bench_sizes:
            per_row = _cell(bytes_per_row(s["total_bytes"], s["rows"]))
            indexes = "; ".join(f"{name}: {size}" for name, size in s["indexes"].items())
            lines.append(f"| {s['rows']} | {s['heap_bytes']} | {s['total_bytes']} | {per_row} | {indexes} |")
    return "\n".join(lines) + "\n"
