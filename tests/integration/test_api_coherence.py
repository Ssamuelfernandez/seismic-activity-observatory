"""Coherencia entre `/api/eventos` y `/api/estadisticas` con los mismos filtros (T015: F7, SC-003, FR-010)."""
import asyncio

import pytest

from api.timeutil import MS_PER_HOUR, parse_iso_to_ms
from tests.support.api_client import api_client, seed_database
from tests.support.api_seed import synthetic_event

COUNTRIES = {"ESP": "España", "JPN": "Japón"}
DAY_START = parse_iso_to_ms("2026-11-01")
DAY = {"start": "2026-11-01", "end": "2026-11-02"}
COMBINATIONS = {
    "min_mag": {**DAY, "min_mag": "2"},
    "country": {**DAY, "country_id": "esp"},
    "none": {**DAY, "country_id": "none"},
    "range": {"start": "2026-11-01T02:30:00", "end": "2026-11-01T09:00:00"},
    "combined": {"start": "2026-11-01T01:00:00", "end": "2026-11-01T20:00:00", "min_mag": "0", "country_id": "JPN"},
}


def _events():
    kinds = [(2.5, 8.0, "ESP"), (None, None, None), (-1.0, -2.0, "JPN"), (5.5, 120.0, None), (0.0, 300.0, "JPN"),
             (3.0, None, "ESP"), (7.2, 9.99, "JPN"), (1.0, 35.0, None)]
    return [synthetic_event(number, time_ms=DAY_START + (number * 7 // 3) * MS_PER_HOUR // 2 + number,
                            mag=mag, depth_km=depth, country_id=country)
            for number, (mag, depth, country) in enumerate(kinds * 3, start=1)]


async def _both(db, params):
    async with api_client(db) as client:
        events = (await client.get("/api/eventos", params=params)).json()
        stats = (await client.get("/api/estadisticas", params=params)).json()
    return events, stats


@pytest.mark.parametrize("name", list(COMBINATIONS))
def test_stats_and_events_agree(db, name):
    params = COMBINATIONS[name]
    asyncio.run(seed_database(db, live=_events(), countries=COUNTRIES))
    events, stats = asyncio.run(_both(db, params))
    total = events["metadata"]["total"]
    assert stats["total"] == total
    assert sum(b["count"] for b in stats["by_hour"]["buckets"]) == total
    assert sum(i["count"] for i in stats["by_country"]["items"]) == total
    depth = stats["histograms"]["depth"]
    assert sum(b["count"] for b in depth["bins"]) + depth["no_value"] == total
    magnitude = stats["histograms"]["magnitude"]
    bins_sum = sum(b["count"] for b in magnitude["bins"])
    if "min_mag" in params:
        assert bins_sum == total
        assert magnitude["no_value"] == events["metadata"]["null_mag_excluded"]
    else:
        assert bins_sum == total - magnitude["no_value"]
    assert total > 0 or name == "none"
