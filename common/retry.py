"""Reintentos con espera exponencial para conectar con Kafka y PostgreSQL (A4)."""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from common.config import RetrySettings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def next_delay(attempt: int, settings: RetrySettings) -> float:
    """Calcula la espera antes del intento siguiente.

    Qué hace:
        Duplica la espera inicial en cada intento hasta el máximo configurado.
    Recibe:
        attempt: número del intento fallido, empezando en 1.
        settings: espera inicial y máxima.
    Devuelve:
        Segundos de espera.
    Por qué existe:
        El orden de arranque no garantiza que Kafka o PostgreSQL estén listos (A4).
    """
    return min(settings.initial_seconds * 2 ** (attempt - 1), settings.max_seconds)


async def retry_forever(
    operation: Callable[[], Awaitable[T]],
    description: str,
    settings: RetrySettings,
    retriable: tuple[type[BaseException], ...],
) -> T:
    """Repite una operación hasta que tenga éxito.

    Qué hace:
        Ejecuta la operación; si falla con un error reintentable, lo registra y espera.
    Recibe:
        operation: función asíncrona sin argumentos.
        description: a qué se intenta conectar, para el registro (FR-009).
        settings: política de espera.
        retriable: tipos de excepción que provocan un nuevo intento.
    Devuelve:
        El resultado de la operación.
    Por qué existe:
        Productor, consumidor y API no deben terminar si el broker o la base tardan (FR-008).
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return await operation()
        except retriable as error:
            delay = next_delay(attempt, settings)
            logger.warning("Reintento %d: no se pudo conectar con %s (%s: %s). Nuevo intento en %.0f s.",
                           attempt, description, type(error).__name__, error, delay)
            await asyncio.sleep(delay)
