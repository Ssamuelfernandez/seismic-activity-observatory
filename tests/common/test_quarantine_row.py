"""Pruebas de `build_quarantine_row` (T026)."""
import hashlib
import json
import re
from datetime import datetime, timezone

import pytest

from common.decode import decode_value
from common.quarantine_row import build_quarantine_row
from common.records import MessageRef
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message, to_bytes

REF = MessageRef("earthquakes.live", 0, 12)
NOW = datetime(2026, 11, 5, 9, 0, 0, tzinfo=timezone.utc)
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _row(raw: bytes | None, reason: str = "invalid_json"):
    decoded = decode_value(raw)
    return build_quarantine_row(decoded, reason, REF, NOW), decoded


def _message() -> dict:
    return build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)


def test_sha256_is_hash_of_received_bytes() -> None:
    raw = to_bytes(_message())
    row, _ = _row(raw, "coordinates_out_of_range")
    assert row.original_sha256 == hashlib.sha256(raw).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", row.original_sha256)


def test_sha256_for_invalid_json_uses_raw_bytes() -> None:
    raw = b"{no json"
    row, _ = _row(raw)
    assert row.original_sha256 == hashlib.sha256(raw).hexdigest()
    assert row.original is None
    assert row.raw_text == "{no json"


@pytest.mark.parametrize("raw", [None, b""])
def test_tombstone_and_empty(raw: bytes | None) -> None:
    row, _ = _row(raw)
    assert row.reason == "invalid_json"
    assert row.raw_text == ""
    assert row.original is None
    assert row.original_sha256 == EMPTY_SHA256


def test_original_is_whole_envelope_when_storable() -> None:
    message = _message()
    row, _ = _row(to_bytes(message), "mag_out_of_range")
    assert json.loads(row.original) == message
    assert row.raw_text is None


def test_unstorable_envelope_goes_to_raw_text() -> None:
    raw = b'{"source":"replay_demo","event":{"id":"x","dmin":NaN}}'
    row, _ = _row(raw, "db_constraint_violation")
    assert row.original is None
    assert row.raw_text == raw.decode()


def test_never_both_none_and_never_both_set() -> None:
    for raw in (None, b"\xff", b"[]", b"null", b'{"a":"\\u0000"}', to_bytes(_message())):
        row, _ = _row(raw)
        assert (row.original is None) != (row.raw_text is None)


def test_invalid_utf8_is_sanitized() -> None:
    row, _ = _row(b"\xff\x00")
    assert row.raw_text == "\\xff\\x00"


def test_json_that_is_not_object_keeps_original_text() -> None:
    row, _ = _row(b"[]", "invalid_envelope")
    assert row.original == "[]"
    assert row.event_id is None and row.source is None and row.is_synthetic is False


def test_copy_rule_valid_values() -> None:
    row, _ = _row(to_bytes(_message()), "mag_out_of_range")
    assert row.event_id == FAQ12_E1
    assert row.source == "replay_demo"
    assert row.is_synthetic is True


@pytest.mark.parametrize("source", ["otro", 5, None, ["usgs_feed"]])
def test_source_not_allowed_is_none(source: object) -> None:
    message = _message()
    message["source"] = source
    row, _ = _row(to_bytes(message), "invalid_envelope")
    assert row.source is None


@pytest.mark.parametrize("source", ["usgs_feed", "usgs_historical", "replay_demo"])
def test_source_allowed_is_copied(source: str) -> None:
    message = _message()
    message["source"] = source
    row, _ = _row(to_bytes(message), "invalid_envelope")
    assert row.source == source


@pytest.mark.parametrize("event_id", [12345, True, None, ["a"], "a\u0000b", "\ud800", "x" * 513])
def test_event_id_not_copied_when_not_safe(event_id: object) -> None:
    message = _message()
    message["event"]["id"] = event_id
    raw = json.dumps(message).encode()
    row, _ = _row(raw, "invalid_field_type")
    assert row.event_id is None


def test_event_id_of_512_chars_is_copied() -> None:
    message = _message()
    message["event"]["id"] = "x" * 512
    row, _ = _row(to_bytes(message), "mag_out_of_range")
    assert row.event_id == "x" * 512


def test_event_id_is_not_escaped() -> None:
    message = _message()
    message["event"]["id"] = "ñandú-1"
    row, _ = _row(to_bytes(message), "mag_out_of_range")
    assert row.event_id == "ñandú-1"


def test_event_missing_or_not_object_gives_no_event_id() -> None:
    message = _message()
    message["event"] = "texto"
    row, _ = _row(to_bytes(message), "invalid_envelope")
    assert row.event_id is None


@pytest.mark.parametrize("value", [1, "true", None, "x"])
def test_is_synthetic_must_be_exact_bool(value: object) -> None:
    message = _message()
    message["is_synthetic"] = value
    row, _ = _row(to_bytes(message), "invalid_envelope")
    assert row.is_synthetic is False


def test_is_synthetic_false_is_kept() -> None:
    message = _message()
    message["is_synthetic"] = False
    row, _ = _row(to_bytes(message), "mag_out_of_range")
    assert row.is_synthetic is False


def test_kafka_reference_and_received_at() -> None:
    row, _ = _row(to_bytes(_message()), "mag_out_of_range")
    assert (row.kafka_topic, row.kafka_partition, row.kafka_offset) == ("earthquakes.live", 0, 12)
    assert row.received_at == NOW


def test_reason_never_comes_from_message() -> None:
    message = _message()
    message["reason"] = "inventado"
    row, _ = _row(to_bytes(message), "mag_out_of_range")
    assert row.reason == "mag_out_of_range"


def test_nul_in_json_escape_sequence_is_kept_as_is() -> None:
    # \u0000 escrito como 6 caracteres ASCII dentro de texto roto: se conserva tal cual
    row, _ = _row(b'{"a":"\\u0000" ')
    assert row.raw_text == '{"a":"\\u0000" '
