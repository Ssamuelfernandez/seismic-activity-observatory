"""Comparación de las últimas 24 h con la media diaria de 2025 (T016: F7, api.md §5.1)."""
import asyncio
import time

from api.timeutil import MS_PER_HOUR, parse_iso_to_ms
from tests.support.api_client import request_api
from tests.support.api_seed import synthetic_event

PATH = "/api/estadisticas"
COUNTRIES = {"ESP": "España", "JPN": "Japón"}
Y2025 = parse_iso_to_ms("2025-06-15")
REFERENCE = {"start": 1_735_689_600_000, "end": 1_767_225_600_000}
DAY_RANGE = {"start": "2026-11-01", "end": "2026-11-02"}


def _get(db, params=None, live=None):
    return asyncio.run(request_api(db, PATH, params=params, live=live, countries=COUNTRIES)).json()


def _history(count, offset=0, **overrides):
    return [synthetic_event(1000 + offset + number, time_ms=Y2025 + number, **overrides) for number in range(count)]


def _recent(count, now, offset=0, **overrides):
    return [synthetic_event(2000 + offset + number, time_ms=now - MS_PER_HOUR - number, **overrides)
            for number in range(count)]


def test_counts_mean_diff_and_variation(db):
    now = int(time.time() * 1000)
    comparison = _get(db, live=_history(730, mag=4.5) + _recent(5, now, mag=4.5))["comparison"]
    assert (comparison["n_2025"], comparison["n_recent"]) == (730, 5)
    assert comparison["daily_mean_2025"] == 2.0 and comparison["diff_abs"] == 3.0
    assert comparison["variation_pct"] == 150.0
    assert comparison["recent_incomplete"] is True and comparison["unit"] == "events"


def test_variation_is_rounded_to_two_decimals(db):
    now = int(time.time() * 1000)
    comparison = _get(db, live=_history(1000, mag=4.5) + _recent(2, now, mag=4.5))["comparison"]
    assert comparison["variation_pct"] == round((2 - 1000 / 365) / (1000 / 365) * 100, 2)


def test_min_mag_applied_for_absent_low_and_high_values(db):
    now = int(time.time() * 1000)
    live = _history(3, mag=4.2) + _history(2, 10, mag=6.0) + _recent(2, now, mag=4.2) + _recent(1, now, 10, mag=6.0)
    seen = {}
    for label, params in (("absent", None), ("low", {"min_mag": "2"}), ("high", {"min_mag": "5.5"})):
        comparison = _get(db, params=params, live=live if label == "absent" else None)["comparison"]
        seen[label] = (comparison["min_mag_applied"], comparison["n_2025"], comparison["n_recent"])
    assert seen == {"absent": (4.0, 5, 3), "low": (4.0, 5, 3), "high": (5.5, 2, 1)}


def test_events_below_four_and_null_mag_are_not_counted(db):
    now = int(time.time() * 1000)
    live = _history(2, mag=3.9) + _history(1, 10, mag=None) + _recent(2, now, mag=3.9) + _recent(1, now, 10, mag=None)
    comparison = _get(db, live=live)["comparison"]
    assert (comparison["n_2025"], comparison["n_recent"]) == (0, 0)


def test_country_filter_applies_to_both_sides(db):
    now = int(time.time() * 1000)
    live = (_history(4, mag=5.0, country_id="ESP") + _history(6, 10, mag=5.0, country_id="JPN")
            + _recent(1, now, mag=5.0, country_id="ESP") + _recent(2, now, 10, mag=5.0, country_id="JPN")
            + _recent(3, now, 20, mag=5.0))
    esp = _get(db, params={"country_id": "ESP"}, live=live)["comparison"]
    assert (esp["n_2025"], esp["n_recent"]) == (4, 1)
    none = _get(db, params={"country_id": "none"})["comparison"]
    assert (none["n_2025"], none["n_recent"]) == (0, 3)


def test_zero_mean_gives_null_variation(db):
    now = int(time.time() * 1000)
    comparison = _get(db, live=_recent(3, now, mag=5.0))["comparison"]
    assert comparison["n_2025"] == 0 and comparison["daily_mean_2025"] == 0
    assert comparison["diff_abs"] == 3.0 and comparison["variation_pct"] is None


def test_periods_in_milliseconds_and_independent_of_requested_dates(db):
    before = int(time.time() * 1000)
    body = _get(db, params=DAY_RANGE)
    comparison = body["comparison"]
    assert comparison["reference_period"] == REFERENCE
    recent = comparison["recent_period"]
    assert recent["end"] == body["metadata"]["generated"] >= before
    assert recent["end"] - recent["start"] == 24 * MS_PER_HOUR
    assert body["period"] != recent
