"""Pruebas del publicador del replay (T044). Sin Docker, con dobles de Kafka y de reloj."""
import asyncio
from datetime import datetime, timedelta, timezone

from aiokafka.errors import KafkaConnectionError

from common.config import KafkaSettings, RetrySettings
from common.kafka_topics import TOPIC_LIVE, TOPIC_REPLAY
from common.replay_message import ReplayItem, build_controlled_block
from producer.replay_runner import run_replay

SETTINGS = KafkaSettings(bootstrap_servers="kafka:9092", topic=TOPIC_REPLAY)
RETRY = RetrySettings(initial_seconds=0.0, max_seconds=0.0)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_items() -> list[ReplayItem]:
    """20 eventos reales de prueba (SINTÉTICOS) y el bloque controlado: 26 elementos."""
    real = [ReplayItem({"id": f"fake-{n}", "properties": {}}, False, START) for n in range(20)]
    return real + build_controlled_block(START)


class Harness:
    """Dobles de Kafka, reloj y espera que registran el orden de los acontecimientos."""

    def __init__(self, failures: int = 0):
        self.log: list[tuple] = []
        self.sent: list[tuple[str, str | None, dict]] = []
        self.sleeps: list[float] = []
        self.stopped = False
        self.failures = failures
        self.ticks = 0

    def clock(self) -> datetime:
        self.ticks += 1
        return START + timedelta(seconds=self.ticks)

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.log.append(("sleep",))

    async def ensure(self, bootstrap: str) -> None:
        self.log.append(("ensure", bootstrap))

    async def start(self, settings, retry):
        harness = self

        class Producer:
            async def stop(self):
                harness.stopped = True

        return Producer()

    async def publish(self, producer, topic, key, message) -> None:
        self.log.append(("begin", key))
        await asyncio.sleep(0)
        if self.failures:
            self.failures -= 1
            raise KafkaConnectionError("simulado")
        self.sent.append((topic, key, message))
        self.log.append(("end", key))

    def run(self, items, interval=2.0):
        return asyncio.run(run_replay(
            items, interval, SETTINGS, RETRY, clock=self.clock, sleep=self.sleep,
            ensure=self.ensure, start=self.start, publish=self.publish))


def test_publishes_26_only_in_replay_topic():
    harness = Harness()
    summary = harness.run(make_items())
    assert len(harness.sent) == 26
    assert {topic for topic, _, _ in harness.sent} == {TOPIC_REPLAY}
    assert TOPIC_LIVE not in {topic for topic, _, _ in harness.sent}
    assert (summary.real, summary.block, summary.total) == (20, 6, 26)
    assert harness.stopped
    assert harness.sent[0][1] == "fake-0"
    assert harness.sent[0][2]["mode"] == "replay"


def test_replay_at_strictly_increasing():
    harness = Harness()
    harness.run(make_items())
    instants = [message["replay_at"] for _, _, message in harness.sent]
    assert instants == sorted(set(instants))


def test_next_not_sent_before_previous_finishes():
    harness = Harness()
    harness.run(make_items())
    sends = [entry for entry in harness.log if entry[0] in ("begin", "end")]
    assert [entry[0] for entry in sends] == ["begin", "end"] * 26


def test_waits_between_messages_but_not_after_last():
    harness = Harness()
    harness.run(make_items(), interval=2.0)
    assert harness.sleeps == [2.0] * 25
    assert harness.log[-1][0] == "end"


def test_kafka_failure_is_retried_and_message_still_sent_once():
    harness = Harness(failures=2)
    harness.run(make_items()[:3])
    assert len(harness.sent) == 3
    assert len([entry for entry in harness.log if entry[0] == "begin"]) == 5
