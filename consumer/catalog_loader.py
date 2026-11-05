"""Carga del catálogo de países en `public.country` al arrancar (C10, FR-009 a FR-012).

Lee el archivo en solo lectura, lo valida con `common/geo.py` y lo vuelca en una transacción.
Es repetible: cargar dos veces el mismo archivo no cambia nada (SC-005).
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common.geo import CountryCatalog, CountryIndex, build_country_index, parse_country_catalog
from common.records import CountryRow
from consumer.queries import COUNTRY_COUNT, COUNTRY_UPSERT

logger = logging.getLogger(__name__)

CHANGED_TAG = "INSERT 0 1"


@dataclass(frozen=True)
class CatalogLoadResult:
    """Resultado de una carga: entidades del archivo, filas nuevas y filas corregidas."""

    total: int
    inserted: int
    updated: int


def _values(row: CountryRow) -> tuple[str, str, str, str, str]:
    """Valores de una `CountryRow` en el orden de `COUNTRY_COLUMNS`."""
    return (row.country_id, row.name_es, row.admin, row.continent, row.subregion)


async def _upsert_catalog(conn: Any, catalog: CountryCatalog) -> CatalogLoadResult:
    """Hace el upsert fila a fila en una transacción y calcula nuevas y corregidas.

    La etiqueta del comando no distingue insertar de actualizar: `inserted` sale de contar
    antes y después, y `updated` es lo cambiado menos lo insertado.
    """
    async with conn.transaction():
        before = await conn.fetchval(COUNTRY_COUNT)
        changed = 0
        for entry in catalog.entries:
            tag = await conn.execute(COUNTRY_UPSERT, *_values(entry.row))
            changed += tag == CHANGED_TAG
        inserted = await conn.fetchval(COUNTRY_COUNT) - before
    return CatalogLoadResult(len(catalog.entries), inserted, changed - inserted)


async def load_country_catalog(pool: Any, path: str | Path) -> tuple[CountryIndex, CatalogLoadResult]:
    """Carga el catálogo y devuelve el índice espacial listo para asignar países.

    Qué hace:
        Lee el GeoJSON, lo parsea (unicidad de `ADM0_A3`), construye el `STRtree` y hace el
        upsert de `public.country` en una sola transacción; escribe una línea INFO.
    Recibe:
        pool: pool de asyncpg con el rol del consumidor.
        path: ruta del GeoJSON (`COUNTRY_CATALOG_PATH`).
    Devuelve:
        El índice y el resultado (`total`, `inserted`, `updated`).
    Por qué existe:
        El FK de `current_event.country_id` exige que el catálogo esté en la base antes de
        consumir. Si el catálogo no es válido lanza `CatalogError` sin tocar la base.
    """
    with open(path, encoding="utf-8") as handle:
        catalog = parse_country_catalog(json.load(handle))
    index = build_country_index(catalog)
    async with pool.acquire() as conn:
        result = await _upsert_catalog(conn, catalog)
    logger.info("catalog loaded total=%d inserted=%d updated=%d",
                result.total, result.inserted, result.updated)
    return index, result
