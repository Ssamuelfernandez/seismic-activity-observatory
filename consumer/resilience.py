"""Reintentos sin límite de la escritura en PostgreSQL y del commit del offset (FR-014, FR-029, C2).

Una línea `WARNING` por intento, sin traceback, con los campos de `consumer-runtime.md` §4. La
espera se interrumpe con `stop_event` (parada limpia) sin confirmar ningún offset.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import asyncpg
from aiokafka.errors import CommitFailedError, KafkaError
from aiokafka.structs import TopicPartition

from common.config import RetrySettings
from common.records import MessageRef
from common.retry import next_delay
from consumer.db_errors import is_content_error

logger = logging.getLogger(__name__)

T = TypeVar("T")

ERROR_TEXT_MAX_CHARS = 200
NO_VALUE = "-"
OP_COMMIT_OFFSET = "commit_offset"
DB_RETRIABLE = (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, asyncio.TimeoutError)
KAFKA_RETRIABLE = (KafkaError, OSError)


class StopRequested(Exception):
    """Se pidió parar (SIGTERM/SIGINT) mientras se esperaba entre reintentos."""


@dataclass(frozen=True)
class OpContext:
    """Operación en curso y mensaje al que pertenece, para la línea `retry`."""

    op: str
    event_id: str | None
    ref: MessageRef


@dataclass(frozen=True)
class RetryControl:
    """Política de espera y señal de parada que comparten todos los reintentos."""

    settings: RetrySettings
    stop_event: asyncio.Event


@dataclass(frozen=True)
class ErrorRule:
    """Qué excepciones se reintentan y cuáles se propagan aunque sean de ese tipo."""

    retriable: tuple[type[BaseException], ...]
    propagate: Callable[[BaseException], bool]


async def wait_or_stop(stop_event: asyncio.Event, delay_seconds: float) -> bool:
    """Espera `delay_seconds` o hasta que se active `stop_event`; devuelve True si se pidió parar."""
    try:
        await asyncio.wait_for(stop_event.wait(), delay_seconds)
    except asyncio.TimeoutError:
        return False
    return True


def _log_retry(attempt: int, delay: float, context: OpContext, error: BaseException) -> None:
    """Escribe la línea `retry` de `consumer-runtime.md` §4 (una por intento, sin traceback)."""
    detail = " ".join(str(error).split())[:ERROR_TEXT_MAX_CHARS]
    sqlstate = getattr(error, "sqlstate", None) or NO_VALUE
    ref = context.ref
    logger.warning(
        'retry attempt=%d wait_s=%g op=%s event_id=%s topic=%s partition=%d offset=%d '
        'error=%s sqlstate=%s detail="%s"',
        attempt, delay, context.op, context.event_id or NO_VALUE, ref.topic, ref.partition, ref.offset,
        type(error).__name__, sqlstate, detail,
    )


async def _retry(operation: Callable[[], Awaitable[T]], context: OpContext, control: RetryControl,
                 rule: ErrorRule) -> T:
    """Repite la operación hasta que tenga éxito; no hay límite de intentos."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return await operation()
        except rule.retriable as error:
            if rule.propagate(error):
                raise
            delay = next_delay(attempt, control.settings)
            _log_retry(attempt, delay, context, error)
            if await wait_or_stop(control.stop_event, delay):
                raise StopRequested() from error


async def retry_db_operation(operation: Callable[[], Awaitable[T]], context: OpContext,
                             control: RetryControl, retry_content: bool = False) -> T:
    """Ejecuta una escritura en PostgreSQL reintentando los fallos que no dependen del contenido.

    Qué hace:
        Reintenta sin límite, con espera 1, 2, 4, 8, 16 y 30 s, los errores de la base
        (`PostgresError`, `InterfaceError`, `OSError`, `TimeoutError`). Un error de contenido
        (`is_content_error`) se propaga al llamador, salvo con `retry_content` (la cuarentena
        nunca se vuelve a cuarentena: su fallo es error de base). Un defecto (`TypeError`...)
        no se captura.
    Recibe:
        operation: corrutina sin argumentos; context: operación y mensaje para el registro;
        control: política de espera y `stop_event`; retry_content: reintentar también contenido.
    Devuelve:
        El resultado de la operación.
    Por qué existe:
        Una caída de la base no debe perder ni saltarse mensajes: el offset no se confirma
        hasta que la escritura tenga éxito (C2, FR-014, FR-029).
    """
    retriable = DB_RETRIABLE + ((UnicodeError,) if retry_content else ())
    propagate = (lambda error: False) if retry_content else is_content_error
    return await _retry(operation, context, control, ErrorRule(retriable, propagate))


async def commit_offset_with_retry(consumer: Any, context: OpContext, control: RetryControl) -> bool:
    """Confirma el offset del mensaje (`offset + 1`) reintentando los fallos de comunicación.

    Qué hace:
        `CommitFailedError` (el grupo cambió de generación) no se reintenta: se registra y se
        sigue, porque el mensaje se reentregará y la base es idempotente. Otros `KafkaError` y
        `OSError` se reintentan con la misma espera que la base.
    Recibe:
        consumer: consumidor de Kafka; context: mensaje (su `ref` da tema, partición y offset);
        control: política de espera y `stop_event`.
    Devuelve:
        True si el offset quedó confirmado; False si se saltó por `CommitFailedError`.
    Por qué existe:
        El offset se confirma siempre después del commit en PostgreSQL (constitución §1, C2).
    """
    ref = context.ref
    offsets = {TopicPartition(ref.topic, ref.partition): ref.offset + 1}
    rule = ErrorRule(KAFKA_RETRIABLE, lambda error: isinstance(error, CommitFailedError))
    try:
        await _retry(lambda: consumer.commit(offsets), context, control, rule)
    except CommitFailedError as error:
        _log_retry_skipped(context, error)
        return False
    return True


def _log_retry_skipped(context: OpContext, error: CommitFailedError) -> None:
    """Registra que el commit del offset se salta (el mensaje se reentregará)."""
    ref = context.ref
    logger.warning("commit_skipped event_id=%s topic=%s partition=%d offset=%d error=%s",
                   context.event_id or NO_VALUE, ref.topic, ref.partition, ref.offset, type(error).__name__)
