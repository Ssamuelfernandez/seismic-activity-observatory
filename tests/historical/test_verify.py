"""Pruebas de la verificación de la carga con una conexión de mentira (T012, B14, B17, SC-004)."""
import asyncio

from consumer import queries
from historical.verify import snapshot_fingerprint, verify_load


class FakeConn:
    """Conexión de mentira: responde por texto de sentencia y anota las llamadas."""

    def __init__(self, loaded: int, historical: int = 0) -> None:
        self.counts = {queries.HISTORICAL_LOADED_COUNT: loaded, queries.HISTORICAL_SOURCE_COUNT: historical}
        self.rows = {queries.FINGERPRINT_CURRENT: (5, "aaa"), queries.FINGERPRINT_VERSION: (6, "bbb"),
                    queries.FINGERPRINT_QUARANTINE: (1, "ccc")}
        self.calls: list[tuple] = []

    async def fetchval(self, sql, *args):
        self.calls.append((sql, args))
        return self.counts[sql]

    async def fetchrow(self, sql, *args):
        self.calls.append((sql, args))
        return self.rows[sql]


class FakePool:
    def __init__(self, conn: FakeConn) -> None:
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class Context:
            async def __aenter__(self):
                return conn

            async def __aexit__(self, *exc):
                return False

        return Context()


IDS = [f"synthetic-{n}" for n in range(10)]


def test_formula_unique_minus_quarantine_holds() -> None:
    result = asyncio.run(verify_load(FakePool(FakeConn(loaded=8)), IDS, IDS[:2]))
    assert result.ok is True
    assert (result.unique, result.quarantined, result.expected, result.loaded) == (10, 2, 8, 8)


def test_discrepancy_is_false_and_message_has_both_figures() -> None:
    result = asyncio.run(verify_load(FakePool(FakeConn(loaded=7)), IDS, IDS[:2]))
    assert result.ok is False
    assert "8" in result.message and "7" in result.message


def test_repeated_ids_count_once_and_ids_are_passed_as_a_list() -> None:
    conn = FakeConn(loaded=2)
    result = asyncio.run(verify_load(FakePool(conn), ["synthetic-1", "synthetic-2", "synthetic-1"], []))
    assert result.ok is True and result.unique == 2
    assert isinstance(conn.calls[0][1][0], list)


def test_quarantined_ids_outside_unique_set_are_ignored() -> None:
    result = asyncio.run(verify_load(FakePool(FakeConn(loaded=3)), ["synthetic-1", "synthetic-2", "synthetic-3"],
                                     ["synthetic-other"]))
    assert result.ok is True and result.quarantined == 0


def test_fingerprint_returns_count_and_hash_of_readable_tables() -> None:
    fingerprint = asyncio.run(snapshot_fingerprint(FakePool(FakeConn(0))))
    assert fingerprint == {"current_event": (5, "aaa"), "event_version": (6, "bbb")}
