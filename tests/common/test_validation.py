"""Pruebas de `validate_message`: los 14 motivos, su orden y los límites (T023)."""
import json
from collections.abc import Callable
from datetime import datetime, timezone

import pytest

from common.decode import decode_value
from common.records import Rejection, ValidEvent
from common.synthetic_event import build_synthetic_event_id, build_synthetic_message
from common.transform import MAX_EPOCH_MS, MIN_EPOCH_MS
from common.validation import validate_message
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message as build_fixture

LIVE = "earthquakes.live"
REPLAY = "earthquakes.replay"
SURROGATE = chr(0xD800)


def _base() -> dict:
    return build_fixture(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)


def _validate(message: object, topic: str = LIVE) -> ValidEvent | Rejection:
    return validate_message(decode_value(json.dumps(message).encode("utf-8")), topic)


def _mutated(mutate: Callable[[dict], None], topic: str = LIVE) -> ValidEvent | Rejection:
    message = _base()
    mutate(message)
    return _validate(message, topic)


def _reason(result: ValidEvent | Rejection) -> str:
    assert isinstance(result, Rejection), f"se esperaba rechazo y salió {result!r}"
    return result.reason


def _props(message: dict) -> dict:
    return message["event"]["properties"]


def _coords(message: dict) -> list:
    return message["event"]["geometry"]["coordinates"]


def _deep(levels: int) -> list:
    node: list = []
    for _ in range(levels - 1):
        node = [node]
    return node


def test_valid_message_returns_valid_event() -> None:
    result = _validate(_base())
    assert isinstance(result, ValidEvent)
    assert (result.event_id, result.updated_ms, result.mag) == (FAQ12_E1, E1_UPDATED_1005, 4.2)
    assert result.ingested_at == datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
    assert result.replay_at is None


# --- Una prueba por motivo -------------------------------------------------------------


def test_invalid_json_tombstone() -> None:
    assert _reason(validate_message(decode_value(None), LIVE)) == "invalid_json"


def test_invalid_json_broken_text() -> None:
    assert _reason(validate_message(decode_value(b"{no"), LIVE)) == "invalid_json"


@pytest.mark.parametrize("value", [None, [], 123])
def test_invalid_envelope_not_an_object(value: object) -> None:
    assert _reason(_validate(value)) == "invalid_envelope"


@pytest.mark.parametrize("key", ["source", "mode", "ingested_at", "is_synthetic", "event"])
def test_invalid_envelope_missing_key(key: str) -> None:
    assert _reason(_mutated(lambda m: m.pop(key))) == "invalid_envelope"


def test_invalid_envelope_unknown_source() -> None:
    assert _reason(_mutated(lambda m: m.update(source="otro"))) == "invalid_envelope"


def test_invalid_envelope_unknown_mode() -> None:
    assert _reason(_mutated(lambda m: m.update(mode="batch"))) == "invalid_envelope"


@pytest.mark.parametrize(
    "value",
    ["2026-11-04 10:00:00Z", "2026-11-04T10:00:00", "2026-13-04T10:00:00Z", "2026-02-30T10:00:00Z", 5, None],
)
def test_invalid_envelope_bad_ingested_at(value: object) -> None:
    assert _reason(_mutated(lambda m: m.update(ingested_at=value))) == "invalid_envelope"


def test_invalid_envelope_is_synthetic_not_bool() -> None:
    assert _reason(_mutated(lambda m: m.update(is_synthetic=1))) == "invalid_envelope"


def test_invalid_envelope_event_not_object() -> None:
    assert _reason(_mutated(lambda m: m.update(event=[]))) == "invalid_envelope"


def test_invalid_envelope_bad_replay_at_when_present() -> None:
    assert _reason(_mutated(lambda m: m.update(replay_at="mañana"))) == "invalid_envelope"


def test_ingested_at_with_fraction_is_valid() -> None:
    assert isinstance(_mutated(lambda m: m.update(ingested_at="2026-11-04T10:00:00.123456789Z")), ValidEvent)


def test_replay_at_absent_in_live_is_null() -> None:
    assert isinstance(_mutated(lambda m: m.pop("replay_at")), ValidEvent)


def test_mode_topic_mismatch_replay_in_live_topic() -> None:
    result = _mutated(lambda m: m.update(mode="replay", replay_at="2026-11-04T10:30:00Z"))
    assert _reason(result) == "mode_topic_mismatch"


def test_mode_topic_mismatch_live_in_replay_topic() -> None:
    assert _reason(_validate(_base(), REPLAY)) == "mode_topic_mismatch"


def test_replay_at_missing() -> None:
    result = _mutated(lambda m: m.update(mode="replay", replay_at=None), REPLAY)
    assert _reason(result) == "replay_at_missing"


