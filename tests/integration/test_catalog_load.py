"""Carga del catálogo en `public.country` contra PostgreSQL real, con el rol del consumidor (T008).

El catálogo es el real (`data/catalogo/paises.geojson`); el repetido es un GeoJSON sintético.
"""
import asyncio
import hashlib
import json
import logging
from pathlib import Path

import asyncpg
import pytest

from common.geo import CatalogError
from consumer.catalog_loader import load_country_catalog
from tests.support import evidence
from tests.support.temp_database import TempDatabase

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "catalogo" / "paises.geojson"
TOTAL = 177
ROWS_SQL = "SELECT country_id, name_es, admin, continent, subregion FROM public.country ORDER BY country_id"
COUNT_SQL = "SELECT count(*) AS paises, count(DISTINCT country_id) AS codigos FROM public.country"
LOG_LINE = "catalog loaded total=177 inserted={} updated={}"


async def _load(db: TempDatabase, path: Path):
    pool = await asyncpg.create_pool(host=db.host, port=db.port, database=db.name, user=db.consumer_user,
                                     password=db.consumer_password, min_size=1, max_size=2)
    try:
        return await load_country_catalog(pool, path)
    finally:
        await pool.close()


async def _admin(db: TempDatabase, sql: str) -> list[tuple]:
    conn = await db.admin()
    try:
        return [tuple(r.values()) for r in await conn.fetch(sql)]
    finally:
        await conn.close()


async def _record_count(db: TempDatabase) -> None:
    conn = await db.admin()
    try:
        await evidence.record_query(conn, "geografia_catalogo_carga", COUNT_SQL,
                                    label="tras dos cargas del catálogo real")
    finally:
        await conn.close()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_first_load_inserts_177_and_second_changes_nothing(db: TempDatabase, caplog) -> None:
    hash_before = _sha(CATALOG_PATH)
    with caplog.at_level(logging.INFO, logger="consumer.catalog_loader"):
        _, first = asyncio.run(_load(db, CATALOG_PATH))
        rows_first = asyncio.run(_admin(db, ROWS_SQL))
        _, second = asyncio.run(_load(db, CATALOG_PATH))
    rows_second = asyncio.run(_admin(db, ROWS_SQL))
    assert (first.total, first.inserted, first.updated) == (TOTAL, TOTAL, 0)
    assert (second.total, second.inserted, second.updated) == (TOTAL, 0, 0)
    assert len(rows_first) == TOTAL and rows_first == rows_second
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("catalog loaded")]
    assert lines == [LOG_LINE.format(TOTAL, 0), LOG_LINE.format(0, 0)]
    assert _sha(CATALOG_PATH) == hash_before
    asyncio.run(_record_count(db))


def test_hand_altered_row_is_corrected(db: TempDatabase) -> None:
    asyncio.run(_load(db, CATALOG_PATH))
    original = asyncio.run(_admin(db, "SELECT name_es FROM public.country WHERE country_id = 'ESP'"))
    asyncio.run(_admin(db, "UPDATE public.country SET name_es = 'ALTERADO' WHERE country_id = 'ESP' RETURNING 1"))
    _, result = asyncio.run(_load(db, CATALOG_PATH))
    assert (result.inserted, result.updated) == (0, 1)
    assert asyncio.run(_admin(db, "SELECT name_es FROM public.country WHERE country_id = 'ESP'")) == original


def test_duplicate_code_raises_and_leaves_table_unchanged(db: TempDatabase, tmp_path: Path) -> None:
    asyncio.run(_load(db, CATALOG_PATH))
    before = asyncio.run(_admin(db, ROWS_SQL))
    square = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    props = {"ADM0_A3": "ZZZ", "NAME_ES": "Sintético", "ADMIN": "Synthetic", "CONTINENT": "X", "SUBREGION": "Y"}
    feature = {"type": "Feature", "properties": props, "geometry": square}
    bad = tmp_path / "duplicado.geojson"
    bad.write_text(json.dumps({"type": "FeatureCollection", "features": [feature, feature]}), encoding="utf-8")
    with pytest.raises(CatalogError, match="ZZZ"):
        asyncio.run(_load(db, bad))
    assert asyncio.run(_admin(db, ROWS_SQL)) == before
