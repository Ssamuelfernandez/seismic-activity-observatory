"""Arnés de las pruebas de integración del bucle: Kafka simulado, PostgreSQL real (T059, T060).

Ejecuta el `consume_until_stopped` real con `process_record` y el escritor reales contra la base
temporal; solo el consumidor de Kafka es de mentira. Pensado para `asyncio.run` (sin pytest-asyncio).
"""
import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import asyncpg
from aiokafka.structs import TopicPartition

from common.config import HealthSettings, RetrySettings
from common.kafka_topics import TOPIC_LIVE
from common.records import MessageRef
from consumer.counters import Counters
from consumer.loop import LoopContext, consume_until_stopped
from consumer.pipeline import PipelineDeps, bind_pool_writers
from consumer.resilience import RetryControl
from tests.support.db_helpers import no_country_locator
from tests.support.temp_database import TempDatabase

FIXED_NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
HEARTBEAT_FILE = Path(tempfile.gettempdir()) / "loop_harness.alive"
BOOTSTRAP = "kafka:9092"
POOL_MAX_SIZE = 2
RETRY = RetrySettings(initial_seconds=1, max_seconds=30)


class SimulatedCrash(BaseException):
    """Corte del proceso tras el commit de PostgreSQL; hereda de `BaseException` para que ningún `except` lo absorba."""


class ReplayConsumer:
    """Consumidor de Kafka de mentira: entrega de uno en uno desde `start` y recuerda el último commit."""

    def __init__(self, raws: list[bytes | None], start: int, stop_event: asyncio.Event):
        self.raws = raws
        self.next_offset = start
        self.committed = start
        self.stop_event = stop_event

    async def getmany(self, **kwargs) -> dict:
        if self.next_offset >= len(self.raws):
            self.stop_event.set()
            return {}
        offset = self.next_offset
        self.next_offset += 1
        record = SimpleNamespace(topic=TOPIC_LIVE, partition=0, offset=offset, key=None, value=self.raws[offset])
        return {TopicPartition(TOPIC_LIVE, 0): [record]}

    async def commit(self, offsets: dict) -> None:
        self.committed = max(offsets.values())

    def assignment(self) -> set:
        return {TopicPartition(TOPIC_LIVE, 0)}

    async def end_offsets(self, partitions) -> dict:
        return {p: len(self.raws) for p in partitions}


def crash_after_commit_at(offset: int):
    """Gancho `after_db_commit` que lanza `SimulatedCrash` al llegar al offset indicado."""
    def hook(ref: MessageRef, is_synthetic: bool) -> None:
        if ref.offset == offset:
            raise SimulatedCrash(f"corte tras el commit de PostgreSQL en el offset {offset}")
    return hook


async def open_pool(db: TempDatabase) -> asyncpg.Pool:
    """Pool con el rol real `observatory_consumer` sobre la base temporal."""
    return await asyncpg.create_pool(host=db.host, port=db.port, database=db.name, user=db.consumer_user,
                                     password=db.consumer_password, min_size=1, max_size=POOL_MAX_SIZE)


async def run_session(pool: asyncpg.Pool, consumer: ReplayConsumer, counters: Counters, hook=None,
                      locate=no_country_locator) -> None:
    """Ejecuta el bucle real hasta que el consumidor simulado se queda sin mensajes (o el gancho corta)."""
    write_event, write_quarantine = bind_pool_writers(pool)
    control = RetryControl(RETRY, consumer.stop_event)
    deps = PipelineDeps(write_event, write_quarantine, control, locate, clock=lambda: FIXED_NOW, after_db_commit=hook)
    health = HealthSettings(str(HEARTBEAT_FILE), 60)
    context = LoopContext(consumer, deps, counters, health, consumer.stop_event, BOOTSTRAP)
    await consume_until_stopped(context)
