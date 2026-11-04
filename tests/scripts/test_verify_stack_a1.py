"""Pruebas del criterio A1 de `verify_stack.py`: hay eventos reales en `live.current_event`."""
from scripts.verify_stack import REAL_EVENT_COUNT_SQL, has_real_event


def test_positive_count_means_real_events_are_present():
    assert has_real_event("37\n")
    assert has_real_event("1")


def test_zero_empty_or_non_numeric_output_means_none():
    assert not has_real_event("0")
    assert not has_real_event("")
    assert not has_real_event("ERROR: relation does not exist")


def test_query_filters_real_events_from_the_feed():
    assert "is_synthetic = false" in REAL_EVENT_COUNT_SQL
    assert "source = 'usgs_feed'" in REAL_EVENT_COUNT_SQL
    assert "live.current_event" in REAL_EVENT_COUNT_SQL