def test_valid_replay_message_in_replay_topic() -> None:
    result = _mutated(lambda m: m.update(mode="replay", replay_at="2026-11-04T10:30:00Z"), REPLAY)
    assert isinstance(result, ValidEvent)
    assert result.replay_at == datetime(2026, 11, 4, 10, 30, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("value", [None, ""])
def test_missing_id(value: object) -> None:
    assert _reason(_mutated(lambda m: m["event"].update(id=value))) == "missing_id"


def test_missing_id_absent() -> None:
    assert _reason(_mutated(lambda m: m["event"].pop("id"))) == "missing_id"


@pytest.mark.parametrize("value", [None, "x", 1.5, True])
def test_missing_time_wrong_value(value: object) -> None:
    assert _reason(_mutated(lambda m: _props(m).update(time=value))) == "missing_time"


def test_missing_time_absent_or_no_properties() -> None:
    assert _reason(_mutated(lambda m: _props(m).pop("time"))) == "missing_time"
    assert _reason(_mutated(lambda m: m["event"].update(properties=[]))) == "missing_time"


@pytest.mark.parametrize("value", [None, "x", 1.5, False])
def test_missing_updated_wrong_value(value: object) -> None:
    assert _reason(_mutated(lambda m: _props(m).update(updated=value))) == "missing_updated"


def test_missing_updated_absent() -> None:
    assert _reason(_mutated(lambda m: _props(m).pop("updated"))) == "missing_updated"


@pytest.mark.parametrize(
    "geometry",
    [
        None,
        [],
        {"type": "LineString", "coordinates": [1, 2]},
        {"type": "Point", "coordinates": [1]},
        {"type": "Point", "coordinates": "ab"},
        {"type": "Point"},
    ],
)
def test_invalid_geometry(geometry: object) -> None:
    assert _reason(_mutated(lambda m: m["event"].update(geometry=geometry))) == "invalid_geometry"


def test_coordinates_out_of_range_latitude_145() -> None:
    # prueba de aceptación 6
    assert _reason(_mutated(lambda m: _coords(m).__setitem__(1, 145))) == "coordinates_out_of_range"


@pytest.mark.parametrize(
    "index,value",
    [(0, 181), (0, -180.5), (1, -90.1), (0, 10**400), (0, float("nan")), (1, float("inf"))],
)
def test_coordinates_out_of_range_other_cases(index: int, value: float) -> None:
    assert _reason(_mutated(lambda m: _coords(m).__setitem__(index, value))) == "coordinates_out_of_range"


@pytest.mark.parametrize("value", [-10.01, 15.01, float("nan"), float("inf"), 10**400])
def test_mag_out_of_range(value: float) -> None:
    assert _reason(_mutated(lambda m: _props(m).update(mag=value))) == "mag_out_of_range"


@pytest.mark.parametrize("value", [-100.01, 1000.01, float("nan"), float("-inf")])
def test_depth_out_of_range(value: float) -> None:
    assert _reason(_mutated(lambda m: _coords(m).__setitem__(2, value))) == "depth_out_of_range"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m["event"].update(id=12345),
        lambda m: m["event"].update(id=True),
        lambda m: _props(m).update(place=42),
        lambda m: _props(m).update(url=[]),
        lambda m: _props(m).update(status=1),
        lambda m: _props(m).update(magType=1),
        lambda m: _props(m).update(sig=True),
        lambda m: _props(m).update(sig="5"),
        lambda m: _props(m).update(sig=1.5),
        lambda m: _props(m).update(mag="4.2"),
        lambda m: _coords(m).__setitem__(2, "6"),
        lambda m: _coords(m).__setitem__(0, "10"),
        lambda m: _coords(m).__setitem__(1, True),
    ],
)
def test_invalid_field_type(mutate: Callable[[dict], None]) -> None:
    assert _reason(_mutated(mutate)) == "invalid_field_type"


@pytest.mark.parametrize("value", [2**31, -(2**31) - 1])
def test_value_out_of_range_sig(value: int) -> None:
    assert _reason(_mutated(lambda m: _props(m).update(sig=value))) == "value_out_of_range"


@pytest.mark.parametrize("value", [MIN_EPOCH_MS - 1, MAX_EPOCH_MS])
@pytest.mark.parametrize("field", ["time", "updated"])
def test_value_out_of_range_time_fields(field: str, value: int) -> None:
    assert _reason(_mutated(lambda m: _props(m).update({field: value}))) == "value_out_of_range"


def test_db_constraint_violation_for_unstorable_field() -> None:
    # `dmin` = NaN: válido por contrato pero no almacenable como jsonb
    assert _reason(_mutated(lambda m: _props(m).update(dmin=float("nan")))) == "db_constraint_violation"


def test_db_constraint_violation_for_nul_and_depth() -> None:
    assert _reason(_mutated(lambda m: _props(m).update(place="a\u0000b"))) == "db_constraint_violation"
    assert _reason(_mutated(lambda m: _props(m).update(extra=_deep(100)))) == "db_constraint_violation"


