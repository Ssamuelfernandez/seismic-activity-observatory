"""Fallos de USGS con PostgreSQL real y el mock: error registrado, nada publicado, estado intacto (T012).

Todos los eventos son sintéticos (`synthetic-...`) y viven en la base temporal de la sesión.
"""
import asyncio

import pytest

from common.backoff import BackoffSettings
from producer.cycle import STATUS_FETCH_ERROR, STATUS_OK, run_cycle
from tests.support.mock_usgs import MODE_429, MODE_500, MODE_NO_FEATURES, MODE_NOT_JSON, MODE_OK, MODE_SLOW, synthetic_feature
from tests.support.producer_harness import (
    RecordingPublisher, cycle, feed_settings, make_deps, run_with_pool, scalar, snapshot,
)
from tests.support.temp_database import TempDatabase

# modo del mock -> (estado HTTP registrado, comienzo del texto de error)
CASES = {
    MODE_500: (500, "HTTP 500"),
    MODE_429: (429, "HTTP 429"),
    MODE_SLOW: (None, "timeout"),
    MODE_NOT_JSON: (200, "invalid_body: "),
    MODE_NO_FEATURES: (200, "invalid_body: "),
}


@pytest.mark.parametrize("mode", list(CASES))
def test_usgs_failure_logs_error_and_leaves_state_untouched(db: TempDatabase, mock_usgs, mode: str) -> None:
    mock_usgs.features = [synthetic_feature(1), synthetic_feature(2, event_type="quarry blast")]
    publisher = RecordingPublisher()

    async def scenario(pool):
        deps = make_deps(pool, publisher)
        first = await cycle(deps, mock_usgs.url)
        before = await snapshot(db)
        runs_before = await scalar(db, "SELECT count(*) FROM ingest.ingest_run")
        mock_usgs.mode = mode
        failed = await cycle(deps, mock_usgs.url)
        after = await snapshot(db)
        runs_after = await scalar(db, "SELECT count(*) FROM ingest.ingest_run")
        mock_usgs.mode = MODE_OK
        mock_usgs.features = [synthetic_feature(1, updated=2_000)]
        recovered = await cycle(deps, mock_usgs.url)
        return first, failed, recovered, before, after, runs_after - runs_before

    first, failed, recovered, before, after, new_runs = run_with_pool(db, scenario)
    assert first.status == STATUS_OK and first.published == 1
    assert failed.status == STATUS_FETCH_ERROR and failed.published == 0
    assert before == after and new_runs == 1
    assert len(publisher.sent) == 2 and recovered.published == 1  # el 1.º ciclo y el posterior a la recuperación
    status, error = asyncio.run(_last_failure(db))
    assert (status, error.startswith(CASES[mode][1])) == (CASES[mode][0], True)


async def _last_failure(db: TempDatabase) -> tuple:
    conn = await db.admin()
    try:
        row = await conn.fetchrow("SELECT status, error, sha256, event_count FROM ingest.ingest_run "
                                  "WHERE error IS NOT NULL ORDER BY id DESC LIMIT 1")
        assert row["sha256"] is None and row["event_count"] is None
        return row["status"], row["error"]
    finally:
        await conn.close()


def test_loop_recovers_with_millisecond_backoff(db: TempDatabase, mock_usgs) -> None:
    """Dos ciclos fallidos con espera de milisegundos y luego el mock responde: el siguiente ciclo publica."""
    from producer.loop import run_loop
    mock_usgs.features = [synthetic_feature(1)]
    mock_usgs.mode = MODE_500
    publisher = RecordingPublisher()
    waits: list[float] = []

    async def scenario(pool):
        deps = make_deps(pool, publisher)
        results = []

        async def run_one():
            result = await run_cycle(deps, feed_settings(mock_usgs.url))
            results.append(result)
            if len(results) == 2:
                mock_usgs.mode = MODE_OK
            return result

        async def sleep(seconds):
            waits.append(seconds)
            await asyncio.sleep(seconds)

        await run_loop(run_one, lambda: None, sleep, 0.01, BackoffSettings(0.001, 0.004),
                       jitter=lambda: 1.0, max_cycles=3)
        return results

    results = run_with_pool(db, scenario)
    assert [r.status for r in results] == [STATUS_FETCH_ERROR, STATUS_FETCH_ERROR, STATUS_OK]
    assert waits == [0.001, 0.002, 0.01] and len(publisher.sent) == 1
