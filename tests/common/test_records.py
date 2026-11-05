"""Pruebas de las estructuras inmutables de `common/records.py` (T013)."""
import dataclasses
from datetime import datetime, timezone

import pytest

from common.records import (
    DecodeResult,
    kafka_columns,
    EventRows,
    DateRow,
    MessageRef,
    ProcessingResult,
    RawRecord,
    Rejection,
    ResultKind,
    VersionOutcome,
)


def test_message_ref_is_immutable() -> None:
    ref = MessageRef("earthquakes.live", 0, 5)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.offset = 6  # type: ignore[misc]


def test_rejection_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        Rejection("invalid_json").reason = "otro"  # type: ignore[misc]


def test_decode_result_is_immutable_and_raw_is_bytes() -> None:
    decoded = DecodeResult(raw=b"", obj=None, ok=False)
    assert isinstance(decoded.raw, bytes)
    with pytest.raises(dataclasses.FrozenInstanceError):
        decoded.ok = True  # type: ignore[misc]


def test_processing_result_is_immutable_with_optional_event_id() -> None:
    ref = MessageRef("earthquakes.live", 0, 1)
    result = ProcessingResult(kind=ResultKind.QUARANTINE, ref=ref, reason="invalid_json")
    assert result.event_id is None and result.updated_ms is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.converted = True  # type: ignore[misc]


def test_version_outcome_has_exactly_five_members() -> None:
    assert {m.name for m in VersionOutcome} == {
        "NEW_EVENT",
        "NEWER_VERSION",
        "LATE_OLD_VERSION",
        "REDELIVERY",
        "SAME_UPDATED_CONFLICT",
    }
    assert len(VersionOutcome) == 5


def test_raw_record_exposes_ref() -> None:
    record = RawRecord("earthquakes.replay", 0, 9, b"k", b"v")
    assert record.ref == MessageRef("earthquakes.replay", 0, 9)


def test_event_rows_envelope_properties_come_from_current() -> None:
    now = datetime(2026, 11, 4, tzinfo=timezone.utc)
    rows = EventRows(
        current={"source": "replay_demo", "ingested_at": now, "replay_at": None, "is_synthetic": True},
        version={},
        date=DateRow(now.date(), 2026, 11, 4, 3),
        nulls=(),
        original="{}",
    )
    assert (rows.source, rows.ingested_at, rows.replay_at, rows.is_synthetic) == (
        "replay_demo",
        now,
        None,
        True,
    )


def test_kafka_columns_copies_a_real_reference() -> None:
    assert kafka_columns(MessageRef("earthquakes.live", 2, 40)) == ("earthquakes.live", 2, 40)


def test_kafka_columns_is_all_none_for_batch_reference() -> None:
    assert kafka_columns(MessageRef("earthquakes.live", None, None)) == (None, None, None)


def test_raw_record_without_partition_has_batch_reference() -> None:
    record = RawRecord("earthquakes.live", None, None, None, b"v")
    assert record.ref == MessageRef("earthquakes.live", None, None)
