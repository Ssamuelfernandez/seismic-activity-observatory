"""Bucle del productor: ciclo, latido y espera, con backoff por fallos consecutivos (B1, B10, A10)."""
import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from common.backoff import PRODUCTION_BACKOFF, BackoffSettings, compute_backoff_seconds
from common.config import (
    DatabaseSettings, FeedSettings, HealthSettings, KafkaSettings, RetrySettings,
)
from common.db import check_database, create_pool_with_retry
from common.health import clear_heartbeat, touch_heartbeat
from common.kafka_topics import ensure_topics
from common.retry import retry_forever
from producer.cycle import CycleDeps, CycleResult, STATUS_FETCH_ERROR, STATUS_OK, run_cycle
from producer.ingest_store import PoolIngestStore
from producer.publisher import RETRIABLE_KAFKA_ERRORS, publish_message, start_producer
from producer.usgs_client import fetch_feed

logger = logging.getLogger(__name__)

# El productor está vivo si el ciclo fue correcto o si falló solo USGS (plan.md §3).
HEARTBEAT_STATUSES = (STATUS_OK, STATUS_FETCH_ERROR)
NO_HTTP_STATUS = "-"


@dataclass(frozen=True)
class ProducerSettings:
    """Configuración completa del productor."""

    kafka: KafkaSettings
    database: DatabaseSettings
    retry: RetrySettings
    health: HealthSettings
    feed: FeedSettings


def format_cycle_line(number: int, result: CycleResult, next_wait_seconds: float) -> str:
    """Línea de log de un ciclo con el formato de data-model.md §6."""
    http = NO_HTTP_STATUS if result.http is None else result.http
    return (f"cycle={number} status={result.status} http={http} latency_ms={result.latency_ms} "
            f"fetched={result.fetched} excluded={result.excluded} published={result.published} "
            f"skipped={result.skipped} unmarked={result.unmarked} next_wait_s={next_wait_seconds:.1f}")


async def run_loop(run_one: Callable[[], Awaitable[CycleResult]], touch: Callable[[], None],
                   sleep: Callable[[float], Awaitable[None]], poll_seconds: float,
                   backoff: BackoffSettings, jitter: Callable[[], float],
                   max_cycles: int | None = None) -> None:
    """Repite ciclo, latido y espera; tras un fallo la espera crece (backoff) y tras un éxito vuelve a `poll_seconds`.

    Qué hace:
        Cuenta los fallos consecutivos. El latido se renueva tras un ciclo correcto o un fallo
        controlado de USGS, no tras un fallo de Kafka o PostgreSQL.
    Recibe:
        run_one: un ciclo; touch: renueva el latido; sleep: espera; poll_seconds: espera normal;
        backoff: parámetros del backoff; jitter: fuente de números en [0, 1]; max_cycles: tope (solo pruebas).
    Devuelve:
        Nada; sin tope no termina por sí mismo.
    Por qué existe:
        Reintentar sin golpear a USGS durante una caída y sin dar por muerto a un productor sano (B10).
    """
    failures = 0
    number = 0
    while max_cycles is None or number < max_cycles:
        number += 1
        result = await run_one()
        failures = 0 if result.status == STATUS_OK else failures + 1
        wait = poll_seconds if failures == 0 else compute_backoff_seconds(failures, backoff, jitter())
        if result.status in HEARTBEAT_STATUSES:
            touch()
        logger.info(format_cycle_line(number, result, wait))
        await sleep(wait)


async def run_producer(settings: ProducerSettings) -> None:
    """Arranca las conexiones y ejecuta ciclos mientras el proceso viva.

    Qué hace:
        Espera a PostgreSQL y a Kafka, asegura los temas y entra en el bucle de ciclos.
    Recibe:
        settings: configuración del productor.
    Devuelve:
        Nunca termina por sí mismo.
    Por qué existe:
        Productor real del feed de USGS con reintentos de arranque (A4) y cierre ordenado.
    """
    clear_heartbeat(settings.health.heartbeat_file)
    await check_database(settings.database, settings.retry)
    pool = await create_pool_with_retry(settings.database, settings.retry)
    producer = await start_producer(settings.kafka, settings.retry)
    try:
        await retry_forever(lambda: ensure_topics(settings.kafka.bootstrap_servers),
                            "Kafka (creación de temas)", settings.retry, RETRIABLE_KAFKA_ERRORS)
        await _loop_with_connections(settings, pool, producer)
    finally:
        await producer.stop()
        await pool.close()


async def _loop_with_connections(settings: ProducerSettings, pool, producer) -> None:
    """Monta las dependencias del ciclo con las conexiones abiertas y lanza el bucle."""
    async def publish(key: str | None, message: dict) -> None:
        await publish_message(producer, settings.kafka.topic, key, message)

    deps = CycleDeps(fetch=fetch_feed, store=PoolIngestStore(pool), publish=publish,
                     now=lambda: datetime.now(timezone.utc))
    await run_loop(
        run_one=lambda: run_cycle(deps, settings.feed),
        touch=lambda: touch_heartbeat(settings.health.heartbeat_file),
        sleep=asyncio.sleep, poll_seconds=settings.feed.poll_seconds,
        backoff=PRODUCTION_BACKOFF, jitter=random.random,
    )
