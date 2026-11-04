"""Líneas de registro de decisión por mensaje y volcado periódico de contadores (FR-003, FR-023, C8).

Formato: `specs/003-consumidor-idempotente/contracts/consumer-runtime.md` §4.
"""
import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from common.records import ProcessingResult, ResultKind, VersionOutcome
from consumer.counters import Counters, snapshot

logger = logging.getLogger(__name__)

COUNTERS_LOG_INTERVAL_SECONDS = 60
NO_VALUE = "-"
DECISION_QUARANTINED = "quarantined"
DECISION_QUARANTINE_DUPLICATE = "quarantine_duplicate"


def _decision_name(result: ProcessingResult) -> str:
    """Nombre de la decisión: el valor del resultado de versión o el de cuarentena."""
    if result.kind is ResultKind.EVENT:
        return result.outcome.value
    return DECISION_QUARANTINED if result.inserted else DECISION_QUARANTINE_DUPLICATE


def log_decision(result: ProcessingResult) -> None:
    """Escribe la línea de decisión de un mensaje (una por decisión).

    Qué hace:
        INFO `decision=… event_id=<id|-> topic=… partition=… offset=…`, con `reason=` solo en
        cuarentena; el conflicto «mismo updated, contenido distinto» es un único WARNING con
        `updated_ms`.
    Recibe:
        result: resultado de `process_record` (su `ref` y `event_id` dan los campos).
    Devuelve:
        Nada.
    Por qué existe:
        FR-003: cada mensaje deja una línea con su decisión, antes del commit del offset.
    """
    ref = result.ref
    event_id = result.event_id or NO_VALUE
    if result.outcome is VersionOutcome.SAME_UPDATED_CONFLICT:
        logger.warning("decision=%s event_id=%s updated_ms=%s topic=%s partition=%d offset=%d",
                       _decision_name(result), event_id, result.updated_ms, ref.topic, ref.partition, ref.offset)
        return
    line = f"decision={_decision_name(result)} event_id={event_id} topic={ref.topic} " \
           f"partition={ref.partition} offset={ref.offset}"
    if result.kind is ResultKind.QUARANTINE:
        line += f" reason={result.reason}"
    logger.info(line)


def dump_counters(counters: Counters) -> None:
    """Escribe una línea `COUNTERS {json}` con los contadores y las claves ordenadas."""
    logger.info("COUNTERS %s", json.dumps(snapshot(counters), sort_keys=True, separators=(",", ":")))


async def run_counters_dump(counters: Counters, interval_seconds: float = COUNTERS_LOG_INTERVAL_SECONDS,
                            sleep: Callable[[float], Awaitable[None]] = asyncio.sleep) -> None:
    """Vuelca los contadores cada `interval_seconds` y una vez más al ser cancelada.

    Qué hace:
        Bucle de espera y volcado. No mira `stop_event`: el bucle de consumo la cancela y la
        espera al detenerse; solo entonces escribe el volcado final, una sola vez.
    Recibe:
        counters: estado compartido con el bucle; interval_seconds: periodo; sleep: espera
        (inyectable para simular el reloj en las pruebas).
    Devuelve:
        Nunca termina por sí misma; relanza `CancelledError` tras el volcado final.
    Por qué existe:
        C8 pide ver los contadores durante la sesión y el resumen al detenerse (FR-023).
    """
    try:
        while True:
            await sleep(interval_seconds)
            dump_counters(counters)
    except asyncio.CancelledError:
        dump_counters(counters)
        raise
