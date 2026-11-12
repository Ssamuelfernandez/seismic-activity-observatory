"""Punto de entrada del consumidor idempotente: solo configura y arranca."""
import asyncio
import signal

from common.config import (
    load_consumer_topics, load_database_settings, load_health_settings, load_kafka_settings,
    load_log_level, load_retry_settings, read_optional_int, read_str,
)
from common.logging_setup import configure_logging
from consumer.fault_hook import AfterDbCommit, build_fault_hook
from consumer.loop import ConsumerSettings, run_consumer

STOP_SIGNALS = (signal.SIGTERM, signal.SIGINT)
FAULT_OFFSET_VARIABLE = "CONSUMER_FAULT_CRASH_AT_OFFSET"


def build_settings() -> ConsumerSettings:
    """Carga la configuración del entorno; `DB_USER` es el rol `observatory_consumer` (FR-027)."""
    return ConsumerSettings(
        kafka=load_kafka_settings(),
        database=load_database_settings(),
        retry=load_retry_settings(),
        health=load_health_settings(),
        group_id=read_str("KAFKA_GROUP_ID"),
        country_catalog_path=read_str("COUNTRY_CATALOG_PATH"),
        topics=load_consumer_topics(),
    )


async def run(settings: ConsumerSettings, after_db_commit: AfterDbCommit | None) -> None:
    """Instala el manejador de SIGTERM/SIGINT que activa `stop_event` y arranca el bucle."""
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in STOP_SIGNALS:
        loop.add_signal_handler(stop_signal, stop_event.set)
    await run_consumer(settings, stop_event, after_db_commit)


def main() -> None:
    """Configura el registro, construye el gancho de prueba (None si la variable está vacía) y arranca."""
    configure_logging(load_log_level())
    after_db_commit = build_fault_hook(read_optional_int(FAULT_OFFSET_VARIABLE))
    asyncio.run(run(build_settings(), after_db_commit))


if __name__ == "__main__":
    main()
