"""Punto de entrada del productor mínimo: solo configura y arranca."""
import asyncio

from common.config import (
    load_database_settings, load_health_settings, load_kafka_settings, load_log_level,
    load_retry_settings,
)
from common.logging_setup import configure_logging
from producer.loop import ProducerSettings, read_interval_seconds, run_producer, validate_interval_against_health


def main() -> None:
    """Carga la configuración y arranca el bucle del productor."""
    configure_logging(load_log_level())
    health = load_health_settings()
    interval = read_interval_seconds()
    validate_interval_against_health(interval, health)
    settings = ProducerSettings(
        kafka=load_kafka_settings(),
        database=load_database_settings(),
        retry=load_retry_settings(),
        health=health,
        interval_seconds=interval,
    )
    asyncio.run(run_producer(settings))


if __name__ == "__main__":
    main()
