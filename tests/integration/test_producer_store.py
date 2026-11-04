"""Almacén de ingesta del productor con PostgreSQL real y el rol `observatory_producer` (T008).

Todos los datos son sintéticos (`synthetic-...`) y viven en la base temporal de la sesión.
"""
import asyncio
import json
from datetime import datetime, timedelta, timezone

from common.ingest_decision import build_exclusion_row
from common.usgs_feed import hash_features
from producer import ingest_store as store
from producer.usgs_client import FeedResponse
from tests.support.mock_usgs import synthetic_feature
from tests.support.temp_database import TempDatabase

URL = "http://mock.invalid/feed.geojson"
NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
FEATURES = [synthetic_feature(1), synthetic_feature(2)]


def _response(features: list[dict], generated: int = 1) -> FeedResponse:
    body = json.dumps({"metadata": {"generated": generated}, "features": features}).encode("utf-8")
    return FeedResponse(200, body, 25, NOW)


async def _scalar(db: TempDatabase, sql: str, *args):
    conn = await db.admin()
    try:
        return await conn.fetchval(sql, *args)
    finally:
        await conn.close()


def _run(db: TempDatabase, scenario):
    """Ejecuta `scenario(pool)` con un pool del rol del productor."""
    async def main():
        pool = await db.producer_pool()
        try:
            return await scenario(pool)
        finally:
            await pool.close()
    return asyncio.run(main())


def test_same_hash_twice_keeps_one_raw_and_two_runs(db: TempDatabase) -> None:
    sha = hash_features(FEATURES)

    async def scenario(pool):
        first = await store.record_success(pool, URL, _response(FEATURES, 1), len(FEATURES), sha)
        second = await store.record_success(pool, URL, _response(FEATURES, 2), len(FEATURES), sha)
        return first, second

    assert _run(db, scenario) == (True, False)
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM ingest.ingest_run WHERE status = 200")) == 2
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM ingest.raw_response")) == 1


def test_different_hash_adds_raw_response(db: TempDatabase) -> None:
    changed = [synthetic_feature(1), synthetic_feature(2, updated=2_000)]

    async def scenario(pool):
        await store.record_success(pool, URL, _response(FEATURES), 2, hash_features(FEATURES))
        await store.record_success(pool, URL, _response(changed), 2, hash_features(changed))

    _run(db, scenario)
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM ingest.raw_response")) == 2


def test_failure_leaves_status_and_hash_null_and_is_not_reference(db: TempDatabase) -> None:
    sha = hash_features(FEATURES)

    async def scenario(pool):
        await store.record_failure(pool, URL, NOW, None, 10_000, "timeout")
        before_any = await store.last_ok_hash(pool)
        await store.record_success(pool, URL, _response(FEATURES), 2, sha)
        await store.record_failure(pool, URL, NOW + timedelta(minutes=1), 429, 30, "HTTP 429")
        return before_any, await store.last_ok_hash(pool)

    before_any, after = _run(db, scenario)
    assert before_any is None and after == sha
    row = asyncio.run(_scalar(db, "SELECT row(status, sha256, error) FROM ingest.ingest_run "
                                  "WHERE error = 'timeout'"))
    assert row == (None, None, "timeout")
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM ingest.ingest_run")) == 3


def test_repeated_exclusion_leaves_one_row(db: TempDatabase) -> None:
    rows = [build_exclusion_row(synthetic_feature(9, event_type="quarry blast"), NOW)]

    async def scenario(pool):
        await store.insert_exclusions(pool, rows)
        await store.insert_exclusions(pool, rows)
        await store.insert_exclusions(pool, [])

    _run(db, scenario)
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM live.exclusion")) == 1
    assert asyncio.run(_scalar(db, "SELECT observed_type FROM live.exclusion")) == "quarry blast"


def test_mark_published_never_goes_backwards(db: TempDatabase) -> None:
    async def scenario(pool):
        await store.mark_published(pool, "synthetic-1", 2_000, NOW)
        await store.mark_published(pool, "synthetic-1", 1_000, NOW + timedelta(minutes=1))
        first = await store.load_state(pool, ["synthetic-1", "synthetic-2"])
        await store.mark_published(pool, "synthetic-1", 3_000, NOW + timedelta(minutes=2))
        return first, await store.load_state(pool, ["synthetic-1"])

    first, second = _run(db, scenario)
    assert first == {"synthetic-1": 2_000}
    assert second == {"synthetic-1": 3_000}


async def _insert_raw(db: TempDatabase, ages_days: list[int]) -> None:
    conn = await db.admin()
    try:
        for index, age in enumerate(ages_days):
            await conn.execute("INSERT INTO ingest.raw_response (fetched_at, sha256, body) "
                               "VALUES (now() - make_interval(days => $1), $2, '{}'::jsonb)",
                               age, f"{index:064x}")
    finally:
        await conn.close()


def test_purge_deletes_old_and_keeps_most_recent(db: TempDatabase) -> None:
    asyncio.run(_insert_raw(db, [30, 10, 8, 1]))  # la última insertada (id mayor) tiene 1 día

    async def scenario(pool):
        return await store.purge_raw_responses(pool, 7)

    assert _run(db, scenario) == 3
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM ingest.raw_response")) == 1


def test_purge_keeps_most_recent_even_if_older_than_retention(db: TempDatabase) -> None:
    asyncio.run(_insert_raw(db, [30, 20, 15]))  # todas fuera de retención

    async def scenario(pool):
        return await store.purge_raw_responses(pool, 7)

    assert _run(db, scenario) == 2
    assert asyncio.run(_scalar(db, "SELECT count(*) FROM ingest.raw_response")) == 1
    assert asyncio.run(_scalar(db, "SELECT sha256 FROM ingest.raw_response")) == f"{2:064x}"
