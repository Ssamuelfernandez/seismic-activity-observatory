"""Un tipo distinto de `earthquake` no se publica y queda en `live.exclusion` (T018, decisión D8).

Reutiliza el mock de USGS y el arnés del productor. Los eventos son sintéticos (`synthetic-...`);
el consumidor no cambia: la exclusión ocurre antes de Kafka.
"""
from tests.support import evidence
from tests.support.mock_usgs import synthetic_feature
from tests.support.producer_harness import RecordingPublisher, cycle, make_deps, run_with_pool
from tests.support.temp_database import TempDatabase

EXCLUSION_SQL = ("SELECT event_id, updated_ms, kind, reason, observed_type, is_synthetic "
                 "FROM live.exclusion ORDER BY event_id")
EVIDENCE_NAME = "geografia_no_earthquake"
BLAST = "quarry blast"


async def _exclusions(db: TempDatabase) -> list[tuple]:
    conn = await db.admin()
    try:
        return await evidence.record_query(conn, EVIDENCE_NAME, EXCLUSION_SQL,
                                           label="exclusión del tipo distinto de earthquake")
    finally:
        await conn.close()


def test_non_earthquake_is_excluded_and_not_published(db: TempDatabase, mock_usgs) -> None:
    mock_usgs.features = [synthetic_feature(1, event_type=BLAST), synthetic_feature(2)]
    publisher = RecordingPublisher()

    async def scenario(pool):
        result = await cycle(make_deps(pool, publisher), mock_usgs.url)
        return result, await _exclusions(db)

    result, rows = run_with_pool(db, scenario)
    assert result.published == 1 and [key for key, _ in publisher.sent] == ["synthetic-2"]
    assert len(rows) == 1
    event_id, _, _, _, observed_type, _ = rows[0]
    assert (event_id, observed_type) == ("synthetic-1", BLAST)
