"""Pruebas de consumer/loop.py con consumidor y escritores de mentira (T055).

Orden por mensaje: escritura -> gancho -> línea de decisión -> commit del offset -> contadores.
"""
import asyncio
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from aiokafka.errors import CommitFailedError, KafkaConnectionError
from aiokafka.structs import TopicPartition

from common.config import HealthSettings, RetrySettings
from consumer import loop, resilience
from consumer.counters import Counters
from consumer.pipeline import PipelineDeps
from consumer.resilience import RetryControl
from common.records import VersionOutcome
from tests.support.db_helpers import no_country_locator
from tests.support.messages import (
    E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message, to_bytes,
)

TOPIC = "earthquakes.live"
BOOTSTRAP = "kafka:9092"


def kafka_record(offset: int) -> SimpleNamespace:
    value = to_bytes(build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005 + offset, 4.2))
    return SimpleNamespace(topic=TOPIC, partition=0, offset=offset, key=b"k", value=value)


class FakeConsumer:
    """Entrega un mensaje por llamada; al agotarlos pide parar. Anota getmany y commit."""

    def __init__(self, records, stop_event, calls, commit_errors=()):
        self.queue = list(records)
        self.stop_event = stop_event
        self.calls = calls
        self.getmany_args: list[dict] = []
        self.commits: list[dict] = []
        self.commit_errors = list(commit_errors)

    async def getmany(self, **kwargs):
        self.getmany_args.append(kwargs)
        if not self.queue:
            self.stop_event.set()
            return {}
        record = self.queue.pop(0)
        return {TopicPartition(record.topic, record.partition): [record]}

    async def commit(self, offsets):
        self.calls.append("commit")
        self.commits.append(offsets)
        if self.commit_errors:
            raise self.commit_errors.pop(0)

    def assignment(self):
        return {TopicPartition(TOPIC, 0)}

    async def end_offsets(self, partitions):
        return {p: 0 for p in partitions}


class World:
    """Escenario: consumidor, escritores, contadores y registro de llamadas."""

    def __init__(self, tmp_path: Path, records, commit_errors=(), write_errors=()):
        self.calls: list[str] = []
        self.stop_event = asyncio.Event()
        self.heartbeat = tmp_path / "consumer.alive"
        self.write_errors = list(write_errors)
        self.consumer = FakeConsumer(records, self.stop_event, self.calls, commit_errors)
        self.counters = Counters()
        deps = PipelineDeps(self.write_event, self.write_quarantine,
                            RetryControl(RetrySettings(1, 30), self.stop_event),
                            no_country_locator, after_db_commit=self.hook)
        self.context = loop.LoopContext(self.consumer, deps, self.counters, HealthSettings(str(self.heartbeat), 60),
                                        self.stop_event, BOOTSTRAP)

    async def write_event(self, rows, mode):
        self.calls.append("write")
        if self.write_errors:
            raise self.write_errors.pop(0)
        return VersionOutcome.NEW_EVENT

    async def write_quarantine(self, row, mode):
        self.calls.append("write_quarantine")
        return True

    def hook(self, ref, is_synthetic):
        self.calls.append("hook")

    def run(self):
        asyncio.run(loop.consume_until_stopped(self.context))


@pytest.fixture(autouse=True)
def spies(monkeypatch):
    """Anota la línea de decisión y los contadores en el mismo registro que escritura y commit."""
    waits: list[float] = []

    async def fake_wait(stop_event, delay):
        waits.append(delay)
        return stop_event.is_set()

    monkeypatch.setattr(resilience, "wait_or_stop", fake_wait)
    return waits


def instrument(monkeypatch, world: World) -> None:
    real_log, real_apply = loop.log_decision, loop.apply_result

    def log_spy(result):
        world.calls.append("decision")
        real_log(result)

    def apply_spy(counters, result):
        world.calls.append("counters")
        real_apply(counters, result)

    monkeypatch.setattr(loop, "log_decision", log_spy)
    monkeypatch.setattr(loop, "apply_result", apply_spy)


def test_per_message_order_is_write_hook_decision_commit_counters(tmp_path, monkeypatch):
    world = World(tmp_path, [kafka_record(0)])
    instrument(monkeypatch, world)
    world.run()
    assert world.calls == ["write", "hook", "decision", "commit", "counters"]
    assert world.counters.received == 1 and world.counters.new_events == 1


