"""Bucle del consumidor mínimo: lee del tema y deja cada evento en el registro."""
import asyncio
import json
import logging
import time
from dataclasses import dataclass

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from common.config import DatabaseSettings, HealthSettings, KafkaSettings, RetrySettings
from common.db import check_database
from common.health import clear_heartbeat, touch_heartbeat
from common.kafka_topics import ensure_topics
from common.retry import retry_forever

logger = logging.getLogger(__name__)

POLL_TIMEOUT_MS = 1000
# Cada cuántos segundos se comprueba que el broker responde, y cuánto se espera la respuesta.
HEALTH_PROBE_INTERVAL_SECONDS = 10
HEALTH_PROBE_TIMEOUT_SECONDS = 5
RETRIABLE_KAFKA_ERRORS = (KafkaError, OSError)


@dataclass(frozen=True)
class ConsumerSettings:
    """Configuración completa del consumidor mínimo."""

    kafka: KafkaSettings
    database: DatabaseSettings
    retry: RetrySettings
    health: HealthSettings
    group_id: str


def describe_message(key: bytes | None, value: bytes) -> str:
    """Resume un mensaje recibido en una línea de registro.

    Qué hace:
        Interpreta el JSON y señala si el evento es sintético; si no es JSON, lo indica.
    Recibe:
        key: clave del mensaje; value: valor en bytes.
    Devuelve:
        Línea de texto para el registro.
    Por qué existe:
        El criterio de aceptación es ver en el log el evento sintético del productor (A1).
    """
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return f"Mensaje que no es JSON válido: clave={key!r}"
    tag = "SINTÉTICO" if payload.get("is_synthetic") is True else "REAL"
    event_id = payload.get("event", {}).get("id")
    return f"Evento recibido [{tag}] clave={key.decode() if key else None} event_id={event_id} source={payload.get('source')}"


async def start_consumer(settings: ConsumerSettings) -> AIOKafkaConsumer:
    """Arranca el consumidor reintentando hasta que el broker y el tema existan."""
    async def attempt() -> AIOKafkaConsumer:
        await ensure_topics(settings.kafka.bootstrap_servers)
        consumer = AIOKafkaConsumer(
            settings.kafka.topic,
            bootstrap_servers=settings.kafka.bootstrap_servers,
            group_id=settings.group_id,
            auto_offset_reset="earliest",
            # Sin escritura en PostgreSQL no hay nada que confirmar: el offset se confirmará
            # después del commit en la feature del consumidor idempotente (constitución §1).
            enable_auto_commit=False,
        )
        try:
            await consumer.start()
        except BaseException:
            await consumer.stop()
            raise
        return consumer

    return await retry_forever(attempt, f"Kafka ({settings.kafka.bootstrap_servers})", settings.retry,
                               RETRIABLE_KAFKA_ERRORS)


async def broker_reachable(consumer: AIOKafkaConsumer) -> bool:
    """Comprueba que el consumidor puede hablar con el broker.

    Qué hace:
        Pide al broker el último offset de las particiones asignadas, con un tiempo máximo de espera.
    Recibe:
        consumer: consumidor ya suscrito.
    Devuelve:
        True si el broker respondió a tiempo; False si no hay particiones asignadas o falló la consulta.
    Por qué existe:
        `getmany` devuelve vacío con el broker caído, así que sin esta comprobación el latido seguiría
        renovándose y el consumidor nunca pasaría a unhealthy (A4, T014).
    """
    partitions = consumer.assignment()
    if not partitions:
        return False
    try:
        await asyncio.wait_for(consumer.end_offsets(list(partitions)), HEALTH_PROBE_TIMEOUT_SECONDS)
    except (KafkaError, OSError, asyncio.TimeoutError):
        return False
    return True


async def run_consumer(settings: ConsumerSettings) -> None:
    """Espera a PostgreSQL y Kafka y registra los mensajes que llegan.

    Qué hace:
        Consulta el tema cada segundo, registra cada mensaje y renueva el latido solo mientras el broker responde
        (se comprueba cada HEALTH_PROBE_INTERVAL_SECONDS).
    Recibe:
        settings: configuración del consumidor.
    Devuelve:
        Nunca termina por sí mismo.
    Por qué existe:
        Prueba de punta a punta de la ruta Kafka → consumidor (A1) con reintentos (A4).
    """
    # Supera ~30 líneas por el docstring de la plantilla (§7.4); el cuerpo son 19 líneas: arrancar y consumir en un bucle.
    clear_heartbeat(settings.health.heartbeat_file)
    await check_database(settings.database, settings.retry)
    consumer = await start_consumer(settings)
    logger.info("Consumidor suscrito al tema %s.", settings.kafka.topic)
    try:
        reachable = False
        last_probe = 0.0
        while True:
            batches = await consumer.getmany(timeout_ms=POLL_TIMEOUT_MS)
            for records in batches.values():
                for record in records:
                    logger.info(describe_message(record.key, record.value))
            if time.monotonic() - last_probe >= HEALTH_PROBE_INTERVAL_SECONDS:
                reachable = await broker_reachable(consumer)
                last_probe = time.monotonic()
            if reachable:
                touch_heartbeat(settings.health.heartbeat_file)
    finally:
        await consumer.stop()
