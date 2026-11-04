"""Pruebas del cliente HTTP del feed con el servidor simulado (T007). Sin red externa."""
import asyncio

import pytest

from producer.usgs_client import FeedFetchError, fetch_feed
from tests.support.mock_usgs import MODE_429, MODE_500, MODE_SLOW, MockUsgs, synthetic_feature

TIMEOUT_SECONDS = 1


@pytest.fixture
def mock():
    server = MockUsgs().start()
    server.features = [synthetic_feature(1)]
    yield server
    server.stop()


def test_ok_returns_body_and_latency(mock: MockUsgs) -> None:
    response = asyncio.run(fetch_feed(mock.url, TIMEOUT_SECONDS))
    assert response.status == 200
    assert b"synthetic-1" in response.body
    assert response.latency_ms > 0
    assert response.received_at.tzinfo is not None


@pytest.mark.parametrize("mode,status", [(MODE_500, 500), (MODE_429, 429)])
def test_http_errors_carry_status(mock: MockUsgs, mode: str, status: int) -> None:
    mock.mode = mode
    with pytest.raises(FeedFetchError) as caught:
        asyncio.run(fetch_feed(mock.url, TIMEOUT_SECONDS))
    assert caught.value.status == status
    assert caught.value.latency_ms >= 0


def test_slow_response_times_out_without_status(mock: MockUsgs) -> None:
    mock.mode = MODE_SLOW
    with pytest.raises(FeedFetchError) as caught:
        asyncio.run(fetch_feed(mock.url, TIMEOUT_SECONDS))
    assert caught.value.status is None
    assert caught.value.message == "timeout"
    assert caught.value.latency_ms >= TIMEOUT_SECONDS * 900


def test_stopped_server_raises_fetch_error() -> None:
    server = MockUsgs().start()
    url = server.url
    server.stop()
    with pytest.raises(FeedFetchError) as caught:
        asyncio.run(fetch_feed(url, TIMEOUT_SECONDS))
    assert caught.value.status is None
