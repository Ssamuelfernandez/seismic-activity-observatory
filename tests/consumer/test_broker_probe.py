"""Pruebas de consumer/loop.py: el latido depende de que el broker responda (A4)."""
import asyncio

from aiokafka.errors import KafkaConnectionError

from consumer.loop import broker_reachable

BOOTSTRAP = "kafka:9092"


class FakeConsumer:
    """Consumidor simulado con particiones asignadas y una consulta de offsets configurable."""

    def __init__(self, partitions, end_offsets):
        self._partitions = partitions
        self._end_offsets = end_offsets

    def assignment(self):
        return self._partitions

    async def end_offsets(self, partitions):
        return await self._end_offsets(partitions)


def test_broker_reachable_when_end_offsets_answers():
    async def answer(partitions):
        return {p: 10 for p in partitions}

    assert asyncio.run(broker_reachable(FakeConsumer({"tp"}, answer), BOOTSTRAP))


def test_broker_not_reachable_without_assigned_partitions():
    async def answer(partitions):
        return {}

    assert not asyncio.run(broker_reachable(FakeConsumer(set(), answer), BOOTSTRAP))


def test_broker_not_reachable_when_connection_fails():
    async def fail(partitions):
        raise KafkaConnectionError("sin broker")

    assert not asyncio.run(broker_reachable(FakeConsumer({"tp"}, fail), BOOTSTRAP))


def test_broker_not_reachable_when_it_does_not_answer_in_time(monkeypatch):
    import consumer.loop as loop

    monkeypatch.setattr(loop, "HEALTH_PROBE_TIMEOUT_SECONDS", 0.05)

    async def hang(partitions):
        await asyncio.sleep(5)

    assert not asyncio.run(loop.broker_reachable(FakeConsumer({"tp"}, hang), BOOTSTRAP))
