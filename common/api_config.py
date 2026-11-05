"""Configuración de la API de consulta: límites de la respuesta y espera por la base (F5, FR-019)."""
from dataclasses import dataclass

from common.config import read_int

DEFAULT_API_MAX_EVENTS = 5000
MIN_API_MAX_EVENTS = 1
DEFAULT_API_DB_TIMEOUT_SECONDS = 5
MIN_API_DB_TIMEOUT_SECONDS = 1
# Por debajo de 10 s: la API debe contestar 503 antes de ese tiempo con la base caída (SC-004).
MAX_API_DB_TIMEOUT_SECONDS = 9


@dataclass(frozen=True)
class ApiSettings:
    """Límites de la API: eventos por respuesta y espera máxima por una conexión."""

    max_events: int = DEFAULT_API_MAX_EVENTS
    db_timeout_seconds: int = DEFAULT_API_DB_TIMEOUT_SECONDS


def load_api_settings() -> ApiSettings:
    """Carga `API_MAX_EVENTS` y `API_DB_TIMEOUT_SECONDS` desde el entorno.

    Qué hace:
        Lee ambas variables con su valor por defecto y su rango permitido.
    Devuelve:
        ApiSettings validada; lanza `ConfigError` si un valor no es entero o está fuera de rango.
    Por qué existe:
        El máximo de eventos y la espera por la base son configurables (constitución §10 y §11).
    """
    return ApiSettings(
        max_events=read_int("API_MAX_EVENTS", DEFAULT_API_MAX_EVENTS, minimum=MIN_API_MAX_EVENTS),
        db_timeout_seconds=read_int("API_DB_TIMEOUT_SECONDS", DEFAULT_API_DB_TIMEOUT_SECONDS,
                                    minimum=MIN_API_DB_TIMEOUT_SECONDS, maximum=MAX_API_DB_TIMEOUT_SECONDS),
    )
