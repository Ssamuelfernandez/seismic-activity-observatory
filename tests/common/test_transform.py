"""Pruebas de `common/transform.py` (T021)."""
import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from common.records import MessageRef, ValidEvent
from common.transform import MAX_EPOCH_MS, MIN_EPOCH_MS, build_event_rows, ms_to_utc
from tests.support.messages import (
    E1_TIME_MS,
    E1_UPDATED_1005,
    FAQ12_E1,
    build_message,
    build_synthetic_message,
)

REF = MessageRef("earthquakes.live", 0, 7)
NOW = datetime(2026, 11, 5, 8, 30, 15, tzinfo=timezone.utc)


def _valid(message: dict) -> ValidEvent:
    """Construye el ValidEvent a mano (sin pasar por la validación)."""
    event = message["event"]
    props = event["properties"]
    coords = event["geometry"]["coordinates"]
    replay_at = message["replay_at"]
    return ValidEvent(
        source=message["source"],
        mode=message["mode"],
        ingested_at=datetime.strptime(message["ingested_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
        replay_at=(
            datetime.strptime(replay_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) if replay_at else None
        ),
        is_synthetic=message["is_synthetic"],
        event=event,
        event_id=event["id"],
        time_ms=props["time"],
        updated_ms=props["updated"],
        mag=props.get("mag"),
        depth=coords[2] if len(coords) > 2 else None,
        lon=coords[0],
        lat=coords[1],
        place=props.get("place"),
        status=props.get("status"),
        url=props.get("url"),
        sig=props.get("sig"),
        mag_type=props.get("magType"),
    )


def _message(mag: float | None = 4.2) -> dict:
    return build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, mag)


def test_ms_to_utc_epoch() -> None:
    assert ms_to_utc(0).isoformat() == "1970-01-01T00:00:00+00:00"


def test_ms_to_utc_known_value_has_utc_tzinfo() -> None:
    result = ms_to_utc(1793786700000)
    assert result.isoformat() == "2026-11-04T10:05:00+00:00"
    assert result.tzinfo is timezone.utc


def test_range_constants() -> None:
    assert MIN_EPOCH_MS == -30610224000000
    assert MAX_EPOCH_MS == 32503680000000
    assert ms_to_utc(MIN_EPOCH_MS).isoformat() == "1000-01-01T00:00:00+00:00"
    assert ms_to_utc(MAX_EPOCH_MS - 1).isoformat() == "2999-12-31T23:59:59.999000+00:00"


@pytest.mark.parametrize("ms", [MIN_EPOCH_MS, -1, 0, 1, 1793786700123, MAX_EPOCH_MS - 1])
def test_ms_to_utc_roundtrip_without_losing_milliseconds(ms: int) -> None:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = ms_to_utc(ms) - epoch
    assert (delta.days * 86_400_000) + (delta.seconds * 1000) + delta.microseconds // 1000 == ms


def test_null_mag_is_none_not_zero() -> None:
    rows = build_event_rows(_valid(_message(None)), REF, NOW)
    assert rows.current["mag"] is None
    assert rows.version["mag"] is None
    assert "mag" in rows.nulls


def test_negative_values_use_decimal_of_str() -> None:
    message = _message(-0.06)
    message["event"]["geometry"]["coordinates"][2] = -0.18
    rows = build_event_rows(_valid(message), REF, NOW)
    assert rows.current["mag"] == Decimal("-0.06")
    assert rows.current["depth_km"] == Decimal("-0.18")
    assert rows.version["mag"] == Decimal("-0.06")
    assert rows.version["depth_km"] == Decimal("-0.18")


def test_date_and_iso_dow() -> None:
    rows = build_event_rows(_valid(_message()), REF, NOW)
    assert rows.date.date_id.isoformat() == "2026-11-04"
    assert (rows.date.year, rows.date.month, rows.date.day) == (2026, 11, 4)
    assert rows.date.dow == 3  # miércoles
    assert rows.current["date_id"] == rows.date.date_id


def test_dow_sunday_is_seven() -> None:
    message = _message()
    # 2026-11-08 es domingo: 4 días después de 2026-11-04
    message["event"]["properties"]["time"] = E1_TIME_MS + 4 * 86_400_000
    assert build_event_rows(_valid(message), REF, NOW).date.dow == 7


def test_country_id_goes_only_in_current() -> None:
    rows = build_event_rows(_valid(_message()), REF, NOW, "ESP")
    assert rows.current["country_id"] == "ESP"
    assert "country_id" not in rows.version


def test_country_id_defaults_to_none_in_current() -> None:
    rows = build_event_rows(_valid(_message()), REF, NOW)
    assert rows.current["country_id"] is None
    assert "country_id" not in rows.version


def test_received_at_is_injected_clock_not_event_time() -> None:
    rows = build_event_rows(_valid(_message()), REF, NOW)
    assert rows.version["received_at"] == NOW
    assert rows.version["received_at"] != rows.current["event_time"]
    assert rows.version["kafka_topic"] == "earthquakes.live"
    assert (rows.version["kafka_partition"], rows.version["kafka_offset"]) == (0, 7)


def test_batch_reference_leaves_kafka_columns_null_in_version() -> None:
    """Carga por lote (historico): sin particion ni offset las columnas `kafka_*` salen `None`."""
    rows = build_event_rows(_valid(_message()), MessageRef("earthquakes.live", None, None), NOW)
    version = rows.version
    assert (version["kafka_topic"], version["kafka_partition"], version["kafka_offset"]) == (None, None, None)


def test_ms_and_timestamps_are_consistent() -> None:
    rows = build_event_rows(_valid(_message()), REF, NOW)
    assert rows.current["event_time_ms"] == E1_TIME_MS
    assert rows.current["event_time"] == ms_to_utc(E1_TIME_MS)
    assert rows.current["updated_ms"] == E1_UPDATED_1005
    assert rows.current["updated_at"] == ms_to_utc(E1_UPDATED_1005)


def test_nulls_lists_all_null_fields() -> None:
    message = _message(None)
    props = message["event"]["properties"]
    for key in ("place", "status", "url", "sig", "magType"):
        props[key] = None
    message["event"]["geometry"]["coordinates"] = [1.0, 2.0]
    rows = build_event_rows(_valid(message), REF, NOW)
    assert set(rows.nulls) == {"mag", "depth_km", "place", "status", "url", "sig", "mag_type"}


def test_no_nulls_when_everything_is_present() -> None:
    assert build_event_rows(_valid(_message()), REF, NOW).nulls == ()


def test_lon_lat_are_float_and_sig_is_int() -> None:
    rows = build_event_rows(_valid(_message()), REF, NOW)
    assert isinstance(rows.current["lon"], float)
    assert isinstance(rows.current["lat"], float)
    assert isinstance(rows.current["sig"], int)


def test_original_is_compact_json_equal_to_event() -> None:
    message = _message()
    message["event"]["properties"]["place"] = "Ñandú, 日本"
    rows = build_event_rows(_valid(message), REF, NOW)
    assert json.loads(rows.original) == message["event"]
    assert ", " not in rows.original.replace("Ñandú, 日本", "")
    assert "日本" in rows.original  # ensure_ascii=False
    assert rows.version["original"] == rows.original


def test_envelope_fields_are_copied_for_live() -> None:
    message = _message()
    rows = build_event_rows(_valid(message), REF, NOW)
    assert rows.source == message["source"]
    assert rows.ingested_at == datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
    assert rows.ingested_at != rows.version["received_at"]
    assert rows.replay_at is None
    assert rows.is_synthetic is True
    assert rows.version["source"] == message["source"]
    assert rows.version["is_synthetic"] is True


def test_envelope_fields_are_copied_for_replay() -> None:
    message = build_message(_message()["event"], mode="replay", replay_at="2026-11-04T10:30:00Z")
    rows = build_event_rows(_valid(message), MessageRef("earthquakes.replay", 0, 1), NOW)
    assert rows.replay_at == datetime(2026, 11, 4, 10, 30, 0, tzinfo=timezone.utc)
    assert rows.current["replay_at"] == rows.replay_at


def test_is_synthetic_false_is_copied() -> None:
    message = build_message(_message()["event"], source="usgs_feed", is_synthetic=False)
    rows = build_event_rows(_valid(message), REF, NOW)
    assert rows.current["is_synthetic"] is False
    assert rows.version["is_synthetic"] is False
