"""Publicación del replay en Kafka: un mensaje cada `interval` segundos, solo en `earthquakes.replay` (J1, J3)."""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from common.config import KafkaSettings, RetrySettings
from common.kafka_topics import TOPIC_REPLAY, ensure_topics
from common.live_message import message_key
from common.replay_message import ReplayItem, build_replay_message
from common.retry import retry_forever
from producer.publisher import RETRIABLE_KAFKA_ERRORS, publish_message, start_producer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReplaySummary:
    """Resultado de un replay: eventos reales, del bloque controlado y total publicados."""

    real: int
    block: int
    total: int


def _utc_now() -> datetime:
    """Reloj real en UTC."""
    return datetime.now(timezone.utc)


async def _publish_item(producer, item: ReplayItem, retry: RetrySettings, clock: Callable[[], datetime],
                        publish: Callable[..., Awaitable[None]]) -> None:
    """Publica un elemento; ante un fallo de Kafka reintenta leyendo el reloj en cada intento."""
    key = message_key(item.feature)

    async def attempt() -> None:
        message = build_replay_message(item, clock())
        await publish(producer, TOPIC_REPLAY, key, message)

    await retry_forever(attempt, f"Kafka (publicar {key})", retry, RETRIABLE_KAFKA_ERRORS)


async def run_replay(
    items: list[ReplayItem],
    interval: float,
    settings: KafkaSettings,
    retry: RetrySettings,
    *,
    clock: Callable[[], datetime] = _utc_now,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ensure: Callable[[str], Awaitable[None]] = ensure_topics,
    start: Callable[[KafkaSettings, RetrySettings], Awaitable] = start_producer,
    publish: Callable[..., Awaitable[None]] = publish_message,
) -> ReplaySummary:
    """Publica los elementos en orden, solo en el topic de replay.

    Qué hace:
        Crea los topics, arranca el productor, envía cada elemento con su `replay_at` (reloj leído
        justo antes del envío), espera `interval` entre mensajes (no tras el último) y cierra.
    Recibe:
        items: elementos en orden; interval: segundos entre mensajes; settings: broker;
        retry: política de reintentos; el resto son dobles inyectables para las pruebas.
    Devuelve:
        `ReplaySummary` con reales, bloque y total publicados.
    Por qué existe:
        Es la parte con E/S del replay; nunca escribe en `earthquakes.live` (FR-004, FR-005, FR-007).
    """
    await retry_forever(lambda: ensure(settings.bootstrap_servers), "Kafka (creación de temas)",
                        retry, RETRIABLE_KAFKA_ERRORS)
    producer = await start(settings, retry)
    real = block = 0
    try:
        for index, item in enumerate(items):
            await _publish_item(producer, item, retry, clock, publish)
            if item.is_synthetic:
                block += 1
            else:
                real += 1
            if index < len(items) - 1:
                await sleep(interval)
    finally:
        await producer.stop()
    logger.info("Replay terminado: %d reales y %d del bloque controlado", real, block)
    return ReplaySummary(real=real, block=block, total=real + block)
