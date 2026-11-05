"""`GET /api/eventos` con el rol real y el cliente `httpx` (T009: F1, F2, F3, F4, SC-001, SC-006)."""
import asyncio
import json
import time

from api.timeutil import MS_PER_HOUR, parse_iso_to_ms
from tests.support.api_client import api_client, request_api, seed_database
from tests.support.api_seed import synthetic_event

PATH = "/api/eventos"
METADATA_KEYS = {"generated", "last_ingestion", "mode", "count", "total", "truncated", "next_cursor",
                 "null_mag_excluded"}
COUNTRIES = {"ESP": "España", "JPN": "Japón"}
DAY_START = parse_iso_to_ms("2026-11-01T00:00:00")
RANGE = {"start": "2026-11-01", "end": "2026-11-02"}


def _get(db, params=None, live=None, replay=None):
    return asyncio.run(request_api(db, PATH, params=params, live=live, replay=replay, countries=COUNTRIES))


def _ids(response) -> list[str]:
    return [feature["id"] for feature in response.json()["features"]]


def _assert_json_safe(response) -> None:
    json.dumps(response.json(), allow_nan=False)


def test_no_params_returns_only_last_24_hours(db):
    now = int(time.time() * 1000)
    events = [synthetic_event(1, time_ms=now - MS_PER_HOUR), synthetic_event(2, time_ms=now - 23 * MS_PER_HOUR),
              synthetic_event(3, time_ms=now - 25 * MS_PER_HOUR)]
    response = _get(db, live=events)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert set(body["metadata"]) == METADATA_KEYS
    assert _ids(response) == ["synthetic-1", "synthetic-2"]
    metadata = body["metadata"]
    assert (metadata["mode"], metadata["count"], metadata["total"]) == ("live", 2, 2)
    assert (metadata["truncated"], metadata["next_cursor"], metadata["null_mag_excluded"]) == (False, None, 0)
    assert metadata["last_ingestion"] is None and metadata["generated"] >= now
    _assert_json_safe(response)


def test_empty_result_is_a_valid_200(db):
    response = _get(db)
    assert response.status_code == 200
    body = response.json()
    assert body["features"] == []
    metadata = body["metadata"]
    assert (metadata["count"], metadata["total"], metadata["truncated"], metadata["next_cursor"]) == (
        0, 0, False, None)


def _day_events():
    return [synthetic_event(1, time_ms=parse_iso_to_ms("2026-10-31T23:59:59.999")),
            synthetic_event(2, time_ms=parse_iso_to_ms("2026-11-01T00:00:00")),
            synthetic_event(3, time_ms=parse_iso_to_ms("2026-11-01T12:00:00")),
            synthetic_event(4, time_ms=parse_iso_to_ms("2026-11-02T00:00:00"))]


def test_start_and_end_as_dates_mean_midnight_utc(db):
    response = _get(db, RANGE, live=_day_events())
    assert response.status_code == 200
    assert _ids(response) == ["synthetic-3", "synthetic-2"]


def test_start_without_zone_is_utc(db):
    response = _get(db, {"start": "2026-11-01T00:00:00", "end": "2026-11-02T00:00:00"}, live=_day_events())
    assert _ids(response) == ["synthetic-3", "synthetic-2"]


def test_start_with_zone_is_converted(db):
    params = {"start": "2026-11-01T02:00:00+02:00", "end": "2026-11-02T00:00:00Z"}
    response = _get(db, params, live=_day_events())
    assert _ids(response) == ["synthetic-3", "synthetic-2"]


def test_only_end_looks_24_hours_back(db):
    response = _get(db, {"end": "2026-11-02"}, live=_day_events())
    assert _ids(response) == ["synthetic-3", "synthetic-2"]
    assert response.json()["metadata"]["total"] == 2


def _magnitude_events():
    return [synthetic_event(1, mag=3.0, time_ms=DAY_START + 1), synthetic_event(2, mag=0.0, time_ms=DAY_START + 2),
            synthetic_event(3, mag=-0.5, time_ms=DAY_START + 3), synthetic_event(4, mag=None, time_ms=DAY_START + 4)]


def test_min_mag_zero_excludes_negative_and_null_and_counts_the_null(db):
    response = _get(db, {**RANGE, "min_mag": "0"}, live=_magnitude_events())
    assert _ids(response) == ["synthetic-2", "synthetic-1"]
    metadata = response.json()["metadata"]
    assert (metadata["total"], metadata["null_mag_excluded"]) == (2, 1)


def test_min_mag_negative_includes_negative_magnitudes(db):
    response = _get(db, {**RANGE, "min_mag": "-1"}, live=_magnitude_events())
    assert _ids(response) == ["synthetic-3", "synthetic-2", "synthetic-1"]
    assert response.json()["metadata"]["null_mag_excluded"] == 1


def test_without_min_mag_nulls_are_listed_and_not_excluded(db):
    response = _get(db, RANGE, live=_magnitude_events())
    assert len(_ids(response)) == 4
    assert response.json()["metadata"]["null_mag_excluded"] == 0


def _country_events():
    return [synthetic_event(1, country_id="ESP", time_ms=DAY_START + 1), synthetic_event(2, time_ms=DAY_START + 2),
            synthetic_event(3, country_id="JPN", time_ms=DAY_START + 3)]


def test_country_is_case_insensitive(db):
    async def scenario():
        await seed_database(db, live=_country_events(), countries=COUNTRIES)
        async with api_client(db) as client:
            return [await client.get(PATH, params={**RANGE, "country_id": value}) for value in ("esp", "ESP")]

    for response in asyncio.run(scenario()):
        assert _ids(response) == ["synthetic-1"]
        assert response.json()["features"][0]["properties"]["country_name"] == "España"


def test_country_none_selects_events_without_country(db):
    response = _get(db, {**RANGE, "country_id": "none"}, live=_country_events())
    assert _ids(response) == ["synthetic-2"]
    properties = response.json()["features"][0]["properties"]
    assert (properties["country_id"], properties["country_name"]) == (None, None)


def test_unknown_but_valid_country_returns_empty_200(db):
    response = _get(db, {**RANGE, "country_id": "ZZZ"}, live=_country_events())
    assert response.status_code == 200
    assert response.json()["features"] == [] and response.json()["metadata"]["total"] == 0


def test_event_with_null_mag_depth_and_country(db):
    event = synthetic_event(1, mag=None, depth_km=None, mag_type=None, place=None, status=None, url=None,
                            sig=None, time_ms=DAY_START)
    response = _get(db, RANGE, live=[event])
    feature = response.json()["features"][0]
    assert feature["geometry"]["coordinates"][2] is None
    properties = feature["properties"]
    assert all(properties[key] is None for key in ("mag", "magType", "place", "status", "url", "sig",
                                                  "country_id", "country_name"))
    assert properties["is_synthetic"] is True and properties["time"] == DAY_START
    _assert_json_safe(response)


def test_negative_magnitude_and_depth_are_served(db):
    response = _get(db, RANGE, live=[synthetic_event(1, mag=-0.06, depth_km=-0.18, time_ms=DAY_START)])
    feature = response.json()["features"][0]
    assert feature["properties"]["mag"] == -0.06
    assert feature["geometry"]["coordinates"] == [0.0, 0.0, -0.18]


def test_invalid_parameter_is_400_with_common_body(db):
    response = _get(db, {"min_mag": "abc"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_parameter"
