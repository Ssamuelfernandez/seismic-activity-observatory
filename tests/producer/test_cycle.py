"""Pruebas del ciclo con dobles (cliente, almacén y publicador falsos, reloj fijo). Datos sintéticos."""
import asyncio
import json
from datetime import datetime, timezone

from aiokafka.errors import KafkaConnectionError

from common.config import FeedSettings
from producer.cycle import (
    CycleDeps, STATUS_FETCH_ERROR, STATUS_KAFKA_ERROR, STATUS_OK, run_cycle,
)
from producer.usgs_client import FeedFetchError, FeedResponse
from tests.support.mock_usgs import synthetic_feature

NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
SETTINGS = FeedSettings(url="http://mock.invalid/feed", poll_seconds=60, timeout_seconds=10, raw_retention_days=7)


def _response(features: list[dict]) -> FeedResponse:
    body = json.dumps({"features": features}).encode("utf-8")
    return FeedResponse(200, body, 20, NOW)


class FakeStore:
    """Almacén en memoria que anota el orden de las llamadas en un registro compartido."""

    def __init__(self, log: list, state: dict[str, int] | None = None) -> None:
        self.log = log
        self.state = dict(state or {})
        self.failures: list[tuple] = []
        self.exclusions: list[dict] = []
        self.successes = 0

    async def record_success(self, url, response, event_count, sha256):
        self.successes += 1
        return True

    async def record_failure(self, url, run_at, status, latency_ms, error):
        self.failures.append((status, error))

    async def insert_exclusions(self, rows):
        self.exclusions.extend(rows)

    async def load_state(self, event_ids):
        return {i: self.state[i] for i in event_ids if i in self.state}

    async def mark_published(self, event_id, updated_ms, published_at):
        self.log.append(("mark", event_id))
        self.state[event_id] = updated_ms

    async def purge_raw_responses(self, retention_days):
        self.log.append(("purge", retention_days))
        return 0


class FakePublisher:
    """Publicador que anota (clave, mensaje) y puede fallar en el envío número `fail_at`."""

    def __init__(self, log: list, fail_at: int | None = None) -> None:
        self.log = log
        self.fail_at = fail_at
        self.sent: list[tuple] = []

    async def __call__(self, key, message):
        if self.fail_at is not None and len(self.sent) + 1 == self.fail_at:
            raise KafkaConnectionError("simulado")
        self.sent.append((key, message))
        self.log.append(("ack", key))


def _run(features=None, state=None, fail_at=None, fetch=None):
    log: list = []
    store = FakeStore(log, state)
    publisher = FakePublisher(log, fail_at)

    async def default_fetch(url, timeout):
        return _response(features or [])

    deps = CycleDeps(fetch=fetch or default_fetch, store=store, publish=publisher, now=lambda: NOW)
    result = asyncio.run(run_cycle(deps, SETTINGS))
    return result, store, publisher, log


def test_mark_never_precedes_ack():
    result, _, publisher, log = _run([synthetic_feature(1), synthetic_feature(2)])
    assert result.status == STATUS_OK and result.published == 2
    assert [entry[0] for entry in log] == ["ack", "mark", "ack", "mark", "purge"]
    assert log[0][1] == log[1][1] == "synthetic-1"


def test_kafka_failure_on_second_event_keeps_first_marked_only():
    result, store, publisher, _ = _run([synthetic_feature(1), synthetic_feature(2)], fail_at=2)
    assert result.status == STATUS_KAFKA_ERROR and result.published == 1
    assert set(store.state) == {"synthetic-1"}
    assert len(publisher.sent) == 1


def test_message_key_is_event_id_and_ingested_at_is_shared():
    _, _, publisher, _ = _run([synthetic_feature(1), synthetic_feature(2)])
    assert [key for key, _ in publisher.sent] == ["synthetic-1", "synthetic-2"]
    assert {message["ingested_at"] for _, message in publisher.sent} == {"2026-11-05T09:00:00Z"}
    assert all(message["source"] == "usgs_feed" and message["is_synthetic"] is False
               for _, message in publisher.sent)


def test_non_earthquakes_go_to_exclusions_not_to_publisher():
    features = [synthetic_feature(1), synthetic_feature(2, event_type="quarry blast")]
    result, store, publisher, _ = _run(features)
    assert result.excluded == 1 and result.published == 1
    assert [row["event_id"] for row in store.exclusions] == ["synthetic-2"]
    assert [key for key, _ in publisher.sent] == ["synthetic-1"]


def test_already_published_is_skipped():
    result, _, publisher, _ = _run([synthetic_feature(1, updated=1_000), synthetic_feature(2, updated=2_000)],
                                   state={"synthetic-1": 1_000, "synthetic-2": 1_500})
    assert result.skipped == 1 and result.published == 1
    assert [key for key, _ in publisher.sent] == ["synthetic-2"]


def test_event_without_id_is_published_without_key_or_mark():
    feature = synthetic_feature(1)
    del feature["id"]
    result, store, publisher, _ = _run([feature])
    assert result.unmarked == 1 and result.published == 1
    assert publisher.sent[0][0] is None and store.state == {}


def test_fetch_error_records_failure_and_publishes_nothing():
    async def failing(url, timeout):
        raise FeedFetchError(429, "HTTP 429", 15)

    result, store, publisher, _ = _run(fetch=failing)
    assert result.status == STATUS_FETCH_ERROR and result.http == 429
    assert store.failures == [(429, "HTTP 429")] and store.successes == 0 and publisher.sent == []


def test_invalid_body_records_failure_with_status_200():
    async def broken(url, timeout):
        return FeedResponse(200, b"<html>", 20, NOW)

    result, store, publisher, _ = _run(fetch=broken)
    assert result.status == STATUS_FETCH_ERROR
    assert store.failures[0][0] == 200 and store.failures[0][1].startswith("invalid_body: ")
    assert store.successes == 0 and publisher.sent == []
