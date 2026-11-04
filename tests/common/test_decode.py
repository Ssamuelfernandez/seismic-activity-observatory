"""Pruebas de `decode_value` (T017)."""
import pytest

from common.decode import decode_value


@pytest.mark.parametrize("raw", [None, b""])
def test_tombstone_and_empty_are_invalid_json(raw: bytes | None) -> None:
    result = decode_value(raw)
    assert result.ok is False
    assert result.raw == b""


def test_invalid_utf8_is_not_ok_and_keeps_raw() -> None:
    result = decode_value(b"\xff\xfe{")
    assert result.ok is False
    assert result.raw == b"\xff\xfe{"


def test_utf8_bom_is_not_ok() -> None:
    assert decode_value(b"\xef\xbb\xbf{}").ok is False


@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
def test_utf16_and_utf32_text_is_not_ok(encoding: str) -> None:
    assert decode_value("{}".encode(encoding)).ok is False


def test_broken_json_is_not_ok() -> None:
    assert decode_value(b'{"a": ').ok is False


def test_escaped_lone_surrogate_is_ok() -> None:
    result = decode_value(b'{"a": "\\ud800"}')
    assert result.ok is True
    assert result.obj == {"a": "\ud800"}


def test_integer_over_4300_digits_is_not_ok() -> None:
    assert decode_value(b'{"a": ' + b"1" * 4301 + b"}").ok is False


EXTREME_NESTING_DEPTH = 200_000


def test_extreme_nesting_raises_recursion_error_and_is_not_ok() -> None:
    # El límite de profundidad del analizador en C varía entre parches de CPython 3.12
    # (5000 niveles lanzan RecursionError en 3.12.9 pero no en 3.12.16): se usa una profundidad
    # que lo dispara en ambas versiones.
    raw = b"[" * EXTREME_NESTING_DEPTH + b"]" * EXTREME_NESTING_DEPTH
    assert decode_value(raw).ok is False


def test_nesting_of_1500_levels_never_raises() -> None:
    # Si se decodifica, lo rechazan la validación o la almacenabilidad; nunca una excepción.
    result = decode_value(b"[" * 1500 + b"]" * 1500)
    assert isinstance(result.ok, bool)


@pytest.mark.parametrize("raw,expected", [(b"null", None), (b"[]", []), (b"123", 123)])
def test_valid_json_that_is_not_object_is_ok(raw: bytes, expected: object) -> None:
    result = decode_value(raw)
    assert result.ok is True
    assert result.obj == expected


def test_valid_object_keeps_raw_bytes() -> None:
    raw = b'{"a": 1}'
    result = decode_value(raw)
    assert (result.ok, result.obj, result.raw) == (True, {"a": 1}, raw)
