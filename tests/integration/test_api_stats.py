"""`GET /api/estadisticas` con el rol real y el cliente `httpx` (T014: F7, FR-004, FR-009, US3)."""
import asyncio
import json
import time

from api.timeutil import MS_PER_HOUR, parse_iso_to_ms
from tests.support.api_client import request_api
from tests.support.api_seed import synthetic_event

PATH = "/api/estadisticas"
TOP_KEYS = {"metadata", "period", "filters", "total", "by_hour", "by_country", "histograms", "comparison"}
COMPARISON_KEYS = {"unit", "min_mag_applied", "recent_period", "reference_period", "n_recent", "n_2025",
                   "daily_mean_2025", "diff_abs", "variation_pct", "recent_incomplete"}
COUNTRIES = {"ESP": "España", "JPN": "Japón"}
DAY_START = parse_iso_to_ms("2026-11-01")
RANGE = {"start": "2026-11-01", "end": "2026-11-01T03:00:00"}


def _get(db, params=None, live=None, replay=None):
    return asyncio.run(request_api(db, PATH, params=params, live=live, replay=replay, countries=COUNTRIES))


def _events():
    return [synthetic_event(1, time_ms=DAY_START + 10, mag=2.0, depth_km=5.0, country_id="ESP"),
            synthetic_event(2, time_ms=DAY_START + MS_PER_HOUR + 10, mag=None, depth_km=None),
            synthetic_event(3, time_ms=DAY_START + 2 * MS_PER_HOUR + 10, mag=5.0, depth_km=40.0, country_id="JPN")]


def test_full_shape_with_period_and_filters(db):
    response = _get(db, params=RANGE, live=_events())
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    json.dumps(body, allow_nan=False)
    assert set(body) == TOP_KEYS
    assert set(body["metadata"]) == {"generated", "last_ingestion", "mode"} and body["metadata"]["mode"] == "live"
    assert body["period"] == {"start": DAY_START, "end": DAY_START + 3 * MS_PER_HOUR}
    assert body["filters"] == {"min_mag": None, "country_id": None}
    assert body["total"] == 3
    assert [b["count"] for b in body["by_hour"]["buckets"]] == [1, 1, 1]
    assert body["by_country"]["no_value"] == 1 and len(body["by_country"]["items"]) == 3
    assert len(body["histograms"]["magnitude"]["bins"]) == 8 and len(body["histograms"]["depth"]["bins"]) == 5
    assert body["histograms"]["magnitude"]["no_value"] == 1 and body["histograms"]["depth"]["no_value"] == 1
    assert set(body["comparison"]) == COMPARISON_KEYS


def test_default_period_is_last_24_hours_with_zero_hours(db):
    now = int(time.time() * 1000)
    body = _get(db, live=[synthetic_event(1, time_ms=now - MS_PER_HOUR)]).json()
    assert body["period"]["end"] - body["period"]["start"] == 24 * MS_PER_HOUR
    assert body["total"] == 1 and sum(b["count"] for b in body["by_hour"]["buckets"]) == 1
    assert len(body["by_hour"]["buckets"]) in (24, 25)


def test_limit_and_cursor_are_ignored(db):
    body = _get(db, params={**RANGE, "limit": "1", "cursor": "xx"}, live=_events()).json()
    assert body["total"] == 3


def test_filters_are_normalized_in_response(db):
    first = _get(db, params={**RANGE, "country_id": "esp"}, live=_events())
    assert first.json()["filters"]["country_id"] == "ESP"
    assert _get(db, params={**RANGE, "country_id": "NONE"}).json()["filters"]["country_id"] == "none"
    assert _get(db, params={**RANGE, "min_mag": "3"}).json()["filters"] == {"min_mag": 3.0, "country_id": None}


def test_replay_has_null_comparison_and_zeros(db):
    body = _get(db, params={**RANGE, "mode": "replay"}, live=_events()).json()
    assert body["metadata"]["mode"] == "replay" and body["comparison"] is None
    assert body["total"] == 0 and body["by_country"]["items"] == []
    assert all(b["count"] == 0 for b in body["by_hour"]["buckets"])
    assert all(b["count"] == 0 for b in body["histograms"]["magnitude"]["bins"])


def test_replay_reads_only_the_replay_table(db):
    body = _get(db, params={**RANGE, "mode": "replay"}, replay=_events()[:1]).json()
    assert body["total"] == 1


def test_same_400_errors_as_events(db):
    for params in ({"min_mag": "abc"}, {"mode": "otro"}, {"start": "2026-11-02", "end": "2026-11-01"},
                   {"country_id": "ES"}):
        response = _get(db, params=params)
        assert response.status_code == 400 and response.json()["error"]["code"] == "invalid_parameter"
        assert "detail" not in response.json()
