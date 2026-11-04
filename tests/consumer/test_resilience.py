"""Pruebas de consumer/resilience.py: reintentos sin límite, registro por intento y parada limpia (T045).

La espera está simulada (`wait_or_stop` sustituida): ninguna prueba duerme de verdad.
"""
import asyncio
import logging
import re

import asyncpg.exceptions as pg_exc
import pytest
from aiokafka.errors import CommitFailedError, KafkaConnectionError
from aiokafka.structs import TopicPartition

from common.config import RetrySettings
from common.records import MessageRef
from consumer import resilience
from consumer.resilience import OpContext, RetryControl, StopRequested

SETTINGS = RetrySettings(initial_seconds=1, max_seconds=30)
REF = MessageRef("earthquakes.live", 0, 7)
RETRY_FIELDS = ("attempt", "wait_s", "op", "event_id", "topic", "partition", "offset", "error", "sqlstate", "detail")
DETAIL_LIMIT = 200


class Flaky:
    """Operación que falla `failures` veces con el error dado y después devuelve un valor."""

    def __init__(self, failures: int, error: BaseException):
        self.failures = failures
        self.error = error
        self.calls = 0

    async def __call__(self) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return "ok"


@pytest.fixture
def waits(monkeypatch):
    """Sustituye la espera por un registro de los segundos pedidos (no duerme)."""
    recorded: list[float] = []

    async def fake_wait(stop_event: asyncio.Event, delay_seconds: float) -> bool:
        recorded.append(delay_seconds)
        return stop_event.is_set()

    monkeypatch.setattr(resilience, "wait_or_stop", fake_wait)
    return recorded


def _control() -> RetryControl:
    return RetryControl(SETTINGS, asyncio.Event())


def _context(event_id: str | None = "synthetic-x", op: str = "write_event") -> OpContext:
    return OpContext(op, event_id, REF)


def _retry(operation, context=None, control=None, retry_content=False):
    return asyncio.run(resilience.retry_db_operation(operation, context or _context(),
                                                     control or _control(), retry_content))


def test_wait_sequence_is_1_2_4_8_16_30_30(waits):
    assert _retry(Flaky(7, OSError("sin red"))) == "ok"
    assert waits == [1, 2, 4, 8, 16, 30, 30]


def test_there_is_no_attempt_limit(waits):
    operation = Flaky(60, pg_exc.CannotConnectNowError("arrancando"))
    assert _retry(operation) == "ok"
    assert operation.calls == 61 and len(waits) == 60


def test_each_new_call_restarts_the_wait_at_one_second(waits):
    _retry(Flaky(3, OSError("x")))
    _retry(Flaky(1, OSError("x")))
    assert waits == [1, 2, 4, 1]


def test_one_warning_per_attempt_with_every_field_and_no_traceback(waits, caplog):
    error = pg_exc.CannotConnectNowError("x" * 500)
    with caplog.at_level(logging.WARNING, logger="consumer.resilience"):
        _retry(Flaky(3, error))
    lines = [r for r in caplog.records if r.getMessage().startswith("retry ")]
    assert len(lines) == 3
    for number, record in enumerate(lines, start=1):
        message = record.getMessage()
        assert record.levelno == logging.WARNING and record.exc_info is None
        assert all(f"{field}=" in message for field in RETRY_FIELDS)
        assert f"attempt={number} " in message and "op=write_event" in message
        assert "error=CannotConnectNowError" in message and "sqlstate=57P03" in message
        assert "topic=earthquakes.live partition=0 offset=7" in message
        detail = re.search(r'detail="([^"]*)"', message).group(1)
        assert len(detail) == DETAIL_LIMIT


def test_missing_event_id_is_written_as_dash_and_sqlstate_as_dash(waits, caplog):
    with caplog.at_level(logging.WARNING, logger="consumer.resilience"):
        _retry(Flaky(1, OSError("caída")), _context(event_id=None, op="write_quarantine"))
    message = caplog.records[0].getMessage()
    assert "event_id=- " in message and "sqlstate=- " in message and "op=write_quarantine" in message


def test_content_error_is_not_retried_and_propagates(waits):
    operation = Flaky(1, pg_exc.CheckViolationError("rechazado"))
    with pytest.raises(pg_exc.CheckViolationError):
        _retry(operation)
    assert operation.calls == 1 and waits == []


def test_program_defect_is_not_retried(waits):
    operation = Flaky(1, TypeError("defecto"))
    with pytest.raises(TypeError):
        _retry(operation)
    assert operation.calls == 1 and waits == []


def test_quarantine_write_retries_even_content_errors(waits):
    operation = Flaky(2, pg_exc.CheckViolationError("rechazado"))
    assert _retry(operation, _context(op="write_quarantine"), retry_content=True) == "ok"
    assert operation.calls == 3 and waits == [1, 2]


def test_stop_signal_interrupts_the_wait_without_retrying_again():
    control = _control()
    control.stop_event.set()
    operation = Flaky(5, OSError("caída"))
    with pytest.raises(StopRequested):
        _retry(operation, control=control)
    assert operation.calls == 1


def test_wait_or_stop_returns_true_when_stopped_and_false_after_the_delay():
    stopped = asyncio.Event()
    stopped.set()
    assert asyncio.run(resilience.wait_or_stop(stopped, 30)) is True
    assert asyncio.run(resilience.wait_or_stop(asyncio.Event(), 0.01)) is False


class FakeKafkaConsumer:
    """Consumidor de mentira: `commit` falla con los errores indicados y luego acepta."""

    def __init__(self, errors: list[BaseException]):
        self.errors = list(errors)
        self.commits: list[dict] = []

    async def commit(self, offsets: dict) -> None:
        self.commits.append(offsets)
        if self.errors:
            raise self.errors.pop(0)


def _commit(consumer: FakeKafkaConsumer) -> bool:
    return asyncio.run(resilience.commit_offset_with_retry(consumer, _context(op="commit_offset"), _control()))


def test_commit_sends_offset_plus_one(waits):
    consumer = FakeKafkaConsumer([])
    assert _commit(consumer) is True
    assert consumer.commits == [{TopicPartition("earthquakes.live", 0): 8}]


def test_commit_failed_is_logged_but_not_retried(waits, caplog):
    consumer = FakeKafkaConsumer([CommitFailedError("el grupo cambió de generación")])
    with caplog.at_level(logging.WARNING, logger="consumer.resilience"):
        assert _commit(consumer) is False
    assert len(consumer.commits) == 1 and waits == []
    assert any("CommitFailedError" in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("error", [KafkaConnectionError("sin broker"), OSError("red")])
def test_other_commit_errors_are_retried(waits, error):
    consumer = FakeKafkaConsumer([error, error])
    assert _commit(consumer) is True
    assert len(consumer.commits) == 3 and waits == [1, 2]


def test_commit_retry_line_has_the_commit_operation_name(waits, caplog):
    with caplog.at_level(logging.WARNING, logger="consumer.resilience"):
        _commit(FakeKafkaConsumer([OSError("red")]))
    assert "op=commit_offset" in caplog.records[0].getMessage()
