"""Acceso a la base: una transacción de lectura única por petición (D2, D8, D12)."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from api.errors import (CODE_DATABASE_UNAVAILABLE, MESSAGE_DATABASE_UNAVAILABLE, STATUS_SERVICE_UNAVAILABLE,
                        ApiError)
from common.db import RETRIABLE_DB_ERRORS

logger = logging.getLogger(__name__)

ISOLATION_LEVEL = "repeatable_read"


@asynccontextmanager
async def read_transaction(pool: asyncpg.Pool, timeout_seconds: float) -> AsyncIterator[asyncpg.Connection]:
    """Abre una conexión del pool y una transacción `REPEATABLE READ` de solo lectura.

    Qué hace:
        Toma una conexión esperando como máximo `timeout_seconds`; todas las consultas del bloque ven
        la misma instantánea. Cualquier fallo de base dentro del bloque sale como `ApiError` 503.
    Recibe:
        pool: pool del rol `observatory_api`; timeout_seconds: espera máxima por la conexión.
    Devuelve:
        La conexión, para usarla en el bloque `async with`.
    Por qué existe:
        `total` y las páginas o bloques de estadísticas deben coincidir aunque el consumidor escriba
        entre medias (FR-010), y la base caída debe ser 503, nunca una respuesta vacía (F8).
    """
    try:
        async with pool.acquire(timeout=timeout_seconds) as connection:
            async with connection.transaction(isolation=ISOLATION_LEVEL, readonly=True):
                yield connection
    except RETRIABLE_DB_ERRORS as error:
        logger.error("La consulta a la base falló: %s", type(error).__name__)
        raise ApiError(STATUS_SERVICE_UNAVAILABLE, CODE_DATABASE_UNAVAILABLE,
                       MESSAGE_DATABASE_UNAVAILABLE) from error
