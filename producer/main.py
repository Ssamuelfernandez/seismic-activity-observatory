"""Punto de entrada del productor en vivo: solo configura y arranca."""
import asyncio

from common.config import (
    load_database_settings, load_feed_settings, load_health_settings, load_kafka_settings,
    load_log_level, load_retry_settings, validate_poll_against_health,
)
from common.logging_setup import configure_logging
from producer.loop import ProducerSettings, run_producer


def build_settings() -> ProducerSettings:
    """Carga la configuración completa y comprueba que `POLL_SECONDS` deje renovar el latido (A10)."""
    health = load_health_settings()
    feed = load_feed_settings()
    validate_poll_against_health(feed.poll_seconds, health.max_age_seconds)
    return ProducerSettings(
        kafka=load_kafka_settings(),
        database=load_database_settings(),
        retry=load_retry_settings(),
        health=health,
        feed=feed,
    )


def main() -> None:
    """Configura el registro, carga la configuración y arranca el bucle del productor."""
    configure_logging(load_log_level())
    asyncio.run(run_producer(build_settings()))


if __name__ == "__main__":
    main()
