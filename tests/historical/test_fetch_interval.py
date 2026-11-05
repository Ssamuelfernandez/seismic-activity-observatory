"""Pruebas de la descarga de un intervalo con USGS simulado (T005 y T006, B13)."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

import pytest

from historical.fetch_interval import (
    MAX_ATTEMPTS, FetchTools, IntervalFetchError, fetch_interval,
)
from historical.intervals import Interval
from producer.usgs_client import FeedFetchError
from tests.support.fake_usgs_query import BASE_URL, FakeUsgs, make_event, spread_events

UTC = timezone.utc
MONTH = Interval(datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 2, 1, tzinfo=UTC))
NOW = datetime(2026, 11, 5, 10, 0, 0, tzinfo=UTC)


def make_tools(fake, sleeps: list[float] | None = None) -> FetchTools:
    async def no_sleep(seconds: float) -> None:
        if sleeps is not None:
            sleeps.append(seconds)

    return FetchTools(fetch=fake.fetch, base_url=BASE_URL, sleep=no_sleep, jitter=lambda: 0.5, now=lambda: NOW)


def test_small_interval_makes_one_count_and_one_query() -> None:
    fake = FakeUsgs(spread_events(MONTH.start, MONTH.end, 100))
    data = asyncio.run(fetch_interval(MONTH, make_tools(fake)))
    assert len(data.features) == 100
    assert fake.request_count == 2
    assert len(data.queries) == 1
    assert data.queries[0].usgs_count == data.queries[0].records == 100


def test_month_with_45000_events_is_split_without_losses(caplog) -> None:
    fake = FakeUsgs(spread_events(MONTH.start, MONTH.end, 45_000))
    with caplog.at_level(logging.INFO):
        data = asyncio.run(fetch_interval(MONTH, make_tools(fake)))
    assert len(data.features) == 45_000
    assert len({item["id"] for item in data.features}) == 45_000
    assert len(data.queries) >= 3
    assert sum(query.records for query in data.queries) == 45_000
    assert data.extracted_at == "2026-11-05T10:00:00Z"
    assert len([line for line in caplog.messages if line.startswith("query ")]) == len(data.queries)


def test_records_different_from_count_raises_with_both_figures() -> None:
    fake = FakeUsgs(spread_events(MONTH.start, MONTH.end, 10), count_override=12)
    with pytest.raises(IntervalFetchError, match=r"12.*10|10.*12"):
        asyncio.run(fetch_interval(MONTH, make_tools(fake)))


def test_one_millisecond_interval_over_limit_raises() -> None:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    tiny = Interval(start, start + timedelta(milliseconds=1))
    fake = FakeUsgs([make_event(index, start) for index in range(1)], count_override=20_001)
    with pytest.raises(IntervalFetchError, match="1 ms"):
        asyncio.run(fetch_interval(tiny, make_tools(fake)))


def test_milliseconds_reach_the_url_when_splitting_deeply() -> None:
    fake = FakeUsgs(spread_events(MONTH.start, MONTH.end, 45_000))
    asyncio.run(fetch_interval(MONTH, make_tools(fake)))
    assert all("starttime=" in url for url in fake.urls)


class FlakyFake(FakeUsgs):
    """Falla las primeras `failures` peticiones con 503 y luego responde."""

    def __init__(self, features: list[dict], failures: int) -> None:
        super().__init__(features)
        self.remaining = failures

    async def fetch(self, url: str) -> bytes:
        if self.remaining > 0:
            self.remaining -= 1
            raise FeedFetchError(503, "HTTP 503", 1)
        return await super().fetch(url)


def test_retries_after_two_failures_then_succeeds() -> None:
    fake = FlakyFake(spread_events(MONTH.start, MONTH.end, 5), failures=2)
    sleeps: list[float] = []
    data = asyncio.run(fetch_interval(MONTH, make_tools(fake, sleeps)))
    assert len(data.features) == 5
    assert len(sleeps) == 2
    assert sleeps[1] > sleeps[0]


def test_gives_up_after_max_attempts_naming_the_interval() -> None:
    fake = FlakyFake(spread_events(MONTH.start, MONTH.end, 5), failures=MAX_ATTEMPTS)
    with pytest.raises(IntervalFetchError, match="2025-01-01T00:00:00"):
        asyncio.run(fetch_interval(MONTH, make_tools(fake)))
    assert fake.remaining == 0
