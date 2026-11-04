"""`write_event` con conexión y transacción de mentira: estado inconsistente (T034)."""
import asyncio
import logging
from datetime import datetime, timezone

from common.decode import decode_value
from common.records import MessageRef, ValidEvent, VersionOutcome
from common.transform import build_event_rows
from common.validation import validate_message
from consumer.writer import write_event
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message, to_bytes

REF = MessageRef("earthquakes.live", 0, 3)
NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
INSERTED = "INSERT 0 1"
NOT_INSERTED = "INSERT 0 0"


class FakeTransaction:
    """Transacción de mentira: no hace nada al entrar ni al salir."""

    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, *exc_info) -> None:
        return None


class FakeConnection:
    """Conexión de mentira: `fetchval` devuelve valores fijados y `execute` etiquetas de estado."""

    def __init__(self, stored_updated_ms: int | None, version_tag: str) -> None:
        self.stored_updated_ms = stored_updated_ms
        self.version_tag = version_tag
        self.statements: list[str] = []

    def transaction(self, **kwargs) -> FakeTransaction:
        return FakeTransaction()

    async def fetchval(self, sql: str, *args):
        self.statements.append(sql)
        return self.stored_updated_ms if "FOR UPDATE" in sql else False

    async def execute(self, sql: str, *args) -> str:
        self.statements.append(sql)
        return self.version_tag if "event_version" in sql else INSERTED


def _rows():
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    valid = validate_message(decode_value(to_bytes(message)), "earthquakes.live")
    assert isinstance(valid, ValidEvent)
    return build_event_rows(valid, REF, NOW)


def test_inconsistent_state_logs_warning_and_returns_late_old(caplog) -> None:
    connection = FakeConnection(stored_updated_ms=E1_UPDATED_1005, version_tag=INSERTED)
    with caplog.at_level(logging.WARNING):
        outcome = asyncio.run(write_event(connection, _rows(), "live"))
    assert outcome is VersionOutcome.LATE_OLD_VERSION
    assert f"inconsistent_state event_id={FAQ12_E1}" in caplog.text
    assert not any("current_event" in s and "DO UPDATE" in s for s in connection.statements)


def test_consistent_state_has_no_warning(caplog) -> None:
    connection = FakeConnection(stored_updated_ms=None, version_tag=INSERTED)
    with caplog.at_level(logging.WARNING):
        outcome = asyncio.run(write_event(connection, _rows(), "live"))
    assert outcome is VersionOutcome.NEW_EVENT
    assert "inconsistent_state" not in caplog.text
