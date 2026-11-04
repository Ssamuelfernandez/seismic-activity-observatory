"""Pruebas del bucle del productor: backoff, latido y configuración de arranque."""
import asyncio

import pytest

from common.backoff import BackoffSettings
from common.config import ConfigError
from producer.cycle import (
    CycleResult, STATUS_DB_ERROR, STATUS_FETCH_ERROR, STATUS_KAFKA_ERROR, STATUS_OK,
)
from producer.loop import format_cycle_line, run_loop
from producer.main import build_settings

BACKOFF = BackoffSettings(initial_seconds=2, max_seconds=60)
POLL = 60


def _drive(statuses: list[str]):
    """Ejecuta el bucle con una secuencia de resultados; devuelve (esperas, latidos)."""
    results = iter(CycleResult(status) for status in statuses)
    waits: list[float] = []
    beats: list[int] = []

    async def run_one():
        return next(results)

    async def sleep(seconds):
        waits.append(seconds)

    asyncio.run(run_loop(run_one, lambda: beats.append(1), sleep, POLL, BACKOFF,
                         jitter=lambda: 1.0, max_cycles=len(statuses)))
    return waits, beats


def test_consecutive_usgs_failures_wait_longer_each_time():
    waits, _ = _drive([STATUS_FETCH_ERROR] * 3)
    assert waits == [2, 4, 8]


def test_successful_cycle_resets_counter_and_waits_poll_seconds():
    waits, _ = _drive([STATUS_FETCH_ERROR, STATUS_FETCH_ERROR, STATUS_OK, STATUS_FETCH_ERROR])
    assert waits == [2, 4, POLL, 2]


def test_heartbeat_renewed_after_usgs_failure_but_not_after_kafka_or_db_failure():
    _, beats = _drive([STATUS_FETCH_ERROR])
    assert len(beats) == 1
    _, beats = _drive([STATUS_KAFKA_ERROR, STATUS_DB_ERROR])
    assert beats == []


def test_cycle_line_has_the_documented_fields():
    line = format_cycle_line(3, CycleResult(STATUS_OK, 200, 120, fetched=5, published=1, skipped=4), 60)
    assert line == ("cycle=3 status=ok http=200 latency_ms=120 fetched=5 excluded=0 published=1 "
                    "skipped=4 unmarked=0 next_wait_s=60.0")
    assert "http=-" in format_cycle_line(1, CycleResult(STATUS_FETCH_ERROR), 2)


def _set_env(monkeypatch, poll: str) -> None:
    for name, value in {"HEALTH_FILE": "/tmp/p.alive", "HEALTH_MAX_AGE_SECONDS": "120",
                        "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092", "KAFKA_TOPIC": "earthquakes.live",
                        "DB_HOST": "postgres", "DB_PORT": "5432", "DB_NAME": "x", "DB_USER": "u",
                        "DB_PASSWORD": "p", "POLL_SECONDS": poll}.items():
        monkeypatch.setenv(name, value)


def test_startup_rejects_poll_seconds_above_half_the_heartbeat_age(monkeypatch):
    _set_env(monkeypatch, "61")
    with pytest.raises(ConfigError, match="POLL_SECONDS"):
        build_settings()


def test_startup_accepts_valid_configuration(monkeypatch):
    _set_env(monkeypatch, "60")
    assert build_settings().feed.poll_seconds == 60
