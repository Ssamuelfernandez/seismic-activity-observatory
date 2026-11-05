"""Cursor opaco de paginación por clave (api.md §3.3). Puro: no importa `fastapi` ni `asyncpg`."""
import base64
import json
from dataclasses import dataclass

from api.errors import CODE_INVALID_CURSOR, STATUS_BAD_REQUEST, ApiError

KEY_TIME = "t"
KEY_ID = "id"
BASE64_PADDING = "="
BASE64_BLOCK = 4
MESSAGE_INVALID_CURSOR = "El parámetro 'cursor' no es válido; usa el valor de 'next_cursor' de la respuesta anterior."


@dataclass(frozen=True)
class CursorPosition:
    """Posición `(event_time, id)` del último evento devuelto en la página anterior."""

    time_ms: int
    event_id: str


def encode_cursor(position: CursorPosition) -> str:
    """Codifica una posición como base64url de un JSON `{"t", "id"}` sin relleno.

    Qué hace:
        Serializa el instante en ms y el `id` del evento y los pasa a base64url.
    Recibe:
        position: posición del último evento de la página.
    Devuelve:
        Cadena opaca para el cliente (`metadata.next_cursor`).
    Por qué existe:
        El cliente repite el cursor tal cual y la API reanuda la lectura sin repetir ni saltar eventos (F5).
    """
    payload = json.dumps({KEY_TIME: position.time_ms, KEY_ID: position.event_id}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip(BASE64_PADDING)


def decode_cursor(text: str) -> CursorPosition:
    """Decodifica un cursor; cualquier forma inválida lanza `ApiError` `invalid_cursor`.

    Qué hace:
        Deshace el base64url, lee el JSON y comprueba los tipos de `t` (entero) e `id` (texto).
    Recibe:
        text: valor del parámetro `cursor`.
    Devuelve:
        La posición codificada.
    Por qué existe:
        Un cursor manipulado o truncado debe dar 400 y no una consulta con valores arbitrarios (api.md §6).
    """
    try:
        padded = text + BASE64_PADDING * (-len(text) % BASE64_BLOCK)
        data = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except ValueError as error:
        raise _invalid() from error
    if not isinstance(data, dict):
        raise _invalid()
    time_ms, event_id = data.get(KEY_TIME), data.get(KEY_ID)
    if isinstance(time_ms, bool) or not isinstance(time_ms, int) or not isinstance(event_id, str) or not event_id:
        raise _invalid()
    return CursorPosition(time_ms=time_ms, event_id=event_id)


def _invalid() -> ApiError:
    return ApiError(STATUS_BAD_REQUEST, CODE_INVALID_CURSOR, MESSAGE_INVALID_CURSOR)
