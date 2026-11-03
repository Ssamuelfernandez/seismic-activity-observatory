"""Bucle del productor mínimo: un evento sintético cada intervalo configurado."""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from common.config import (
    MAX_PRODUCER_INTERVAL_SECONDS, MIN_PRODUCER_INTERVAL_SECONDS, DatabaseSettings,
    HealthSettings, KafkaSettings, RetrySettings, read_int,
)
from common.db import check_database
from common.health import clear_heartbeat, touch_heartbeat
from common.kafka_topics import ensure_topics
from common.retry import retry_forever
from common.synthetic_event import build_synthetic_event_id, build_synthetic_message
from producer.publisher import RETRIABLE_KAFKA_ERRORS, publish_message, start_producer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProducerSettings:
    """Configuración completa del productor mínimo."""

    kafka: KafkaSettings
    database: DatabaseSettings
    retry: RetrySettings
    health: HealthSettings
    interval_seconds: int


def read_interval_seconds() -> int:
    """Lee el intervalo entre eventos sintéticos (A10, FR-012)."""
    return read_int("PRODUCER_INTERVAL_SECONDS", minimum=MIN_PRODUCER_INTERVAL_SECONDS,
                    maximum=MAX_PRODUCER_INTERVAL_SECONDS)


def validate_interval_against_health(interval_seconds: int, health: HealthSettings) -> None:
    """Exige que el latido pueda renovarse antes de caducar.

    Por qué existe:
        Si el intervalo fuera mayor que la antigüedad máxima, el productor sano se vería no sano.
    """
    if interval_seconds * 2 > health.max_age_seconds:
        raise ValueError("PRODUCER_INTERVAL_SECONDS debe ser como mucho la mitad de HEALTH_MAX_AGE_SECONDS.")


async def publish_one_event(producer, settings: ProducerSettings) -> None:
    """Publica un evento sintético, reintentando si el broker falla."""
    now = datetime.now(timezone.utc)
    event_id = build_synthetic_event_id(now)
    message = build_synthetic_message(event_id, now)
    await retry_forever(
        lambda: publish_message(producer, settings.kafka.topic, event_id, message),
        f"Kafka ({settings.kafka.bootstrap_servers})", settings.retry, RETRIABLE_KAFKA_ERRORS,
    )


async def run_producer(settings: ProducerSettings) -> None:
    """Arranca las conexiones y publica eventos sintéticos mientras el proceso viva.

    Qué hace:
        Espera a PostgreSQL y a Kafka, asegura los temas y entra en el bucle de publicación.
    Recibe:
        settings: configuración del productor.
    Devuelve:
        Nunca termina por sí mismo.
    Por qué existe:
        Prueba de punta a punta de la ruta productor → Kafka (A1) con reintentos (A4).
    """
    clear_heartbeat(settings.health.heartbeat_file)
    await check_database(settings.database, settings.retry)
    producer = await start_producer(settings.kafka, settings.retry)
    try:
        await retry_forever(lambda: ensure_topics(settings.kafka.bootstrap_servers),
                            "Kafka (creación de temas)", settings.retry, RETRIABLE_KAFKA_ERRORS)
        while True:
            await publish_one_event(producer, settings)
            touch_heartbeat(settings.health.heartbeat_file)
            await asyncio.sleep(settings.interval_seconds)
    finally:
        await producer.stop()
