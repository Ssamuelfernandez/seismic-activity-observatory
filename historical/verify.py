"""Verificación de la carga histórica con SQL sobre el estado actual (B14, B17, research D7)."""
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from consumer import queries

# El rol `observatory_consumer` no puede leer la cuarentena (solo INSERT): su huella la toma un administrador.
FINGERPRINT_QUERIES = {
    "current_event": queries.FINGERPRINT_CURRENT,
    "event_version": queries.FINGERPRINT_VERSION,
}


@dataclass(frozen=True)
class VerifyResult:
    """Resultado de `verify_load`: cifras comparadas y mensaje legible."""

    ok: bool
    unique: int
    quarantined: int
    expected: int
    loaded: int
    historical_rows: int
    message: str


async def verify_load(pool: Any, unique_ids: Collection[str], quarantined_ids: Collection[str]
                      ) -> VerifyResult:
    """Comprueba que `current_event` contiene `|U| - |Q|` de los eventos cargados.

    Qué hace:
        Con U = ids únicos de los archivos y Q = ids de U que esta carga mandó a cuarentena
        (el rol del consumidor no puede leer `live.quarantine`), compara
        `count(current_event de U)` con `|U| - |Q|`. También informa de cuántas filas tienen
        `source = usgs_historical` (igual a `|U| - |Q|` solo sobre una base limpia).
    Recibe:
        pool: pool de asyncpg; unique_ids: ids únicos de la carga; quarantined_ids: ids
        que `process_record` envió a cuarentena en esa carga.
    Devuelve:
        `VerifyResult`; `ok` es falso con una discrepancia y el mensaje trae ambas cifras.
    Por qué existe:
        Demuestra que no se perdió ni se duplicó ningún evento (SC-004, constitución §8).
    """
    ids = sorted(set(unique_ids))
    async with pool.acquire() as conn:
        loaded = await conn.fetchval(queries.HISTORICAL_LOADED_COUNT, ids)
        historical_rows = await conn.fetchval(queries.HISTORICAL_SOURCE_COUNT)
    quarantined = len(set(ids) & set(quarantined_ids))
    expected = len(ids) - quarantined
    ok = loaded == expected
    message = (f"unique={len(ids)} quarantined={quarantined} expected={expected} loaded={loaded} "
               f"historical_rows={historical_rows}")
    return VerifyResult(ok, len(ids), quarantined, expected, loaded, historical_rows, message)


async def snapshot_fingerprint(pool: Any) -> dict[str, tuple[int, str]]:
    """Huella (recuento, md5) de `current_event` y `event_version` (las que el consumidor puede leer).

    Sirve para demostrar «0 diferencias» antes y después de recargar (B17, SC-005).
    """
    result: dict[str, tuple[int, str]] = {}
    async with pool.acquire() as conn:
        for name, sql in FINGERPRINT_QUERIES.items():
            row = await conn.fetchrow(sql)
            result[name] = (row[0], row[1])
    return result
