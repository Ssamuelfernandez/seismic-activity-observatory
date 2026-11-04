"""Pruebas de `common/live_message.py`: mensaje del contrato kafka-message.md §3 (B7, B8)."""
import copy
import json
from datetime import datetime, timedelta, timezone

from common.decode import decode_value
from common.live_message import build_live_message, message_key
from common.records import Rejection
from common.validation import validate_message

LIVE_TOPIC = "earthquakes.live"
INGESTED_AT = datetime(2026, 11, 1, 14, 33, 24, tzinfo=timezone.utc)

# Evento del ejemplo de kafka-message.md §4 (forma real de una consulta de USGS).
CONTRACT_EVENT = {
    "type": "Feature",
    "properties": {
        "mag": -0.06, "place": "3 km WSW of Anza, CA", "time": 1793528210440,
        "updated": 1793528420510, "tz": None,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci41570768",
        "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/ci41570768.geojson",
        "felt": None, "cdi": None, "mmi": None, "alert": None, "status": "automatic",
        "tsunami": 0, "sig": 0, "net": "ci", "code": "41570768", "ids": ",ci41570768,",
        "sources": ",ci,", "types": ",nearby-cities,origin,phase-data,", "nst": 16,
        "dmin": 0.03898, "rms": 0.13, "gap": 54, "magType": "ml", "type": "earthquake",
        "title": "M -0.1 - 3 km WSW of Anza, CA",
    },
    "geometry": {"type": "Point", "coordinates": [-116.701666666667, 33.5401666666667, 6.39]},
    "id": "ci41570768",
}


def test_message_has_exactly_the_contract_fields():
    message = build_live_message(CONTRACT_EVENT, INGESTED_AT)
    assert set(message) == {"source", "mode", "ingested_at", "replay_at", "is_synthetic", "event"}
    assert message["source"] == "usgs_feed"
    assert message["mode"] == "live"
    assert message["replay_at"] is None
    assert message["is_synthetic"] is False
    assert message["ingested_at"] == "2026-11-01T14:33:24Z"


def test_event_is_the_same_unmodified_element():
    original = copy.deepcopy(CONTRACT_EVENT)
    message = build_live_message(CONTRACT_EVENT, INGESTED_AT)
    assert message["event"] == original
    assert CONTRACT_EVENT == original


def test_null_and_negative_magnitude_are_kept():
    assert build_live_message(CONTRACT_EVENT, INGESTED_AT)["event"]["properties"]["mag"] == -0.06
    nulled = copy.deepcopy(CONTRACT_EVENT)
    nulled["properties"]["mag"] = None
    assert build_live_message(nulled, INGESTED_AT)["event"]["properties"]["mag"] is None


def test_ingested_at_is_converted_to_utc_with_z():
    plus_two = INGESTED_AT.astimezone(timezone(timedelta(hours=2)))
    assert build_live_message(CONTRACT_EVENT, plus_two)["ingested_at"] == "2026-11-01T14:33:24Z"


def test_key_is_the_event_id():
    assert message_key(CONTRACT_EVENT) == "ci41570768"


def test_key_is_none_without_id():
    assert message_key({"type": "Feature", "properties": {}}) is None


def test_key_is_none_when_id_is_not_text():
    assert message_key({"id": 123}) is None


def test_message_passes_the_consumer_validation_without_quarantine():
    message = build_live_message(CONTRACT_EVENT, INGESTED_AT)
    decoded = decode_value(json.dumps(message).encode("utf-8"))
    verdict = validate_message(decoded, LIVE_TOPIC)
    assert not isinstance(verdict, Rejection), getattr(verdict, "reason", None)
