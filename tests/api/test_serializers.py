"""Pruebas de api/serializers.py: fila -> Feature y metadata (api.md §3.2-§3.4)."""
import json
from decimal import Decimal

from api.serializers import build_collection, build_feature, build_metadata

PROPERTY_KEYS = {"mag", "magType", "place", "time", "updated", "country_id", "country_name",
                 "is_synthetic", "status", "url", "sig"}
METADATA_KEYS = {"generated", "last_ingestion", "mode", "count", "total", "truncated", "next_cursor",
                 "null_mag_excluded"}


def _row(**overrides) -> dict:
    row = {"event_id": "synthetic-1", "lon": -119.5, "lat": 33.25, "depth_km": Decimal("6.39"),
           "mag": Decimal("2.64"), "mag_type": "ml", "place": "SINTÉTICO", "event_time_ms": 1793536750750,
           "updated_ms": 1793536964214, "country_id": "ESP", "country_name": "España",
           "is_synthetic": True, "status": "automatic", "url": "https://example.invalid/x", "sig": 107}
    row.update(overrides)
    return row


def test_feature_has_contract_shape():
    feature = build_feature(_row())
    assert feature["type"] == "Feature"
    assert feature["id"] == "synthetic-1"
    assert feature["geometry"] == {"type": "Point", "coordinates": [-119.5, 33.25, 6.39]}
    assert set(feature["properties"]) == PROPERTY_KEYS
    props = feature["properties"]
    assert (props["mag"], props["magType"], props["time"], props["updated"]) == (2.64, "ml", 1793536750750,
                                                                                  1793536964214)
    assert (props["country_id"], props["country_name"], props["is_synthetic"], props["sig"]) == (
        "ESP", "España", True, 107)


def test_decimal_becomes_float():
    feature = build_feature(_row())
    assert type(feature["properties"]["mag"]) is float
    assert type(feature["geometry"]["coordinates"][2]) is float


def test_negative_magnitude_and_depth_are_kept():
    feature = build_feature(_row(mag=Decimal("-0.06"), depth_km=Decimal("-0.18")))
    assert feature["properties"]["mag"] == -0.06
    assert feature["geometry"]["coordinates"][2] == -0.18


def test_nulls_stay_null_and_never_zero():
    feature = build_feature(_row(mag=None, depth_km=None, mag_type=None, place=None, status=None, url=None,
                                 sig=None, country_id=None, country_name=None))
    assert feature["geometry"]["coordinates"] == [-119.5, 33.25, None]
    props = feature["properties"]
    assert {key: props[key] for key in ("mag", "magType", "place", "status", "url", "sig",
                                        "country_id", "country_name")} == dict.fromkeys(
        ("mag", "magType", "place", "status", "url", "sig", "country_id", "country_name"))


def test_zero_is_a_real_value():
    feature = build_feature(_row(mag=Decimal("0"), depth_km=Decimal("0"), sig=0))
    assert feature["properties"]["mag"] == 0.0
    assert feature["geometry"]["coordinates"][2] == 0.0
    assert feature["properties"]["sig"] == 0


def test_non_finite_values_become_null():
    feature = build_feature(_row(mag=Decimal("NaN"), depth_km=Decimal("Infinity")))
    assert feature["properties"]["mag"] is None
    assert feature["geometry"]["coordinates"][2] is None


def test_feature_serializes_without_nan():
    json.dumps(build_feature(_row(mag=Decimal("NaN"))), allow_nan=False)


def test_metadata_has_eight_fields():
    metadata = build_metadata(generated=10, last_ingestion=5, mode="live", count=2, total=7,
                              next_cursor="abc", null_mag_excluded=1)
    assert set(metadata) == METADATA_KEYS
    assert metadata["truncated"] is True
    assert (metadata["count"], metadata["total"], metadata["next_cursor"]) == (2, 7, "abc")


def test_metadata_not_truncated_when_count_equals_total():
    metadata = build_metadata(generated=10, last_ingestion=None, mode="replay", count=3, total=3,
                              next_cursor=None, null_mag_excluded=0)
    assert metadata["truncated"] is False
    assert metadata["last_ingestion"] is None
    assert metadata["mode"] == "replay"


def test_collection_is_json_safe():
    metadata = build_metadata(generated=1, last_ingestion=None, mode="live", count=0, total=0,
                              next_cursor=None, null_mag_excluded=0)
    body = build_collection([], metadata)
    assert body == {"type": "FeatureCollection", "metadata": metadata, "features": []}
    json.dumps(body, allow_nan=False)
