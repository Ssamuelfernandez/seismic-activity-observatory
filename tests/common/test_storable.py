"""Pruebas de `common/storable.py` (T019)."""
import pytest

from common.storable import (
    MAX_JSON_DEPTH,
    is_storable_json,
    is_storable_text,
    sanitize_raw_text,
)


def _nested_lists(levels: int) -> list:
    node: list = []
    for _ in range(levels - 1):
        node = [node]
    return node


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        float("1e400"),
        "a\x00b",
        {"a\x00": 1},
        {"a": ["x", {"b": "\ud800"}]},
    ],
)
def test_not_storable_values(value: object) -> None:
    assert is_storable_json(value) is False


def test_normal_values_are_storable() -> None:
    assert is_storable_json({"a": [1, 2.5, None, True, "ñ", {"b": "x"}]}) is True


def test_depth_limit_is_64() -> None:
    assert MAX_JSON_DEPTH == 64
    assert is_storable_json(_nested_lists(64)) is True
    assert is_storable_json(_nested_lists(65)) is False


def test_deep_object_does_not_raise_recursion_error() -> None:
    assert is_storable_json(_nested_lists(1500)) is False


def test_is_storable_text() -> None:
    assert is_storable_text("hola") is True
    assert is_storable_text("a\x00") is False
    assert is_storable_text("\ud800") is False


def test_sanitize_invalid_utf8_uses_literal_escape() -> None:
    assert sanitize_raw_text(b"\xff") == "\\xff"
    assert len(sanitize_raw_text(b"\xff")) == 4


def test_sanitize_real_nul_becomes_four_characters() -> None:
    result = sanitize_raw_text(b"a\x00b")
    assert result == "a\\x00b"


@pytest.mark.parametrize("raw", [None, b""])
def test_sanitize_none_and_empty(raw: bytes | None) -> None:
    assert sanitize_raw_text(raw) == ""


def test_sanitize_keeps_ascii_json_escape_of_nul() -> None:
    text = sanitize_raw_text(b'"\\u0000"')
    assert text == '"\\u0000"'
    assert "\\u0000" in text
