"""Modo `replay` de `/api/eventos` con el rol real (T011: F12 parcial, constitución §7)."""
import asyncio

from api.timeutil import parse_iso_to_ms
from tests.support.api_client import api_client, seed_database
from tests.support.api_seed import synthetic_event

PATH = "/api/eventos"
DAY_START = parse_iso_to_ms("2026-11-01T00:00:00")
RANGE = {"start": "2026-11-01", "end": "2026-11-02"}
LAST_RUN_SQL = ("INSERT INTO ingest.ingest_run (run_at, url, status) VALUES "
                "(timestamptz 'epoch' + 7000 * interval '1 millisecond', 'https://example.invalid', 200)")


def _get(db, modes, live=None, replay=None, ingest_run=False):
    """Siembra una vez y consulta cada modo; devuelve las respuestas por modo."""
    async def scenario():
        await seed_database(db, live=live, replay=replay)
        if ingest_run:
            admin = await db.admin()
            try:
                await admin.execute(LAST_RUN_SQL)
            finally:
                await admin.close()
        async with api_client(db) as client:
            return {mode: await client.get(PATH, params={**RANGE, "mode": mode}) for mode in modes}

    return asyncio.run(scenario())


def test_empty_replay_is_200_with_replay_mode(db):
    response = _get(db, ["replay"])["replay"]
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["mode"] == "replay"
    assert body["features"] == [] and body["metadata"]["total"] == 0


def test_event_only_in_replay_appears_only_with_replay(db):
    responses = _get(db, ["replay", "live"], replay=[synthetic_event(1, time_ms=DAY_START)])
    in_replay, in_live = responses["replay"].json(), responses["live"].json()
    assert [f["id"] for f in in_replay["features"]] == ["synthetic-1"]
    assert in_replay["metadata"]["mode"] == "replay"
    assert in_live["features"] == [] and in_live["metadata"]["mode"] == "live"


def test_event_only_in_live_does_not_appear_in_replay(db):
    responses = _get(db, ["replay", "live"], live=[synthetic_event(2, time_ms=DAY_START)])
    assert responses["replay"].json()["features"] == []
    assert [f["id"] for f in responses["live"].json()["features"]] == ["synthetic-2"]


def test_last_ingestion_is_the_live_one_in_both_modes(db):
    responses = _get(db, ["live", "replay"], ingest_run=True)
    assert [r.json()["metadata"]["last_ingestion"] for r in responses.values()] == [7000, 7000]


def test_unknown_mode_is_400(db):
    response = _get(db, ["otro"])["otro"]
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_parameter"
    assert "mode" in response.json()["error"]["message"]