def test_db_constraint_violation_for_lone_surrogate() -> None:
    # json.dumps escribe el sustituto como secuencia ASCII; json.loads lo devuelve como cadena.
    assert _reason(_mutated(lambda m: _props(m).update(place=SURROGATE))) == "db_constraint_violation"


# --- Prevalencia -----------------------------------------------------------------------


def test_precedence_first_reason_in_order_wins() -> None:
    def break_everything(m: dict) -> None:
        m["event"]["id"] = ""
        _props(m).update(time="x", mag=99)
        _coords(m)[1] = 145

    assert _reason(_mutated(break_everything)) == "missing_id"


def test_precedence_envelope_before_mode_mismatch() -> None:
    assert _reason(_mutated(lambda m: m.update(mode="replay", ingested_at="mal"))) == "invalid_envelope"


def test_precedence_coordinates_before_mag() -> None:
    def mutate(m: dict) -> None:
        _coords(m)[1] = 145
        _props(m).update(mag=99)

    assert _reason(_mutated(mutate)) == "coordinates_out_of_range"


def test_precedence_range_before_field_type() -> None:
    assert _reason(_mutated(lambda m: _props(m).update(mag=99, place=42))) == "mag_out_of_range"


def test_precedence_field_type_before_value_range() -> None:
    assert _reason(_mutated(lambda m: _props(m).update(place=42, sig=2**40))) == "invalid_field_type"


# --- Límites exactos --------------------------------------------------------------------


@pytest.mark.parametrize("value", [-10, 15, -10.0, 15.0])
def test_mag_limits_are_valid(value: float) -> None:
    assert isinstance(_mutated(lambda m: _props(m).update(mag=value)), ValidEvent)


@pytest.mark.parametrize("value", [-100, 1000])
def test_depth_limits_are_valid(value: float) -> None:
    assert isinstance(_mutated(lambda m: _coords(m).__setitem__(2, value)), ValidEvent)


@pytest.mark.parametrize("index,value", [(0, 180), (0, -180), (1, 90), (1, -90)])
def test_coordinate_limits_are_valid(index: int, value: float) -> None:
    assert isinstance(_mutated(lambda m: _coords(m).__setitem__(index, value)), ValidEvent)


def test_event_id_512_is_valid_and_513_is_out_of_range() -> None:
    assert isinstance(_mutated(lambda m: m["event"].update(id="a" * 512)), ValidEvent)
    assert _reason(_mutated(lambda m: m["event"].update(id="a" * 513))) == "value_out_of_range"


def test_sig_int32_limits_are_valid() -> None:
    assert isinstance(_mutated(lambda m: _props(m).update(sig=2**31 - 1)), ValidEvent)
    assert isinstance(_mutated(lambda m: _props(m).update(sig=-(2**31))), ValidEvent)


def test_time_limits_are_valid() -> None:
    assert isinstance(_mutated(lambda m: _props(m).update(time=MIN_EPOCH_MS, updated=MAX_EPOCH_MS - 1)), ValidEvent)


@pytest.mark.parametrize("field", ["mag", "place", "status", "url", "sig", "magType"])
def test_null_properties_are_valid(field: str) -> None:
    assert isinstance(_mutated(lambda m: _props(m).update({field: None})), ValidEvent)


def test_null_or_absent_depth_is_valid() -> None:
    assert isinstance(_mutated(lambda m: _coords(m).__setitem__(2, None)), ValidEvent)
    assert isinstance(_mutated(lambda m: m["event"]["geometry"].update(coordinates=[1.0, 2.0])), ValidEvent)


def test_negative_mag_and_depth_are_valid() -> None:
    def mutate(m: dict) -> None:
        _props(m).update(mag=-0.06)
        _coords(m)[2] = -0.18

    result = _mutated(mutate)
    assert isinstance(result, ValidEvent)
    assert (result.mag, result.depth) == (-0.06, -0.18)


def test_message_without_kafka_key_but_with_event_id_is_valid() -> None:
    # La clave Kafka no se pasa a validate_message: basta con event.id.
    assert isinstance(_validate(_base()), ValidEvent)


def test_huge_integers_do_not_raise() -> None:
    assert _reason(_mutated(lambda m: _props(m).update(sig=10**400))) == "value_out_of_range"
    assert _reason(_mutated(lambda m: _props(m).update(time=10**400))) == "value_out_of_range"


# --- Compatibilidad con el productor de 002 ---------------------------------------------


def test_synthetic_event_of_002_is_valid() -> None:
    now = datetime.now(timezone.utc)
    message = build_synthetic_message(build_synthetic_event_id(now), now)
    decoded = decode_value(json.dumps(message).encode())
    assert isinstance(validate_message(decoded, LIVE), ValidEvent)
