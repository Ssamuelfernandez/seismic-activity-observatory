"""Conexión a PostgreSQL con reintentos (A4). Cada servicio usa su propio rol (FR-030)."""
import asyncio
import logging

import asyncpg

from common.config import DatabaseSettings, RetrySettings
from common.retry import retry_forever

logger = logging.getLogger(__name__)

COMMAND_TIMEOUT_SECONDS = 5
POOL_MIN_SIZE = 1
POOL_MAX_SIZE = 4
# Errores de conexión que justifican reintentar (la base arranca, reinicia o aún no acepta).
RETRIABLE_DB_ERRORS = (OSError, asyncpg.PostgresError, asyncpg.InterfaceError, asyncio.TimeoutError)


async def connect(settings: DatabaseSettings) -> asyncpg.Connection:
    """Abre una conexión con el rol del servicio."""
    return await asyncpg.connect(
        host=settings.host, port=settings.port, database=settings.name,
        user=settings.user, password=settings.password, timeout=COMMAND_TIMEOUT_SECONDS,
    )


async def create_pool(settings: DatabaseSettings) -> asyncpg.Pool:
    """Crea un pool de conexiones con el rol del servicio."""
    return await asyncpg.create_pool(
        host=settings.host, port=settings.port, database=settings.name,
        user=settings.user, password=settings.password,
        min_size=POOL_MIN_SIZE, max_size=POOL_MAX_SIZE, command_timeout=COMMAND_TIMEOUT_SECONDS,
    )


async def create_pool_with_retry(settings: DatabaseSettings, retry: RetrySettings) -> asyncpg.Pool:
    """Crea el pool reintentando hasta que la base esté lista (A4)."""
    return await retry_forever(lambda: create_pool(settings), f"PostgreSQL ({settings.host})",
                               retry, RETRIABLE_DB_ERRORS)


async def check_database(settings: DatabaseSettings, retry: RetrySettings) -> None:
    """Comprueba que la base acepta conexiones con el rol del servicio.

    Qué hace:
        Abre una conexión con reintentos, ejecuta `SELECT 1` y la cierra.
    Recibe:
        settings: conexión y rol; retry: política de reintentos.
    Devuelve:
        Nada.
    Por qué existe:
        Productor y consumidor mínimos no escriben aún, pero deben demostrar que su rol conecta (FR-030).
    """
    async def attempt() -> None:
        connection = await connect(settings)
        try:
            await connection.fetchval("SELECT 1")
        finally:
            await connection.close()

    await retry_forever(attempt, f"PostgreSQL ({settings.host})", retry, RETRIABLE_DB_ERRORS)
    logger.info("PostgreSQL disponible con el rol %s.", settings.user)
