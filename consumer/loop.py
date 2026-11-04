"""Bucle del consumidor idempotente: un mensaje por vuelta, offset después del commit (C2, FR-001).

Orden por mensaje (plan §1): `pipeline.process_record` (escritura y gancho) -> `log_decision` ->
`commit_offset_with_retry` -> `apply_result`. El bucle no escribe nunca el volcado de contadores:
cancela y espera a la corrutina periódica de `reporting`, que lo escribe al ser cancelada.
"""
import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from common.config import DatabaseSettings, HealthSettings, KafkaSettings, RetrySettings
from common.db import check_database, create_pool_with_retry
from common.health import clear_heartbeat, touch_heartbeat
from common.kafka_topics import ensure_topics
from common.records import RawRecord
from common.retry import retry_forever
from consumer.counters import Counters, apply_result
from consumer.fault_hook import AfterDbCommit
from consumer.pipeline import PipelineDeps, bind_pool_writers, process_record
from consumer.reporting import log_decision, run_counters_dump
from consumer.resilience import OpContext, RetryControl, StopRequested, commit_offset_with_retry

logger = logging.getLogger(__name__)

POLL_TIMEOUT_MS = 1000
MAX_RECORDS_PER_POLL = 1
# 24 h: un reintento largo de la base no debe expulsar al consumidor del grupo (plan §5).
MAX_POLL_INTERVAL_MS = 86_400_000
# Cada cuántos segundos se comprueba que el broker responde, y cuánto se espera la respuesta.
HEALTH_PROBE_INTERVAL_SECONDS = 10
HEALTH_PROBE_TIMEOUT_SECONDS = 5
RETRIABLE_KAFKA_ERRORS = (KafkaError, OSError)
OP_COMMIT_OFFSET = "commit_offset"


@dataclass(frozen=True)
class ConsumerSettings:
    """Configuración completa del consumidor."""

    kafka: KafkaSettings
    database: DatabaseSettings
    retry: RetrySettings
    health: HealthSettings
    group_id: str


@dataclass
class HealthProbe:
    """Último resultado del sondeo del broker y cuándo se hizo (para el latido)."""

    reachable: bool = False
    last_probe: float = 0.0


@dataclass(frozen=True)
class LoopContext:
    """Todo lo que necesita una vuelta del bucle."""

    consumer: Any
    deps: PipelineDeps
    counters: Counters
    health: HealthSettings
    stop_event: asyncio.Event
    bootstrap_servers: str
    probe: HealthProbe = field(default_factory=HealthProbe)


async def start_consumer(settings: ConsumerSettings) -> AIOKafkaConsumer:
    """Arranca el consumidor reintentando hasta que el broker y el tema existan."""
    async def attempt() -> AIOKafkaConsumer:
        await ensure_topics(settings.kafka.bootstrap_servers)
        consumer = AIOKafkaConsumer(
            settings.kafka.topic,
            bootstrap_servers=settings.kafka.bootstrap_servers,
            group_id=settings.group_id,
            auto_offset_reset="earliest",
            # El offset se confirma a mano, solo después del commit en PostgreSQL (constitución §1).
            enable_auto_commit=False,
            max_poll_interval_ms=MAX_POLL_INTERVAL_MS,
        )
        try:
            await consumer.start()
        except BaseException:
            await consumer.stop()
            raise
        return consumer

    return await retry_forever(attempt, f"Kafka ({settings.kafka.bootstrap_servers})", settings.retry,
                               RETRIABLE_KAFKA_ERRORS)


async def broker_reachable(consumer: Any, bootstrap_servers: str) -> bool:
    """Comprueba que el consumidor puede hablar con el broker.

    Qué hace:
        Pide al broker el último offset de las particiones asignadas, con un tiempo máximo de
        espera. Si falla, escribe una línea `broker_unreachable` (una por sondeo, sin traceback).
    Recibe:
        consumer: consumidor ya suscrito; bootstrap_servers: dirección del broker, para el registro.
    Devuelve:
        True si el broker respondió a tiempo; False si no hay particiones asignadas o falló la consulta.
    Por qué existe:
        `getmany` devuelve vacío con el broker caído, así que sin esta comprobación el latido seguiría
        renovándose y el consumidor nunca pasaría a unhealthy (A4, FR-029).
    """
    partitions = consumer.assignment()
    if not partitions:
        return False
    try:
        await asyncio.wait_for(consumer.end_offsets(list(partitions)), HEALTH_PROBE_TIMEOUT_SECONDS)
    except (KafkaError, OSError, asyncio.TimeoutError) as error:
        logger.warning("broker_unreachable bootstrap=%s error=%s", bootstrap_servers, type(error).__name__)
        return False
    return True