def test_messages_are_requested_one_at_a_time_with_a_one_second_poll(tmp_path):
    world = World(tmp_path, [kafka_record(0)])
    world.run()
    assert world.consumer.getmany_args[0] == {"timeout_ms": 1000, "max_records": 1}


def test_commit_is_offset_plus_one_for_the_topic_partition(tmp_path):
    world = World(tmp_path, [kafka_record(5)])
    world.run()
    assert world.consumer.commits == [{TopicPartition(TOPIC, 0): 6}]


def test_writer_failure_does_not_commit_nor_change_counters(tmp_path, monkeypatch, spies):
    world = World(tmp_path, [kafka_record(0)], write_errors=[OSError("caída")] * 3)
    instrument(monkeypatch, world)
    world.stop_event.set()
    world.run()
    assert "commit" not in world.calls and "decision" not in world.calls
    assert world.counters.received == 0 and world.consumer.commits == []


def test_retry_then_success_commits_after_the_write(tmp_path, monkeypatch, spies):
    world = World(tmp_path, [kafka_record(0)], write_errors=[OSError("caída"), OSError("caída")])
    instrument(monkeypatch, world)
    world.run()
    assert world.calls == ["write", "write", "write", "hook", "decision", "commit", "counters"]
    assert spies == [1, 2]


def test_commit_failed_keeps_the_decision_line_skips_counters_and_continues(tmp_path, monkeypatch, caplog):
    world = World(tmp_path, [kafka_record(0), kafka_record(1)], commit_errors=[CommitFailedError("generación")])
    instrument(monkeypatch, world)
    with caplog.at_level(logging.INFO):
        world.run()
    assert world.calls == ["write", "hook", "decision", "commit",
                           "write", "hook", "decision", "commit", "counters"]
    assert world.counters.received == 1
    decisions = [r.getMessage() for r in caplog.records if r.getMessage().startswith("decision=")]
    assert len(decisions) == 2


def test_stop_during_a_retry_interrupts_without_committing(tmp_path, monkeypatch):
    world = World(tmp_path, [kafka_record(0)], write_errors=[OSError("caída")] * 100)
    instrument(monkeypatch, world)

    async def stop_on_first_wait(stop_event, delay):
        stop_event.set()
        return True

    monkeypatch.setattr(resilience, "wait_or_stop", stop_on_first_wait)
    world.run()
    assert world.calls == ["write"] and world.consumer.commits == []


def test_heartbeat_is_touched_after_a_complete_turn_with_a_reachable_broker(tmp_path):
    world = World(tmp_path, [kafka_record(0)])
    world.run()
    assert world.heartbeat.exists()


def test_heartbeat_is_not_touched_while_a_message_is_in_retry(tmp_path, monkeypatch):
    world = World(tmp_path, [kafka_record(0)], write_errors=[OSError("caída")] * 100)
    seen: list[bool] = []

    async def observe_wait(stop_event, delay):
        seen.append(world.heartbeat.exists())
        stop_event.set()
        return True

    monkeypatch.setattr(resilience, "wait_or_stop", observe_wait)
    world.run()
    assert seen == [False] and not world.heartbeat.exists()


def test_heartbeat_is_not_touched_when_the_broker_is_unreachable(tmp_path):
    world = World(tmp_path, [kafka_record(0)])

    async def fail(partitions):
        raise KafkaConnectionError("sin broker")

    world.consumer.end_offsets = fail
    world.run()
    assert not world.heartbeat.exists()


def test_broker_unreachable_emits_one_warning_line_without_traceback(caplog):
    consumer = SimpleNamespace(assignment=lambda: {"tp"})

    async def fail(partitions):
        raise KafkaConnectionError("sin broker")

    consumer.end_offsets = fail
    with caplog.at_level(logging.WARNING, logger="consumer.loop"):
        assert asyncio.run(loop.broker_reachable(consumer, BOOTSTRAP)) is False
    (record,) = caplog.records
    assert record.getMessage() == "broker_unreachable bootstrap=kafka:9092 error=KafkaConnectionError"
    assert record.levelno == logging.WARNING and record.exc_info is None


