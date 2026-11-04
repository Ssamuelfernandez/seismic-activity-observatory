"""Pruebas de common/retry.py: espera exponencial y reintentos hasta el éxito (A4)."""
import asyncio

from common.config import RetrySettings
from common.retry import next_delay, retry_forever


def test_next_delay_doubles_each_attempt():
    settings = RetrySettings(initial_seconds=1, max_seconds=30)
    assert [next_delay(n, settings) for n in (1, 2, 3, 4)] == [1, 2, 4, 8]


def test_next_delay_is_capped_at_maximum():
    settings = RetrySettings(initial_seconds=1, max_seconds=30)
    assert next_delay(10, settings) == 30


def test_retry_forever_retries_until_operation_succeeds():
    calls = {"count": 0}

    async def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectionError("todavía no")
        return "listo"

    settings = RetrySettings(initial_seconds=0.001, max_seconds=0.001)
    result = asyncio.run(retry_forever(flaky, "prueba", settings, (ConnectionError,)))
    assert result == "listo"
    assert calls["count"] == 3


def test_retry_forever_does_not_swallow_unexpected_errors():
    async def broken() -> None:
        raise ValueError("error de programación")

    settings = RetrySettings(initial_seconds=0.001, max_seconds=0.001)
    try:
        asyncio.run(retry_forever(broken, "prueba", settings, (ConnectionError,)))
    except ValueError:
        return
    raise AssertionError("debía propagarse el ValueError")
