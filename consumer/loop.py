"""Bucle del consumidor mínimo: lee del tema y deja cada evento en el registro."""
import json
import logging
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


async def run_consumer(settings: ConsumerSettings) -> None:
    """Espera a PostgreSQL y Kafka y registra los mensajes que llegan.

    Qué hace:
        Consulta el tema cada segundo, registra cada mensaje y renueva el latido en cada vuelta.
    Recibe:
        settings: configuración del consumidor.
    Devuelve:
        Nunca termina por sí mismo.
    Por qué existe:
        Prueba de punta a punta de la ruta Kafka → consumidor (A1) con reintentos (A4).
    """
    clear_heartbeat(settings.health.heartbeat_file)
    await check_database(settings.database, settings.retry)
    consumer = await start_consumer(settings)
    logger.info("Consumidor suscrito al tema %s.", settings.kafka.topic)
    try:
        while True:
            batches = await consumer.getmany(timeout_ms=POLL_TIMEOUT_MS)
            for records in batches.values():
                for record in records:
                    logger.info(describe_message(record.key, record.value))
            touch_heartbeat(settings.health.heartbeat_file)
    finally:
        await consumer.stop()
