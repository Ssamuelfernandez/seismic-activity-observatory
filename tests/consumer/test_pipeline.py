"""Pruebas de consumer/pipeline.py con escritores y reloj de mentira (T053)."""
import asyncio
import copy
import logging
from datetime import datetime, timezone

import asyncpg.exceptions as pg_exc
import pytest

from common.geo import CountryMatch
from common.records import MessageRef, RawRecord, ResultKind, VersionOutcome
from consumer import pipeline, resilience
from consumer.pipeline import PipelineDeps, process_record
from consumer.resilience import RetryControl, StopRequested
from common.config import RetrySettings
from tests.support.messages import (
    E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message, to_bytes,
)

NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
TOPIC = "earthquakes.live"


class Recorder:
    """Escritores y gancho de mentira que anotan el orden de las llamadas."""

    def __init__(self, outcome=VersionOutcome.NEW_EVENT, event_errors=(), quarantine_errors=(), inserted=True):
        self.calls: list[str] = []
        self.outcome = outcome
        self.event_errors = list(event_errors)
        self.quarantine_errors = list(quarantine_errors)
        self.inserted = inserted
        self.rows = []
        self.hook_args = []
        self.locate_calls: list[tuple[float, float]] = []
        self.event_rows = []
        self.match = CountryMatch("ESP", ("ESP",))

    def locate(self, lon, lat):
        self.calls.append("locate")
        self.locate_calls.append((lon, lat))
        return self.match

    async def write_event(self, rows, mode):
        self.calls.append("write_event")
        self.event_rows.append(rows)
        if self.event_errors:
            raise self.event_errors.pop(0)
        return self.outcome

    async def write_quarantine(self, row, mode):
        self.calls.append("write_quarantine")
        self.rows.append(row)
        if self.quarantine_errors:
            raise self.quarantine_errors.pop(0)
        return self.inserted

    def hook(self, ref, is_synthetic):
        self.calls.append("after_db_commit")
        self.hook_args.append((ref, is_synthetic))

    def deps(self, stop_event=None, with_hook=True) -> PipelineDeps:
        control = RetryControl(RetrySettings(1, 30), stop_event or asyncio.Event())
        return PipelineDeps(self.write_event, self.write_quarantine, control, self.locate, lambda: NOW,
                            self.hook if with_hook else None)


@pytest.fixture(autouse=True)
def no_real_waits(monkeypatch):
    waits: list[float] = []

    async def fake_wait(stop_event, delay):
        waits.append(delay)
        return stop_event.is_set()

    monkeypatch.setattr(resilience, "wait_or_stop", fake_wait)
    return waits


def record(value: bytes | None, offset: int = 4) -> RawRecord:
    return RawRecord(TOPIC, 0, offset, b"key", value)


def valid_record(mag: float | None = 4.2, offset: int = 4) -> RawRecord:
    return record(to_bytes(build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, mag)), offset)


def latitude_145_record() -> RawRecord:
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    message["event"]["geometry"]["coordinates"][1] = 145
    return record(to_bytes(message))


def nan_dmin_record() -> RawRecord:
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    message["event"]["properties"]["dmin"] = float("nan")
    return record(to_bytes(message))


def run(rec: RawRecord, recorder: Recorder, **kwargs):
    return asyncio.run(process_record(rec, recorder.deps(**kwargs)))


def test_valid_message_writes_and_then_calls_the_hook_in_that_order():
    recorder = Recorder()
    run(valid_record(), recorder)
    assert recorder.calls == ["locate", "write_event", "after_db_commit"]


def test_valid_message_result_has_all_the_fields():
    recorder = Recorder(outcome=VersionOutcome.NEWER_VERSION)
    result = run(valid_record(mag=None), recorder)
    assert result.kind is ResultKind.EVENT and result.outcome is VersionOutcome.NEWER_VERSION
    assert result.converted is True and result.event_id == FAQ12_E1 and result.is_synthetic is True
    assert result.ref == MessageRef(TOPIC, 0, 4) and result.updated_ms == E1_UPDATED_1005
    assert "mag" in result.nulls


def test_hook_receives_the_reference_and_the_synthetic_flag():
    recorder = Recorder()
    run(valid_record(), recorder)
    assert recorder.hook_args == [(MessageRef(TOPIC, 0, 4), True)]


def test_rejected_message_goes_to_quarantine_without_touching_the_event_writer():
    recorder = Recorder()
    result = run(latitude_145_record(), recorder)
    assert recorder.calls == ["write_quarantine", "after_db_commit"]
    assert result.kind is ResultKind.QUARANTINE and result.reason == "coordinates_out_of_range"
    assert result.inserted is True and result.converted is False and result.updated_ms is None
    assert result.event_id == FAQ12_E1 and result.nulls == ()


def test_duplicate_quarantine_row_is_reported_as_not_inserted():
    result = run(latitude_145_record(), Recorder(inserted=False))
    assert result.kind is ResultKind.QUARANTINE and result.inserted is False


