"""Decodificación del valor de un mensaje Kafka (research.md §3, FR-011, FR-014)."""
import json

from common.records import DecodeResult


def decode_value(raw: bytes | None) -> DecodeResult:
    """Decodifica los bytes del valor Kafka como JSON.

    Qué hace:
        Decodifica primero con UTF-8 estricto y después llama a `json.loads(str)`, nunca a
        `json.loads(bytes)` (que autodetectaría UTF-16/32 y aceptaría un BOM). Cualquier
        fallo (nulo, vacío, UTF-8 inválido, JSON roto, entero de más de 4300 dígitos,
        anidamiento excesivo) da `ok = False`.
    Recibe:
        raw: bytes del valor, o None si el mensaje no tiene valor.
    Devuelve:
        DecodeResult con `raw` siempre en bytes (vacío si el valor era nulo).
    Por qué existe:
        Ningún mensaje debe bloquear la cola: lo no decodificable va a cuarentena como
        `invalid_json` (C1, C5).
    """
    if not raw:
        return DecodeResult(raw=b"", obj=None, ok=False)
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        return DecodeResult(raw=raw, obj=None, ok=False)
    return DecodeResult(raw=raw, obj=obj, ok=True)