def to_raw_record(record: Any) -> RawRecord:
    """Convierte un registro de `aiokafka` en un `RawRecord` (aísla el resto del código de la librería)."""
    return RawRecord(record.topic, record.partition, record.offset, record.key, record.value)


async def process_and_commit(raw: RawRecord, context: LoopContext) -> None:
    """Procesa un mensaje y, solo después, escribe la línea de decisión, confirma el offset y cuenta."""
    result = await process_record(raw, context.deps)
    log_decision(result)
    commit_context = OpContext(OP_COMMIT_OFFSET, result.event_id, result.ref)
    if await commit_offset_with_retry(context.consumer, commit_context, context.deps.control):
        apply_result(context.counters, result)


async def _refresh_heartbeat(context: LoopContext) -> None:
    """Sondea el broker cada `HEALTH_PROBE_INTERVAL_SECONDS` y renueva el latido si responde."""
    probe = context.probe
    if time.monotonic() - probe.last_probe >= HEALTH_PROBE_INTERVAL_SECONDS:
        probe.reachable = await broker_reachable(context.consumer, context.bootstrap_servers)
        probe.last_probe = time.monotonic()
    if probe.reachable:
        touch_heartbeat(context.health.heartbeat_file)


async def consume_once(context: LoopContext) -> None:
    """Una vuelta: pide como máximo un mensaje, lo procesa y renueva el latido.

    El latido solo se renueva al terminar la vuelta completa; durante un reintento el bucle no
    avanza y no se renueva (FR-029).
    """
    batches = await context.consumer.getmany(timeout_ms=POLL_TIMEOUT_MS, max_records=MAX_RECORDS_PER_POLL)
    for records in batches.values():
        for record in records:
            await process_and_commit(to_raw_record(record), context)
    await _refresh_heartbeat(context)


async def consume_until_stopped(context: LoopContext) -> None:
    """Consume hasta que `stop_event` se active y deja escrito el volcado final de contadores.

    Qué hace:
        Lanza la corrutina periódica de contadores, repite `consume_once` y, al terminar, la
        cancela y la espera: es ella quien escribe el único `COUNTERS` final.
    Recibe:
        context: consumidor, escritores, contadores, latido y señal de parada.
    Devuelve:
        Nada.
    Por qué existe:
        Parada limpia: ningún mensaje queda a medias y el resumen refleja el último offset
        confirmado (FR-023).
    """
    dump_task = asyncio.create_task(run_counters_dump(context.counters))
    # Cede el control una vez para que la tarea arranque: una tarea cancelada antes de empezar no escribe el volcado final.
    await asyncio.sleep(0)
    try:
        while not context.stop_event.is_set():
            await consume_once(context)
    except StopRequested:
        logger.info("Parada solicitada: el mensaje en curso no se confirma y se reentregará.")
    finally:
        dump_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await dump_task


async def run_consumer(settings: ConsumerSettings, stop_event: asyncio.Event,
                       after_db_commit: AfterDbCommit | None = None) -> None:
    """Espera a PostgreSQL y Kafka y consume hasta que se pida parar.

    Qué hace:
        Comprueba la base, abre el pool y el consumidor, y delega en `consume_until_stopped`.
    Recibe:
        settings: configuración; stop_event: se activa con SIGTERM/SIGINT;
        after_db_commit: gancho de prueba (None en producción).
    Devuelve:
        Cuando se pide parar, tras cerrar el consumidor y el pool.
    Por qué existe:
        Ruta Kafka -> PostgreSQL idempotente con reintentos (C2, A4).
    """
    clear_heartbeat(settings.health.heartbeat_file)
    await check_database(settings.database, settings.retry)
    pool = await create_pool_with_retry(settings.database, settings.retry)
    consumer = await start_consumer(settings)
    logger.info("Consumidor suscrito al tema %s.", settings.kafka.topic)
    write_event, write_quarantine = bind_pool_writers(pool)
    control = RetryControl(settings.retry, stop_event)
    deps = PipelineDeps(write_event, write_quarantine, control, after_db_commit=after_db_commit)
    context = LoopContext(consumer, deps, Counters(), settings.health, stop_event, settings.kafka.bootstrap_servers)
    try:
        await consume_until_stopped(context)
    finally:
        await consumer.stop()
        await pool.close()
