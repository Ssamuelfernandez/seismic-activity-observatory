"""Pruebas del mensaje que construye el cargador (T004, B16, FR-010)."""
import json
from datetime import datetime, timezone

from common.decode import decode_value
from common.records import ValidEvent
from common.validation import validate_message
from historical.envelope import build_message_bytes
from tests.support.messages import build_event

EXTRACTED_AT = datetime(2026, 11, 5, 10, 0, 0, tzinfo=timezone.utc)


def synthetic_feature() -> dict:
    """Feature sintética válida."""
    return build_event("synthetic-hist-1", 1735689600000, 1735689700000, 4.5)


def test_message_fields() -> None:
    feature = synthetic_feature()
    message = json.loads(build_message_bytes(feature, EXTRACTED_AT, is_synthetic=True))
    assert message["source"] == "usgs_historical"
    assert message["mode"] == "live"
    assert message["replay_at"] is None
    assert message["is_synthetic"] is True
    assert message["ingested_at"] == "2026-11-05T10:00:00Z"
    assert message["event"] == feature


def test_is_synthetic_defaults_to_false() -> None:
    message = json.loads(build_message_bytes(synthetic_feature(), EXTRACTED_AT))
    assert message["is_synthetic"] is False


def test_deterministic_bytes() -> None:
    first = build_message_bytes(synthetic_feature(), EXTRACTED_AT, is_synthetic=True)
    second = build_message_bytes(synthetic_feature(), EXTRACTED_AT, is_synthetic=True)
    assert first == second


def test_contract_validation_accepts_it() -> None:
    raw = build_message_bytes(synthetic_feature(), EXTRACTED_AT, is_synthetic=True)
    result = validate_message(decode_value(raw), "earthquakes.live")
    assert isinstance(result, ValidEvent)
