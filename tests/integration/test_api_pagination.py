"""Paginación por cursor de `/api/eventos` con el rol real (T010: F5, SC-002)."""
import asyncio

from api.timeutil import parse_iso_to_ms
from common.api_config import ApiSettings
from tests.support.api_client import api_client, seed_database
from tests.support.api_seed import synthetic_event
from tests.support.temp_database import TempDatabase

PATH = "/api/eventos"
DAY_START = parse_iso_to_ms("2026-11-01T00:00:00")
RANGE = {"start": "2026-11-01", "end": "2026-11-02"}
EVENT_COUNT = 25
PAGE_SIZE = 10
LOW_MAX = 5


def _events(count=EVENT_COUNT):
    return [synthetic_event(number, time_ms=DAY_START + number * 1000) for number in range(1, count + 1)]


async def _read_pages(client, params):
    pages, cursor = [], None
    while True:
        query = {**params, **({"cursor": cursor} if cursor else {})}
        body = (await client.get(PATH, params=query)).json()
        pages.append(body)
        cursor = body["metadata"]["next_cursor"]
        if cursor is None:
            return pages


def _walk(db, events, params, settings=None):
    async def scenario():
        await seed_database(db, live=events)
        async with api_client(db, settings) as client:
            return await _read_pages(client, params)

    return asyncio.run(scenario())


def _all_ids(pages):
    return [feature["id"] for page in pages for feature in page["features"]]


def test_25_events_in_three_pages(db):
    pages = _walk(db, _events(), {**RANGE, "limit": PAGE_SIZE})
    assert [page["metadata"]["count"] for page in pages] == [10, 10, 5]
    assert all(page["metadata"]["total"] == EVENT_COUNT for page in pages)
    assert all(page["metadata"]["truncated"] is True for page in pages)
    assert [page["metadata"]["next_cursor"] is None for page in pages] == [False, False, True]
    ids = _all_ids(pages)
    assert len(ids) == EVENT_COUNT and len(set(ids)) == EVENT_COUNT
    assert ids == [f"synthetic-{number}" for number in range(EVENT_COUNT, 0, -1)]


def test_same_time_events_are_ordered_by_id(db):
    events = [synthetic_event(number, time_ms=DAY_START) for number in range(1, 8)]
    pages = _walk(db, events, {**RANGE, "limit": 3})
    assert _all_ids(pages) == [f"synthetic-{number}" for number in range(7, 0, -1)]
    assert [page["metadata"]["count"] for page in pages] == [3, 3, 1]


def test_revision_between_pages_does_not_repeat_or_move_events(db):
    async def scenario():
        await seed_database(db, live=_events(12))
        async with api_client(db) as client:
            first = (await client.get(PATH, params={**RANGE, "limit": 6})).json()
            admin = await db.admin()
            try:
                # Revisa un evento ya devuelto y otro de la página siguiente: conservan su `time` e `id`.
                await admin.execute(
                    "UPDATE live.current_event SET mag = 7.7, updated_ms = updated_ms + 5000, "
                    "updated_at = updated_at + interval '5 seconds' "
                    "WHERE event_id IN ('synthetic-12', 'synthetic-4')")
            finally:
                await admin.close()
            cursor = first["metadata"]["next_cursor"]
            second = (await client.get(PATH, params={**RANGE, "limit": 6, "cursor": cursor})).json()
            return first, second

    first, second = asyncio.run(scenario())
    ids = _all_ids([first, second])
    assert ids == [f"synthetic-{number}" for number in range(12, 0, -1)]
    revised = {f["id"]: f["properties"]["mag"] for f in first["features"] + second["features"]}
    # El ya devuelto no se vuelve a enviar (conserva el valor de la página 1); el pendiente llega revisado.
    assert revised["synthetic-12"] == 2.5 and revised["synthetic-4"] == 7.7
    assert second["metadata"]["next_cursor"] is None


def _get_status(db, params, settings=None, events=None):
    async def scenario():
        await seed_database(db, live=events or _events(8))
        async with api_client(db, settings) as client:
            return await client.get(PATH, params=params)

    return asyncio.run(scenario())


def test_limit_above_maximum_is_400(db):
    response = _get_status(db, {**RANGE, "limit": LOW_MAX + 1}, ApiSettings(max_events=LOW_MAX))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_parameter"
    assert "limit" in response.json()["error"]["message"]


def test_limit_zero_is_400(db):
    response = _get_status(db, {**RANGE, "limit": 0})
    assert response.status_code == 400 and response.json()["error"]["code"] == "invalid_parameter"


def test_malformed_cursor_is_400(db):
    response = _get_status(db, {**RANGE, "cursor": "xx"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_cursor"


def test_without_limit_uses_maximum_and_reports_real_total(db):
    response = _get_status(db, RANGE, ApiSettings(max_events=LOW_MAX), events=_events(8))
    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert (metadata["count"], metadata["total"], metadata["truncated"]) == (LOW_MAX, 8, True)
    assert metadata["next_cursor"] is not None


def test_limit_greater_than_total_is_not_truncated(db):
    response = _get_status(db, {**RANGE, "limit": 50}, events=_events(8))
    metadata = response.json()["metadata"]
    assert (metadata["count"], metadata["total"], metadata["truncated"], metadata["next_cursor"]) == (
        8, 8, False, None)
