"""Pruebas de api/cursor.py: ida y vuelta y cursores inválidos (F5)."""
import base64
import json

import pytest

from api.cursor import CursorPosition, decode_cursor, encode_cursor
from api.errors import ApiError


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@pytest.mark.parametrize("event_id", ["synthetic-1", 'id con "comillas"', "evento-ñandú-日本", "a/b+c=d"])
def test_round_trip(event_id):
    position = CursorPosition(time_ms=1793536750750, event_id=event_id)
    token = encode_cursor(position)
    assert token.isascii() and "=" not in token
    assert decode_cursor(token) == position


def test_round_trip_negative_time():
    position = CursorPosition(time_ms=-1000, event_id="x")
    assert decode_cursor(encode_cursor(position)) == position


@pytest.mark.parametrize("bad", [
    "",
    "xx",
    "no es base64 !!",
    "ñandú",
    _b64(b"{roto"),
    _b64(b"[1, 2]"),
    _b64(b"\xff\xfe"),
    _b64(json.dumps({"t": "1", "id": "a"}).encode()),
    _b64(json.dumps({"t": True, "id": "a"}).encode()),
    _b64(json.dumps({"t": 1.5, "id": "a"}).encode()),
    _b64(json.dumps({"t": 1, "id": 5}).encode()),
    _b64(json.dumps({"t": 1, "id": ""}).encode()),
    _b64(json.dumps({"t": 1}).encode()),
])
def test_invalid_cursor_raises_invalid_cursor(bad):
    with pytest.raises(ApiError) as caught:
        decode_cursor(bad)
    assert caught.value.status == 400
    assert caught.value.code == "invalid_cursor"
    assert "cursor" in caught.value.message
