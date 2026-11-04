"""Pruebas de los auxiliares puros de `scripts/verify_consumer.py` (T071; se ejecutan en el equipo)."""
from pathlib import Path

import pytest

from scripts.consumer_scenarios.helpers import (
    CountersNotFound,
    check_crash_sequence,
    compare_counters,
    compare_with_sql,
    confirm_destructive,
    evidence_path,
    extract_last_counters,
    parse_group_lag,
)

LOG_TWO_DUMPS = (
    '2026-11-04 10:00:00 INFO [consumer.reporting] COUNTERS {"received":1}\n'
    "2026-11-04 10:00:01 INFO [consumer.loop] otra línea\n"
    '2026-11-04 10:01:00 INFO [consumer.reporting] COUNTERS {"received":5,"new_events":2}\n'
    "2026-11-04 10:01:01 INFO [consumer.loop] Parada solicitada\n"
)
FAQ12_COUNTERS = {
    "late_old_versions": 0, "ms_to_utc_conversions": 5, "new_events": 2, "newer_versions_applied": 1,
    "nulls_kept": {}, "quarantine_duplicates": {}, "quarantined": {}, "received": 5,
    "redeliveries_ignored": 2, "same_updated_conflicts": 0,
}
LAG_OUTPUT = (
    "\nGROUP          TOPIC            PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CONSUMER-ID  HOST  CLIENT-ID\n"
    "consumer-live  earthquakes.live  0          {current}               {end}               {lag}    aiokafka-1   /10.0.0.2  aiokafka\n"
)


def test_extract_last_counters_returns_the_last_dump() -> None:
    assert extract_last_counters(LOG_TWO_DUMPS) == {"received": 5, "new_events": 2}


def test_extract_last_counters_without_line_raises_clear_error() -> None:
    with pytest.raises(CountersNotFound, match="COUNTERS"):
        extract_last_counters("2026-11-04 10:00:00 INFO sin contadores\n")


def test_compare_counters_reports_only_the_differences() -> None:
    assert compare_counters(FAQ12_COUNTERS, {"received": 5, "new_events": 2}) == []
    problems = compare_counters(FAQ12_COUNTERS, {"received": 6, "new_events": 2})
    assert len(problems) == 1 and "received" in problems[0]


def test_compare_counters_reports_a_missing_key() -> None:
    assert "inexistente" in compare_counters(FAQ12_COUNTERS, {"inexistente": 1})[0]


def test_compare_with_sql_accepts_consistent_figures() -> None:
    assert compare_with_sql(FAQ12_COUNTERS, current_rows=2, quarantine_by_reason={}) == []


def test_compare_with_sql_detects_sql_and_identity_failures() -> None:
    assert any("new_events" in p for p in compare_with_sql(FAQ12_COUNTERS, current_rows=3, quarantine_by_reason={}))
    broken = {**FAQ12_COUNTERS, "ms_to_utc_conversions": 4}
    assert any("identidad" in p for p in compare_with_sql(broken, current_rows=2, quarantine_by_reason={}))


def test_compare_with_sql_compares_quarantine_by_reason() -> None:
    counters = {**FAQ12_COUNTERS, "received": 6, "quarantined": {"invalid_json": 1}}
    assert compare_with_sql(counters, 2, {"invalid_json": 1}) == []
    assert any("invalid_json" in p for p in compare_with_sql(counters, 2, {"invalid_json": 2}))


@pytest.mark.parametrize(("current", "end", "lag", "expected"), [(5, 5, 0, 0), (5, 105, 100, 100), ("-", 5, "-", None)])
def test_parse_group_lag(current, end, lag, expected) -> None:
    assert parse_group_lag(LAG_OUTPUT.format(current=current, end=end, lag=lag)) == expected


def test_parse_group_lag_without_rows_is_none() -> None:
    assert parse_group_lag("\nConsumer group 'consumer-live' has no active members.\n") is None


def test_evidence_path_is_inside_the_evidence_folder() -> None:
    path = evidence_path("prueba2_reenvio", "out")
    assert isinstance(path, Path)
    assert path.name == "prueba2_reenvio.out"
    assert path.parent.parts[-3:] == ("docs", "evidencias", "consumidor-idempotente")


@pytest.mark.parametrize(("yes", "env", "expected"), [
    (True, {}, True),
    (False, {"VERIFY_CONSUMER_CONFIRM": "yes"}, True),
    (False, {}, False),
    (False, {"VERIFY_CONSUMER_CONFIRM": "no"}, False),
    (False, {"VERIFY_CONSUMER_CONFIRM": "YES"}, False),
    (False, {"VERIFY_CONSUMER_CONFIRM": ""}, False),
])
def test_confirm_destructive(yes: bool, env: dict, expected: bool) -> None:
    class Args:
        pass

    args = Args()
    args.yes = yes
    assert confirm_destructive(args, env) is expected


CRASH_LOG = (
    "INFO decision=new_event event_id=a topic=earthquakes.live partition=0 offset=1\n"
    "WARNING FAULT crash_after_db_commit offset=2\n"
    "INFO Consumidor suscrito al tema earthquakes.live.\n"
    "INFO decision=redelivery_ignored event_id=a topic=earthquakes.live partition=0 offset=2\n"
)


def test_check_crash_sequence_accepts_fault_then_redelivery() -> None:
    assert check_crash_sequence(CRASH_LOG, 2) == []


def test_check_crash_sequence_rejects_decision_before_fault() -> None:
    early = "INFO decision=new_event event_id=a topic=t partition=0 offset=2\n" + CRASH_LOG
    assert any("antes del FAULT" in p for p in check_crash_sequence(early, 2))


def test_check_crash_sequence_rejects_missing_redelivery_and_double_fault() -> None:
    assert any("redelivery_ignored" in p for p in check_crash_sequence(CRASH_LOG.rsplit("\n", 2)[0], 2))
    assert check_crash_sequence(CRASH_LOG + CRASH_LOG, 2)[0].startswith("líneas FAULT")
