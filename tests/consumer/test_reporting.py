"""Pruebas de consumer/reporting.py: línea de decisión y volcado de contadores (T047)."""
import asyncio
import json
import logging

import pytest

from common.records import MessageRef, ProcessingResult, ResultKind, VersionOutcome
from consumer import reporting
from consumer.counters import Counters, apply_result

REF = MessageRef("earthquakes.live", 0, 12)
REPORT_LOGGER = "consumer.reporting"


def event(outcome: VersionOutcome, event_id: str | None = "synthetic-faq12-e1", updated_ms: int | None = 99):
    return ProcessingResult(ResultKind.EVENT, REF, outcome=outcome, converted=True, event_id=event_id,
                            updated_ms=updated_ms)


def quarantine(inserted: bool, reason: str = "coordinates_out_of_range", event_id: str | None = None):
    return ProcessingResult(ResultKind.QUARANTINE, REF, reason=reason, inserted=inserted, event_id=event_id)


def decision_lines(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == REPORT_LOGGER]


@pytest.mark.parametrize("outcome, name", [
    (VersionOutcome.NEW_EVENT, "new_event"), (VersionOutcome.NEWER_VERSION, "newer_version"),
    (VersionOutcome.LATE_OLD_VERSION, "late_old_version"), (VersionOutcome.REDELIVERY, "redelivery_ignored"),
])
def test_event_decision_line_is_info_with_the_contract_format(caplog, outcome, name):
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.log_decision(event(outcome))
    (record,) = decision_lines(caplog)
    assert record.levelno == logging.INFO
    assert record.getMessage() == (f"decision={name} event_id=synthetic-faq12-e1 "
                                   "topic=earthquakes.live partition=0 offset=12")


def test_missing_event_id_is_written_as_dash(caplog):
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.log_decision(event(VersionOutcome.NEW_EVENT, event_id=None))
    assert "event_id=- " in decision_lines(caplog)[0].getMessage()


def test_new_quarantine_row_carries_the_reason(caplog):
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.log_decision(quarantine(True))
    assert decision_lines(caplog)[0].getMessage() == (
        "decision=quarantined event_id=- topic=earthquakes.live partition=0 offset=12 "
        "reason=coordinates_out_of_range")


def test_duplicate_quarantine_row_is_quarantine_duplicate_with_reason(caplog):
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.log_decision(quarantine(False, "invalid_json", "synthetic-x"))
    message = decision_lines(caplog)[0].getMessage()
    assert message.startswith("decision=quarantine_duplicate event_id=synthetic-x ")
    assert message.endswith("reason=invalid_json")


def test_event_lines_never_carry_a_reason(caplog):
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.log_decision(event(VersionOutcome.NEW_EVENT))
    assert "reason=" not in decision_lines(caplog)[0].getMessage()


def test_same_updated_conflict_is_a_single_warning_line_with_updated_ms(caplog):
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.log_decision(event(VersionOutcome.SAME_UPDATED_CONFLICT, updated_ms=1793786700000))
    (record,) = decision_lines(caplog)
    assert record.levelno == logging.WARNING
    assert record.getMessage() == ("decision=same_updated_conflict event_id=synthetic-faq12-e1 "
                                   "updated_ms=1793786700000 topic=earthquakes.live partition=0 offset=12")


def test_dump_counters_writes_one_counters_line_with_sorted_keys(caplog):
    counters = Counters()
    apply_result(counters, event(VersionOutcome.NEW_EVENT))
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        reporting.dump_counters(counters)
    (record,) = decision_lines(caplog)
    message = record.getMessage()
    assert message.startswith("COUNTERS {")
    payload = json.loads(message.removeprefix("COUNTERS "))
    assert payload["received"] == 1 and payload["new_events"] == 1
    assert list(payload) == sorted(payload)


async def _run_periodic(counters: Counters, ticks: int, caplog) -> list[float]:
    """Lanza la corrutina con un reloj simulado, la deja dar `ticks` vueltas y la cancela."""
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        await asyncio.sleep(0)

    task = asyncio.create_task(reporting.run_counters_dump(counters, sleep=fake_sleep))
    while len(sleeps) < ticks:
        await asyncio.sleep(0)
    caplog_before = len([r for r in caplog.records if r.getMessage().startswith("COUNTERS")])
    assert caplog_before >= ticks - 1
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    return sleeps


def test_periodic_task_dumps_every_interval_and_writes_one_final_dump_when_cancelled(caplog):
    counters = Counters()
    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        sleeps = asyncio.run(_run_periodic(counters, 3, caplog))
    assert set(sleeps) == {reporting.COUNTERS_LOG_INTERVAL_SECONDS} == {60}
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("COUNTERS")]
    assert len(lines) >= 3


def test_final_dump_is_written_once_and_only_on_cancellation(caplog):
    counters = Counters()

    async def scenario() -> int:
        gate = asyncio.Event()

        async def blocked_sleep(seconds: float) -> None:
            await gate.wait()

        task = asyncio.create_task(reporting.run_counters_dump(counters, sleep=blocked_sleep))
        await asyncio.sleep(0)
        before = len([r for r in caplog.records if r.getMessage().startswith("COUNTERS")])
        apply_result(counters, event(VersionOutcome.NEW_EVENT))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return before

    with caplog.at_level(logging.INFO, logger=REPORT_LOGGER):
        before = asyncio.run(scenario())
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("COUNTERS")]
    assert before == 0 and len(lines) == 1
    assert json.loads(lines[0].removeprefix("COUNTERS "))["received"] == 1
