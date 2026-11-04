"""Pruebas de consumer/counters.py: contadores de C8 e identidades de FR-023/FR-036 (T049)."""
import pytest

from common.records import MessageRef, ProcessingResult, ResultKind, VersionOutcome
from consumer.counters import Counters, apply_result, check_identities, snapshot

REF = MessageRef("earthquakes.live", 0, 0)
O = VersionOutcome


def event(outcome: VersionOutcome, nulls: tuple[str, ...] = ()) -> ProcessingResult:
    return ProcessingResult(ResultKind.EVENT, REF, outcome=outcome, converted=True, nulls=nulls)


def quarantine(reason: str, inserted: bool, converted: bool = False) -> ProcessingResult:
    return ProcessingResult(ResultKind.QUARANTINE, REF, reason=reason, inserted=inserted, converted=converted)


FAQ12 = [event(O.NEW_EVENT), event(O.REDELIVERY), event(O.NEWER_VERSION), event(O.REDELIVERY), event(O.NEW_EVENT)]
LAT_TWICE = [quarantine("coordinates_out_of_range", True), quarantine("coordinates_out_of_range", False)]
DB_TWICE = [quarantine("db_constraint_violation", True, converted=True),
            quarantine("db_constraint_violation", False, converted=True)]


def run(results: list[ProcessingResult]) -> dict:
    counters = Counters()
    for result in results:
        apply_result(counters, result)
    return snapshot(counters)


def test_initial_snapshot_is_all_zero_with_empty_maps():
    data = snapshot(Counters())
    assert data["received"] == 0 and data["ms_to_utc_conversions"] == 0
    assert data["nulls_kept"] == {} and data["quarantined"] == {} and data["quarantine_duplicates"] == {}


@pytest.mark.parametrize("outcome, field", [
    (O.NEW_EVENT, "new_events"), (O.NEWER_VERSION, "newer_versions_applied"),
    (O.LATE_OLD_VERSION, "late_old_versions"), (O.REDELIVERY, "redeliveries_ignored"),
    (O.SAME_UPDATED_CONFLICT, "same_updated_conflicts"),
])
def test_each_outcome_increments_its_own_counter_and_received(outcome, field):
    data = run([event(outcome)])
    assert data[field] == 1 and data["received"] == 1 and data["ms_to_utc_conversions"] == 1
    assert sum(data[name] for name in ("new_events", "newer_versions_applied", "late_old_versions",
                                       "redeliveries_ignored", "same_updated_conflicts")) == 1


def test_conversion_counts_only_when_converted():
    data = run([quarantine("invalid_json", True)])
    assert data["received"] == 1 and data["ms_to_utc_conversions"] == 0


def test_nulls_kept_counts_per_field():
    data = run([event(O.NEW_EVENT, ("mag", "place")), event(O.NEW_EVENT, ("mag",))])
    assert data["nulls_kept"] == {"mag": 2, "place": 1}


def test_new_quarantine_rows_and_duplicates_are_counted_apart_by_reason():
    data = run(LAT_TWICE + [quarantine("invalid_json", True)])
    assert data["quarantined"] == {"coordinates_out_of_range": 1, "invalid_json": 1}
    assert data["quarantine_duplicates"] == {"coordinates_out_of_range": 1}


@pytest.mark.parametrize("name, results, received, conversions", [
    ("caso 1: FAQ 12", FAQ12, 5, 5),
    ("caso 2: FAQ 12 + latitud 145 dos veces", FAQ12 + LAT_TWICE, 7, 5),
    ("caso 3: FAQ 12 + db_constraint_violation dos veces", FAQ12 + DB_TWICE, 7, 7),
])
def test_fr036_cases_satisfy_the_identities(name, results, received, conversions):
    data = run(results)
    assert data["received"] == received and data["ms_to_utc_conversions"] == conversions, name
    assert check_identities(data) == []


def test_fr036_case_values_of_the_event_counters():
    data = run(FAQ12 + DB_TWICE)
    assert (data["new_events"], data["newer_versions_applied"], data["redeliveries_ignored"]) == (2, 1, 2)
    assert data["quarantined"] == {"db_constraint_violation": 1}
    assert data["quarantine_duplicates"] == {"db_constraint_violation": 1}


def test_check_identities_detects_tampered_counters():
    good = run(FAQ12 + LAT_TWICE)
    assert check_identities({**good, "ms_to_utc_conversions": good["ms_to_utc_conversions"] + 1})
    assert check_identities({**good, "received": good["received"] + 1})
    assert check_identities({**good, "new_events": good["new_events"] + 1})
    assert check_identities({**good, "quarantine_duplicates": {}})


def test_snapshot_is_a_copy_not_a_view():
    counters = Counters()
    data = snapshot(counters)
    apply_result(counters, event(O.NEW_EVENT, ("mag",)))
    assert data["received"] == 0 and data["nulls_kept"] == {}
