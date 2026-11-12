"""Referencia real de índices con el rol `observatory_api`, solo lectura (T083, E6, FR-016, FR-019).

Los índices y la transacción de solo lectura se comprueban en la base temporal (esquema real,
sin datos); el recuento de `usgs_historical` se lee de la base real del stack (solo lectura).
"""
import asyncio
import os

import asyncpg
import pytest

from scripts.benchmarks.storage import read_real_reference, render_real_reference
from tests.support.temp_database import TempDatabase

USGS_HISTORICAL_ROWS = 18_302


def test_four_real_indexes_with_size_and_idx_scan_in_read_only_transaction(db: TempDatabase) -> None:
    async def main():
        pool = await db.api_pool()
        try:
            async with pool.acquire() as conn:
                reference = await read_real_reference(conn)
                with pytest.raises(asyncpg.PostgresError):
                    await conn.execute("INSERT INTO live.current_event (event_id) VALUES ('x')")
                return reference
        finally:
            await pool.close()
    reference = asyncio.run(main())
    assert len(reference.indexes) == 4 and reference.read_only is True
    assert all(i.size_bytes > 0 and i.idx_scan >= 0 and i.definition.startswith("CREATE") for i in reference.indexes)
    assert reference.counts["replay.current_event"] == 0 and "ix_current_event_mag" in render_real_reference(reference)


def test_real_database_has_18302_usgs_historical_rows() -> None:
    async def main():
        conn = await asyncpg.connect(host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]),
                                     database=os.environ["DB_NAME"], user="observatory_api",
                                     password=os.environ["DB_API_PASSWORD"], timeout=10)
        try:
            return await read_real_reference(conn)
        finally:
            await conn.close()
    reference = asyncio.run(main())
    assert reference.usgs_historical == USGS_HISTORICAL_ROWS and reference.read_only is True
    assert len(reference.indexes) == 4


def test_real_storage_bytes_per_row_equals_size_over_real_count_and_is_positive() -> None:
    """T084: tamaños con `pg_total_relation_size` de las tablas reales; bytes por fila = tamaño / recuento real."""
    from pathlib import Path

    from scripts.benchmarks.bench_schema import connect_admin
    from scripts.benchmarks.storage import read_storage, render_storage_md

    async def main():
        conn = await connect_admin(dict(os.environ))
        try:
            return await read_storage(conn, {"data/historical": Path("/app/data/historical"),
                                             "data/catalogo": Path("/app/data/catalogo")})
        finally:
            await conn.close()
    report = asyncio.run(main())
    current = next(t for t in report.tables if (t.schema, t.name) == ("live", "current_event"))
    assert current.rows >= USGS_HISTORICAL_ROWS and current.total_bytes > current.index_bytes > 0
    assert current.bytes_per_row == current.total_bytes / current.rows
    assert all(t.total_bytes > 0 for t in report.tables) and report.database_bytes > 0
    assert all(size and size > 0 for size in report.directories.values())
    assert "bytes por fila" in render_storage_md(report).lower() and "no disponible" in render_storage_md(report)
