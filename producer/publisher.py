"""Envío de mensajes a Kafka y espera de confirmación."""
import json
import logging

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from common.config import KafkaSettings, RetrySettings
from common.retry import retry_forever

logger = logging.getLogger(__name__)

# KafkaError cubre las caídas del broker; OSError, los fallos de red al conectar.
RETRIABLE_KAFKA_ERRORS = (KafkaError, OSError)


async def start_producer(settings: KafkaSettings, retry: RetrySettings) -> AIOKafkaProducer:
    """Arranca el productor de Kafka reintentando hasta que el broker esté listo.

    Qué hace:
        Crea el cliente con confirmación de todas las réplicas e idempotencia y lo conecta.
    Recibe:
        settings: broker y tema; retry: política de reintentos.
    Devuelve:
        El productor conectado.
    Por qué existe:
        Productor mínimo con las garantías que usará el productor real (A4, B-series).
    """
    async def attempt() -> AIOKafkaProducer:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.bootstrap_servers,
            acks="all",
            enable_idempotence=True,
        )
        try:
            await producer.start()
        except BaseException:
            await producer.stop()
            raise
        return producer

    return await retry_forever(attempt, f"Kafka ({settings.bootstrap_servers})", retry,
                               RETRIABLE_KAFKA_ERRORS)


async def publish_message(producer: AIOKafkaProducer, topic: str, key: str, message: dict) -> None:
    """Publica un mensaje JSON y espera la confirmación del broker.

    Qué hace:
        Serializa el mensaje en UTF-8 y lo envía con `send_and_wait`.
    Recibe:
        producer: productor conectado; topic: tema; key: clave (`event.id`); message: valor.
    Devuelve:
        Nada.
    Por qué existe:
        La publicación solo cuenta cuando el broker la confirma (kafka-message.md §2).
    """
    value = json.dumps(message, ensure_ascii=False).encode("utf-8")
    await producer.send_and_wait(topic, value=value, key=key.encode("utf-8"))
    logger.info("Publicado en %s: clave=%s", topic, key)
