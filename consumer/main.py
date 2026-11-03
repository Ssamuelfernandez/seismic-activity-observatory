"""Punto de entrada del consumidor mínimo: solo configura y arranca."""
import asyncio

from common.config import (
    load_database_settings, load_health_settings, load_kafka_settings, load_log_level,
    load_retry_settings, read_str,
)
from common.logging_setup import configure_logging
from consumer.loop import ConsumerSettings, run_consumer


def main() -> None:
    """Carga la configuración y arranca el bucle del consumidor."""
    configure_logging(load_log_level())
    settings = ConsumerSettings(
        kafka=load_kafka_settings(),
        database=load_database_settings(),
        retry=load_retry_settings(),
        health=load_health_settings(),
        group_id=read_str("KAFKA_GROUP_ID"),
    )
    asyncio.run(run_consumer(settings))


if __name__ == "__main__":
    main()
