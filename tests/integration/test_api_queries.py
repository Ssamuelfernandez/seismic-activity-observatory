"""Consultas de eventos con el rol real `observatory_api` (T008: F1, F3, F4, F11, FR-002, FR-005, FR-006)."""
import asyncio

from api.cursor import CursorPosition
from api.db_access import read_transaction
from api.params import QueryFilters
from api.queries import fetch_counts, fetch_events_page, fetch_last_ingestion_ms
from tests.support.api_client import seed_database
from tests.support.api_seed import BASE_TIME_MS, synthetic_event
from tests.support.temp_database import TempDatabase

START = BASE_TIME_MS
END = BASE_TIME_MS + 10_000
TIMEOUT_SECONDS = 5
BIG_LIMIT = 100


def _filters(**overrides) -> QueryFilters:
    values = {"start_ms": START, "end_ms": END, "min_mag": None, "country_id": None, "mode": "live"}
    values.update(overrides)
    return QueryFilters(**values)


async def _query(db: TempDatabase, filters: QueryFilters, cursor=None, limit=BIG_LIMIT):
    pool = await db.api_pool()
    try:
        async with read_transaction(pool, TIMEOUT_SECONDS) as conn:
            counts = await fetch_counts(conn, filters)
            rows, has_more = await fetch_events_page(conn, filters, cursor, limit)
        return counts, [row["event_id"] for row in rows], has_more
    finally:
        await pool.close()


def _ids(db, events, filters, **kwargs):
    asyncio.run(seed_database(db, live=events, countries={"ESP": "España"}))
    return asyncio.run(_query(db, filters, **kwargs))


def test_range_is_inclusive_at_start_and_exclusive_at_end(db):
    events = [synthetic_event(1, time_ms=START - 1), synthetic_event(2, time_ms=START),
              synthetic_event(3, time_ms=END - 1), synthetic_event(4, time_ms=END)]
    counts, ids, _ = _ids(db, events, _filters())
    assert ids == ["synthetic-3", "synthetic-2"]
    assert counts.total == 2


def test_min_mag_excludes_null_and_counts_it_apart(db):
    events = [synthetic_event(1, mag=3.0, time_ms=START), synthetic_event(2, mag=-0.5, time_ms=START + 1),
              synthetic_event(3, mag=None, time_ms=START + 2), synthetic_event(4, mag=1.0, time_ms=START + 3)]
    counts, ids, _ = _ids(db, events, _filters(min_mag=1.0))
    assert ids == ["synthetic-4", "synthetic-1"]
    assert (counts.total, counts.null_count) == (2, 1)


def test_min_mag_negative_keeps_negative_magnitudes(db):
    events = [synthetic_event(1, mag=-0.5, time_ms=START), synthetic_event(2, mag=-2.0, time_ms=START + 1),
              synthetic_event(3, mag=None, time_ms=START + 2)]
    counts, ids, _ = _ids(db, events, _filters(min_mag=-1.0))
    assert ids == ["synthetic-1"]
    assert (counts.total, counts.null_count) == (1, 1)


def test_without_min_mag_nulls_are_included_and_total_counts_all(db):
    events = [synthetic_event(1, mag=None, time_ms=START), synthetic_event(2, mag=2.0, time_ms=START + 1)]
    counts, ids, _ = _ids(db, events, _filters())
    assert len(ids) == 2 and counts.total == 2 and counts.null_count == 1


def test_country_filter_and_none(db):
    events = [synthetic_event(1, country_id="ESP", time_ms=START), synthetic_event(2, time_ms=START + 1),
              synthetic_event(3, country_id="ESP", time_ms=START + 2)]
    _, esp_ids, _ = _ids(db, events, _filters(country_id="ESP"))
    assert esp_ids == ["synthetic-3", "synthetic-1"]
    counts, ids, _ = asyncio.run(_query(db, _filters(country_id="none")))
    assert ids == ["synthetic-2"] and counts.total == 1
    counts, ids, _ = asyncio.run(_query(db, _filters(country_id="ZZZ")))
    assert ids == [] and counts.total == 0


def test_revision_appears_once_with_new_data(db):
    asyncio.run(seed_database(db, live=[synthetic_event(1, mag=2.0, time_ms=START, updated_ms=START + 10)]))

    async def revise():
        admin = await db.admin()
        try:
            await admin.execute(
                "UPDATE live.current_event SET mag = 3.5, updated_ms = $1, "
                "updated_at = timestamptz 'epoch' + $1::bigint * interval '1 millisecond' "
                "WHERE event_id = 'synthetic-1'", START + 500)
        finally:
            await admin.close()

    asyncio.run(revise())
    counts, ids, _ = asyncio.run(_query(db, _filters()))
    assert ids == ["synthetic-1"] and counts.total == 1


def test_order_is_time_then_id_descending(db):
    events = [synthetic_event(1, time_ms=START + 5), synthetic_event(2, time_ms=START + 5),
              synthetic_event(3, time_ms=START + 9), synthetic_event(4, time_ms=START + 1)]
    _, ids, _ = _ids(db, events, _filters())
    assert ids == ["synthetic-3", "synthetic-2", "synthetic-1", "synthetic-4"]


def test_limit_and_has_more_and_cursor_resume(db):
    events = [synthetic_event(number, time_ms=START + number) for number in range(1, 6)]
    _, ids, has_more = _ids(db, events, _filters(), limit=2)
    assert ids == ["synthetic-5", "synthetic-4"] and has_more is True
    cursor = CursorPosition(START + 4, "synthetic-4")
    _, ids, has_more = asyncio.run(_query(db, _filters(), cursor=cursor, limit=10))
    assert ids == ["synthetic-3", "synthetic-2", "synthetic-1"] and has_more is False


def test_page_row_carries_country_name_and_nulls(db):
    events = [synthetic_event(1, country_id="ESP", time_ms=START),
              synthetic_event(2, mag=None, depth_km=None, time_ms=START + 1)]
    asyncio.run(seed_database(db, live=events, countries={"ESP": "España"}))

    async def rows():
        pool = await db.api_pool()
        try:
            async with read_transaction(pool, TIMEOUT_SECONDS) as conn:
                return (await fetch_events_page(conn, _filters(), None, BIG_LIMIT))[0]
        finally:
            await pool.close()

    page = asyncio.run(rows())
    assert page[0]["event_id"] == "synthetic-2" and page[0]["country_name"] is None
    assert page[0]["mag"] is None and page[0]["depth_km"] is None
    assert page[1]["country_name"] == "España" and page[1]["is_synthetic"] is True


def test_last_ingestion_is_none_then_last_successful_run(db):
    async def scenario():
        pool = await db.api_pool()
        try:
            async with read_transaction(pool, TIMEOUT_SECONDS) as conn:
                before = await fetch_last_ingestion_ms(conn)
        finally:
            await pool.close()
        admin = await db.admin()
        try:
            await admin.execute(
                "INSERT INTO ingest.ingest_run (run_at, url, status) VALUES "
                "(timestamptz 'epoch' + 1000 * interval '1 millisecond', 'https://example.invalid', 200), "
                "(timestamptz 'epoch' + 9000 * interval '1 millisecond', 'https://example.invalid', 500)")
        finally:
            await admin.close()
        pool = await db.api_pool()
        try:
            async with read_transaction(pool, TIMEOUT_SECONDS) as conn:
                return before, await fetch_last_ingestion_ms(conn)
        finally:
            await pool.close()

    assert asyncio.run(scenario()) == (None, 1000)
