"""Pruebas de `common/usgs_feed.py`: validar el cuerpo del feed y su hash canónico (B4, B5, B10)."""
import json
import logging

import pytest

from common.usgs_feed import FeedFormatError, hash_features, parse_feed_body

FEATURE = {"type": "Feature", "id": "synthetic-1", "properties": {"updated": 10, "mag": None}}


def _body(obj) -> bytes:
    return json.dumps(obj).encode("utf-8")


def test_valid_body_returns_the_features():
    raw = _body({"metadata": {"generated": 1}, "features": [FEATURE]})
    assert parse_feed_body(raw) == [FEATURE]


def test_empty_features_list_is_valid_and_has_zero_events():
    assert parse_feed_body(_body({"features": []})) == []


@pytest.mark.parametrize("raw", [b"{no", b"", b"\xff\xfe"])
def test_broken_json_raises_with_a_reason(raw):
    with pytest.raises(FeedFormatError, match="JSON"):
        parse_feed_body(raw)


def test_body_that_is_not_an_object_raises():
    with pytest.raises(FeedFormatError, match="objeto"):
        parse_feed_body(b"[]")


def test_object_without_features_raises():
    with pytest.raises(FeedFormatError, match="features"):
        parse_feed_body(b"{}")


def test_features_that_is_not_a_list_raises():
    with pytest.raises(FeedFormatError, match="lista"):
        parse_feed_body(_body({"features": {"a": 1}}))


def test_elements_that_are_not_objects_are_dropped_with_a_warning(caplog):
    raw = _body({"features": [FEATURE, 5, "x", None]})
    with caplog.at_level(logging.WARNING):
        assert parse_feed_body(raw) == [FEATURE]
    assert "descarta" in caplog.text


def test_hash_is_64_hex_characters():
    digest = hash_features([FEATURE])
    assert len(digest) == 64 and int(digest, 16) >= 0


def test_hash_ignores_key_order():
    reordered = {"properties": {"mag": None, "updated": 10}, "id": "synthetic-1", "type": "Feature"}
    assert hash_features([FEATURE]) == hash_features([reordered])


def test_hash_ignores_the_metadata_of_the_response():
    first = parse_feed_body(_body({"metadata": {"generated": 1}, "features": [FEATURE]}))
    second = parse_feed_body(_body({"metadata": {"generated": 2}, "features": [FEATURE]}))
    assert hash_features(first) == hash_features(second)


def test_hash_changes_when_an_updated_changes():
    changed = {**FEATURE, "properties": {"updated": 11, "mag": None}}
    assert hash_features([FEATURE]) != hash_features([changed])


def test_hash_accepts_non_ascii_text():
    feature = {"id": "synthetic-2", "properties": {"place": "Ñuble, Chile"}}
    assert len(hash_features([feature])) == 64
