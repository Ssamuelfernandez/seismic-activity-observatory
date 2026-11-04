"""Ciclos, reinicio y reenvío con PostgreSQL real, mock de USGS y la canalización del consumidor (T013).

Todos los eventos son sintéticos (`synthetic-...`) y viven en la base temporal de la sesión.
"""
import asyncio

from producer.cycle import STATUS_DB_ERROR, STATUS_OK
from tests.support.db_helpers import process_message
from tests.support.mock_usgs import synthetic_feature
from tests.support.producer_harness import (
    FlakyMarkStore, RecordingPublisher, cycle, make_deps, run_with_pool, scalar, snapshot,
)
from tests.support.temp_database import TempDatabase

COUNT_CURRENT = "SELECT count(*) FROM live.current_event"
COUNT_VERSION = "SELECT count(*) FROM live.event_version"


def test_second_cycle_with_same_response_publishes_nothing(db: TempDatabase, mock_usgs) -> None:
    mock_usgs.features = [synthetic_feature(n) for n in (1, 2, 3)]
    publisher = RecordingPublisher()

    async def scenario(pool):
        deps = make_deps(pool, publisher)
        return await cycle(deps, mock_usgs.url), await cycle(deps, mock_usgs.url)

    first, second = run_with_pool(db, scenario)
    assert (first.status, first.published) == (STATUS_OK, 3)
    assert (second.published, second.skipped) == (0, 3)
    assert asyncio.run(scalar(db, "SELECT count(*) FROM ingest.raw_response")) == 1
    assert asyncio.run(scalar(db, "SELECT count(*) FROM ingest.ingest_run WHERE status = 200")) == 2


def test_restart_on_same_database_publishes_nothing(db: TempDatabase, mock_usgs) -> None:
    mock_usgs.features = [synthetic_feature(1), synthetic_feature(2)]

    async def run_once(pool):
        return await cycle(make_deps(pool, RecordingPublisher()), mock_usgs.url)

    first = run_with_pool(db, run_once)
    after_restart = run_with_pool(db, run_once)  # pool y ciclo nuevos sobre la misma base
    assert first.published == 2 and after_restart.published == 0 and after_restart.skipped == 2


def test_only_a_greater_updated_is_published(db: TempDatabase, mock_usgs) -> None:
    publisher = RecordingPublisher()

    async def scenario(pool):
        deps = make_deps(pool, publisher)
        counts = []
        for updated in (2_000, 1_000, 2_000, 3_000):
            mock_usgs.features = [synthetic_feature(1, updated=updated)]
            counts.append((await cycle(deps, mock_usgs.url)).published)
        return counts

    assert run_with_pool(db, scenario) == [1, 0, 0, 1]
    assert [m["event"]["properties"]["updated"] for _, m in publisher.sent] == [2_000, 3_000]


def test_cut_between_ack_and_mark_resends_once_and_consumer_is_idempotent(db: TempDatabase, mock_usgs) -> None:
    mock_usgs.features = [synthetic_feature(1)]
    publisher = RecordingPublisher()

    async def scenario(pool):
        flaky = make_deps(pool, publisher, FlakyMarkStore(pool, failures=1))
        cut = await cycle(flaky, mock_usgs.url)
        state_after_cut = (await snapshot(db))["ingest_state"]
        resent = await cycle(make_deps(pool, publisher), mock_usgs.url)
        again = await cycle(make_deps(pool, publisher), mock_usgs.url)
        return cut, state_after_cut, resent, again

    cut, state_after_cut, resent, again = run_with_pool(db, scenario)
    assert cut.status == STATUS_DB_ERROR and state_after_cut == []
    assert resent.published == 1 and again.published == 0
    assert len(publisher.sent) == 2 and publisher.sent[0] == publisher.sent[1]
    assert asyncio.run(_through_consumer(db, publisher)) == ((1, 1), (1, 1))


async def _through_consumer(db: TempDatabase, publisher: RecordingPublisher) -> tuple:
    """Pasa los dos mensajes por la canalización del consumidor; devuelve los recuentos tras cada uno."""
    conn = await db.consumer()
    try:
        counts = []
        for offset, (_, message) in enumerate(publisher.sent):
            await process_message(conn, message, offset)
            counts.append((await conn.fetchval(COUNT_CURRENT), await conn.fetchval(COUNT_VERSION)))
        return tuple(counts)
    finally:
        await conn.close()