def test_a_single_final_counters_line_comes_from_the_periodic_task_after_the_last_commit(tmp_path, caplog):
    world = World(tmp_path, [kafka_record(0), kafka_record(1)])
    with caplog.at_level(logging.INFO):
        world.run()
    lines = [r for r in caplog.records if r.getMessage().startswith("COUNTERS")]
    assert len(lines) == 1 and lines[0].name == "consumer.reporting"
    assert json.loads(lines[0].getMessage().removeprefix("COUNTERS "))["received"] == 2


def test_start_consumer_uses_manual_commit_and_a_long_poll_interval(monkeypatch):
    captured = {}

    class FakeAIOKafka:
        def __init__(self, *topics, **kwargs):
            captured["topics"] = topics
            captured.update(kwargs)

        async def start(self):
            return None

    async def no_topics(bootstrap):
        return None

    monkeypatch.setattr(loop, "AIOKafkaConsumer", FakeAIOKafka)
    monkeypatch.setattr(loop, "ensure_topics", no_topics)
    settings = loop.ConsumerSettings(
        kafka=SimpleNamespace(bootstrap_servers=BOOTSTRAP, topic=TOPIC), database=None,
        retry=RetrySettings(1, 30), health=None, group_id="consumer-live",
        country_catalog_path="catalogo.geojson",
        topics=("earthquakes.live", "earthquakes.replay"))
    asyncio.run(loop.start_consumer(settings))
    assert captured["topics"] == ("earthquakes.live", "earthquakes.replay")
    assert captured["enable_auto_commit"] is False and captured["group_id"] == "consumer-live"
    assert captured["auto_offset_reset"] == "earliest"
    assert captured["max_poll_interval_ms"] == loop.MAX_POLL_INTERVAL_MS == 86_400_000


class StartupSpy:
    """Dobles del arranque: anotan el orden y pueden fallar en un paso."""

    def __init__(self, monkeypatch, fail_at=None):
        self.calls: list[str] = []
        self.fail_at = fail_at
        self.pool = SimpleNamespace(close=self.close)
        monkeypatch.setattr(loop, "check_database", self.step("check_database"))
        monkeypatch.setattr(loop, "create_pool_with_retry", self.step("pool", self.pool))
        monkeypatch.setattr(loop, "ensure_schema_ready", self.step("ensure_schema_ready"))
        monkeypatch.setattr(loop, "load_country_catalog", self.step("load_catalog", (None, None)))
        monkeypatch.setattr(loop, "start_consumer", self.step("start_consumer", SimpleNamespace(stop=self.stop)))
        monkeypatch.setattr(loop, "assign_country", lambda index, lon, lat: None)

        async def no_consume(context):
            self.calls.append("consume")

        monkeypatch.setattr(loop, "consume_until_stopped", no_consume)

    def step(self, name, result=None):
        async def run(*args, **kwargs):
            self.calls.append(name)
            if self.fail_at == name:
                raise RuntimeError(name)
            return result
        return run

    async def close(self):
        self.calls.append("pool_close")

    async def stop(self):
        self.calls.append("consumer_stop")


def run_consumer_with(monkeypatch, tmp_path, fail_at=None):
    spy = StartupSpy(monkeypatch, fail_at)
    settings = loop.ConsumerSettings(
        kafka=SimpleNamespace(bootstrap_servers=BOOTSTRAP, topic=TOPIC), database=None,
        retry=RetrySettings(1, 30), health=HealthSettings(str(tmp_path / "alive"), 60),
        group_id="g", country_catalog_path="catalogo.geojson", topics=(TOPIC,))
    return spy, lambda: asyncio.run(loop.run_consumer(settings, asyncio.Event()))


def test_startup_order_loads_the_catalog_before_creating_the_consumer(tmp_path, monkeypatch):
    spy, run = run_consumer_with(monkeypatch, tmp_path)
    run()
    assert spy.calls == ["check_database", "pool", "ensure_schema_ready", "load_catalog",
                         "start_consumer", "consume", "consumer_stop", "pool_close"]


@pytest.mark.parametrize("failing", ["ensure_schema_ready", "load_catalog"])
def test_nothing_is_consumed_if_schema_check_or_catalog_load_fails(tmp_path, monkeypatch, failing):
    spy, run = run_consumer_with(monkeypatch, tmp_path, fail_at=failing)
    with pytest.raises(RuntimeError):
        run()
    assert "start_consumer" not in spy.calls and "consume" not in spy.calls
    assert spy.calls[-1] == "pool_close"
