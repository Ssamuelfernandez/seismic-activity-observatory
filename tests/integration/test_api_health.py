"""`GET /api/salud` con el rol real (T017: F6, FR-011)."""
import asyncio
import time

from tests.support.api_client import api_client

PATH = "/api/salud"
RUN_SQL = ("INSERT INTO ingest.ingest_run (run_at, url, status) VALUES "
           "(timestamptz 'epoch' + 5000 * interval '1 millisecond', 'https://example.invalid', 200)")
FORBIDDEN_FRAGMENTS = ("password", "postgres", "observatory_", "host", "5432")


def _get(db, params=None, with_run=False):
    async def scenario():
        if with_run:
            admin = await db.admin()
            try:
                await admin.execute(RUN_SQL)
            finally:
                await admin.close()
        async with api_client(db) as client:
            return await client.get(PATH, params=params)
    return asyncio.run(scenario())


def test_health_without_ingestions_has_null_last_ingestion(db):
    before = int(time.time() * 1000)
    response = _get(db)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"status", "last_ingestion", "generated"}
    assert body["status"] == "ok" and body["last_ingestion"] is None
    assert isinstance(body["generated"], int) and before <= body["generated"] <= int(time.time() * 1000)


def test_health_with_successful_run_returns_its_time_in_ms(db):
    body = _get(db, with_run=True).json()
    assert body["status"] == "ok" and body["last_ingestion"] == 5000


def test_health_ignores_mode_and_other_params(db):
    body = _get(db, params={"mode": "replay", "min_mag": "abc", "foo": "1"}, with_run=True).json()
    assert body["status"] == "ok" and body["last_ingestion"] == 5000


def test_health_does_not_leak_connection_data(db):
    text = _get(db).text.lower()
    assert not any(fragment in text for fragment in FORBIDDEN_FRAGMENTS)
    assert db.api_password.lower() not in text
