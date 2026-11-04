"""Pruebas de `common/ingest_decision.py`: tabla de decisión de research.md §3 (B3, B6)."""
from datetime import datetime, timezone

import pytest

from common.ingest_decision import Decision, build_exclusion_row, decide_publication

FETCHED_AT = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)


def _feature(event_id="synthetic-1", updated=1000, kind="earthquake"):
    properties = {"updated": updated, "mag": 1.0}
    if kind is not None:
        properties["type"] = kind
    feature = {"type": "Feature", "properties": properties}
    if event_id is not None:
        feature["id"] = event_id
    return feature


def test_new_event_is_published():
    assert decide_publication(_feature(), None) is Decision.PUBLISH


def test_greater_updated_is_published():
    assert decide_publication(_feature(updated=2000), 1000) is Decision.PUBLISH


def test_equal_updated_is_skipped():
    assert decide_publication(_feature(updated=1000), 1000) is Decision.SKIP


def test_lower_updated_is_skipped():
    assert decide_publication(_feature(updated=500), 1000) is Decision.SKIP


def test_other_type_is_excluded():
    assert decide_publication(_feature(kind="quarry blast"), None) is Decision.EXCLUDE


def test_other_type_is_excluded_even_with_previous_state():
    assert decide_publication(_feature(kind="explosion", updated=5), 1000) is Decision.EXCLUDE


def test_missing_type_is_excluded():
    assert decide_publication(_feature(kind=None), None) is Decision.EXCLUDE


def test_missing_id_is_published_unmarked():
    assert decide_publication(_feature(event_id=None), None) is Decision.PUBLISH_UNMARKED


def test_empty_id_is_published_unmarked():
    assert decide_publication(_feature(event_id=""), None) is Decision.PUBLISH_UNMARKED


def test_missing_updated_is_published_unmarked():
    feature = _feature()
    del feature["properties"]["updated"]
    assert decide_publication(feature, None) is Decision.PUBLISH_UNMARKED


@pytest.mark.parametrize("updated", [True, False, "1000", 1000.5, None])
def test_non_integer_updated_is_published_unmarked(updated):
    assert decide_publication(_feature(updated=updated), None) is Decision.PUBLISH_UNMARKED


def test_invalidity_prevails_over_type():
    feature = _feature(event_id=None, kind="quarry blast")
    assert decide_publication(feature, None) is Decision.PUBLISH_UNMARKED


def test_missing_properties_is_published_unmarked():
    assert decide_publication({"id": "synthetic-1"}, None) is Decision.PUBLISH_UNMARKED


def test_exclusion_row_follows_the_data_model():
    row = build_exclusion_row(_feature(kind="quarry blast", updated=77), FETCHED_AT)
    assert row == {
        "event_id": "synthetic-1", "updated_ms": 77, "kind": "non_earthquake_type",
        "reason": "properties.type distinto de earthquake", "observed_type": "quarry blast",
        "fetched_at": FETCHED_AT, "is_synthetic": False,
    }


def test_exclusion_row_without_type_has_null_observed_type():
    row = build_exclusion_row(_feature(kind=None), FETCHED_AT)
    assert row["observed_type"] is None
