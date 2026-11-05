"""Pruebas del contenido de los casos de `tests/support/publish_messages.py` (T072; sin Kafka)."""
import pytest

from common.decode import decode_value
from common.kafka_topics import TOPIC_LIVE
from common.records import Rejection
from common.validation import validate_message
from tests.support.publish_messages import CASES, build_case, build_parser

QUARANTINE_REASONS = [
    "coordinates_out_of_range", None, "db_constraint_violation", "invalid_json", "invalid_json",
    "mode_topic_mismatch", "value_out_of_range",
]


def _reason(item) -> str | None:
    verdict = validate_message(decode_value(item.value), TOPIC_LIVE)
    return verdict.reason if isinstance(verdict, Rejection) else None


def test_help_lists_every_case() -> None:
    text = build_parser().format_help()
    assert all(name in text for name in CASES)
    assert set(CASES) == {"faq12", "late-old", "replay-100", "invalid-twice", "constraint-twice",
                          "quarantine-set", "numbered", "geo-madrid", "geo-atlantico", "geo-mag-nula",
                          "geo-lat-145"}


@pytest.mark.parametrize(("name", "size"), [("faq12", 5), ("late-old", 1), ("replay-100", 100),
                                             ("invalid-twice", 2), ("constraint-twice", 2), ("quarantine-set", 7)])
def test_case_sizes(name: str, size: int) -> None:
    assert len(build_case(name)) == size


def test_numbered_uses_distinct_ids_and_count() -> None:
    items = build_case("numbered", 3)
    assert [i.key for i in items] == [b"synthetic-numbered-0001", b"synthetic-numbered-0002", b"synthetic-numbered-0003"]


def test_faq12_and_late_old_are_valid_and_keyed_by_event_id() -> None:
    for item in build_case("faq12") + build_case("late-old"):
        assert _reason(item) is None
        assert item.key.startswith(b"synthetic-faq12-")


def test_repeated_cases_send_identical_bytes() -> None:
    for name in ("replay-100", "invalid-twice", "constraint-twice"):
        assert len({item.value for item in build_case(name)}) == 1


def test_quarantine_set_reasons_in_order() -> None:
    assert [_reason(item) for item in build_case("quarantine-set")] == QUARANTINE_REASONS


def test_quarantine_set_hostile_bytes_are_exact() -> None:
    items = build_case("quarantine-set")
    assert items[3].value == b"\xff\xfe{" and items[4].value is None and items[4].key is not None
    assert b"\\u0000" in items[2].value
    assert len(items[6].key) == 600


def test_all_published_messages_are_synthetic() -> None:
    for name in CASES:
        for item in build_case(name):
            if item.value and decode_value(item.value).ok:
                assert decode_value(item.value).obj["is_synthetic"] is True


@pytest.mark.parametrize(("name", "reason", "event_id"), [
    ("geo-madrid", None, "synthetic-geo-madrid"), ("geo-atlantico", None, "synthetic-geo-atlantico"),
    ("geo-mag-nula", None, "synthetic-geo-mag-nula"), ("geo-lat-145", "coordinates_out_of_range", "synthetic-geo-lat-145"),
])
def test_geo_cases_are_single_keyed_messages_with_expected_validity(name: str, reason: str | None, event_id: str) -> None:
    items = build_case(name)
    assert len(items) == 1 and items[0].key == event_id.encode()
    assert _reason(items[0]) == reason
