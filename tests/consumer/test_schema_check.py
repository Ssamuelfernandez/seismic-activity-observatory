"""`ensure_schema_ready` con un pool de mentira: tablas presentes o ausentes (T006, FR-008)."""
import asyncio

import pytest

from consumer.schema_check import REQUIRED_TABLES, SchemaNotReadyError, ensure_schema_ready


class FakePool:
    """Pool de mentira: `fetchval` devuelve NULL (None) para las tablas ausentes."""

    def __init__(self, missing: str | None = None) -> None:
        self.missing = missing
        self.asked: list[str] = []

    async def fetchval(self, sql: str, table: str):
        self.asked.append(table)
        return None if table == self.missing else table


def test_required_tables_are_the_eight_of_the_consumer() -> None:
    assert set(REQUIRED_TABLES) == {
        "public.country", "public.date_dim", "live.current_event", "live.event_version",
        "live.quarantine", "replay.current_event", "replay.event_version", "replay.quarantine",
    }


@pytest.mark.parametrize("missing", REQUIRED_TABLES)
def test_missing_table_raises_with_its_name(missing: str) -> None:
    with pytest.raises(SchemaNotReadyError, match=missing.replace(".", r"\.")):
        asyncio.run(ensure_schema_ready(FakePool(missing)))


def test_all_tables_present_does_not_raise() -> None:
    pool = FakePool()
    asyncio.run(ensure_schema_ready(pool))
    assert pool.asked == list(REQUIRED_TABLES)