@pytest.mark.parametrize("value, reason", [(None, "invalid_json"), (b"", "invalid_json"), (b"{roto", "invalid_json")])
def test_undecodable_values_are_quarantined_as_invalid_json(value, reason):
    recorder = Recorder()
    result = run(record(value), recorder)
    assert result.reason == reason and recorder.rows[0].original_sha256
    assert "write_event" not in recorder.calls


def test_pre_database_db_constraint_violation_is_quarantined_and_counts_as_converted():
    recorder = Recorder()
    result = run(nan_dmin_record(), recorder)
    assert result.kind is ResultKind.QUARANTINE and result.reason == "db_constraint_violation"
    assert result.converted is True and result.updated_ms is None
    assert recorder.calls == ["write_quarantine", "after_db_commit"]


def test_content_error_from_the_event_writer_goes_to_quarantine_and_logs_validation_gap(caplog):
    recorder = Recorder(event_errors=[pg_exc.CheckViolationError("viola un CHECK")])
    with caplog.at_level(logging.ERROR, logger="consumer.pipeline"):
        result = run(valid_record(), recorder)
    assert result.kind is ResultKind.QUARANTINE and result.reason == "db_constraint_violation"
    assert result.converted is True and result.inserted is True and result.nulls == ()
    assert recorder.calls == ["locate", "write_event", "write_quarantine", "after_db_commit"]
    (line,) = [r for r in caplog.records if r.levelno == logging.ERROR]
    message = line.getMessage()
    assert message.startswith(f"validation_gap event_id={FAQ12_E1} sqlstate=23514")
    assert "topic=earthquakes.live partition=0 offset=4" in message


def test_transient_error_is_retried_and_then_the_result_is_normal(no_real_waits):
    recorder = Recorder(event_errors=[OSError("caída"), pg_exc.CannotConnectNowError("arrancando")])
    result = run(valid_record(), recorder)
    assert result.kind is ResultKind.EVENT and recorder.calls.count("write_event") == 3
    assert no_real_waits == [1, 2] and recorder.calls[-1] == "after_db_commit"


def test_failed_quarantine_write_is_retried_without_creating_another_quarantine_row():
    recorder = Recorder(quarantine_errors=[pg_exc.CheckViolationError("falla")])
    result = run(latitude_145_record(), recorder)
    assert recorder.calls == ["write_quarantine", "write_quarantine", "after_db_commit"]
    assert recorder.rows[0] == recorder.rows[1] and recorder.rows[0].reason == "coordinates_out_of_range"
    assert result.inserted is True


def test_permanent_writer_failure_never_returns_and_never_reaches_the_hook():
    recorder = Recorder(event_errors=[OSError("caída")] * 100)
    stop = asyncio.Event()
    stop.set()
    with pytest.raises(StopRequested):
        run(valid_record(), recorder, stop_event=stop)
    assert recorder.calls == ["locate", "write_event"]


def test_no_hook_installed_means_nothing_is_called_after_the_write():
    recorder = Recorder()
    run(valid_record(), recorder, with_hook=False)
    assert recorder.calls == ["locate", "write_event"]


def test_program_defect_in_the_writer_is_not_swallowed():
    recorder = Recorder(event_errors=[TypeError("defecto")])
    with pytest.raises(TypeError):
        run(valid_record(), recorder)


def test_the_message_is_not_mutated_and_the_clock_is_injected():
    recorder = Recorder()
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    before = copy.deepcopy(message)
    run(record(to_bytes(message)), recorder)
    assert message == before and pipeline.utc_now().tzinfo is timezone.utc


def test_locator_is_called_once_with_lon_lat_and_its_country_reaches_the_writer():
    recorder = Recorder()
    run(valid_record(), recorder)
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    lon, lat = message["event"]["geometry"]["coordinates"][:2]
    assert recorder.locate_calls == [(lon, lat)]
    assert recorder.event_rows[0].current["country_id"] == "ESP"
    assert "country_id" not in recorder.event_rows[0].version


def test_locator_is_not_called_when_the_message_goes_to_quarantine():
    recorder = Recorder()
    run(latitude_145_record(), recorder)
    assert recorder.locate_calls == [] and "locate" not in recorder.calls


def test_no_country_is_written_as_none():
    recorder = Recorder()
    recorder.match = CountryMatch(None, ())
    run(valid_record(), recorder)
    assert recorder.event_rows[0].current["country_id"] is None


def test_multiple_candidates_log_a_country_tie_line(caplog):
    recorder = Recorder()
    recorder.match = CountryMatch("AAA", ("AAA", "BBB"))
    with caplog.at_level(logging.INFO, logger="consumer.pipeline"):
        run(valid_record(), recorder)
    (line,) = [r.getMessage() for r in caplog.records if r.getMessage().startswith("country_tie")]
    assert line == f"country_tie event_id={FAQ12_E1} candidates=AAA,BBB chosen=AAA"


@pytest.mark.parametrize("match", [CountryMatch("ESP", ("ESP",)), CountryMatch(None, ())])
def test_single_or_no_candidate_logs_no_country_tie(caplog, match):
    recorder = Recorder()
    recorder.match = match
    with caplog.at_level(logging.INFO, logger="consumer.pipeline"):
        run(valid_record(), recorder)
    assert not [r for r in caplog.records if "country_tie" in r.getMessage()]
