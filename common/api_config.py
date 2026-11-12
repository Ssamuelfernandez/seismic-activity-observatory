"""Configuración de la API de consulta: límites de la respuesta y espera por la base (F5, FR-019)."""
from dataclasses import dataclass

import re

from common.config import ConfigError, read_int, read_str

CORS_VARIABLE = "CORS_ALLOWED_ORIGINS"
DEFAULT_CORS_ORIGINS = "https://observatorio.ssamuelfernandez.net,http://localhost:4200"
# Origen exacto: esquema http(s), host y puerto opcional; sin ruta, barra final ni comodines.
_ORIGIN_PATTERN = re.compile(r"^https?://[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(:[0-9]{1,5})?$")
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


def parse_cors_origins(raw: str) -> tuple[str, ...]:
    """Valida y normaliza la lista de orígenes CORS permitidos.

    Qué hace:
        Divide por comas, recorta espacios, ignora vacíos y duplicados, y exige que cada
        elemento sea `http(s)://host[:puerto]` sin ruta ni barra final.
    Recibe:
        raw: texto de `CORS_ALLOWED_ORIGINS`.
    Devuelve:
        Tupla de orígenes únicos en el orden dado; lanza `ConfigError` nombrando la variable
        si hay `*`, un elemento no válido o la lista queda vacía.
    Por qué existe:
        Solo el panel público y el desarrollo local pueden leer la API (F9, FR-001, FR-003).
    """
    items = tuple(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))
    if not items:
        raise ConfigError(f"La variable {CORS_VARIABLE} no contiene ningún origen.")
    for item in items:
        if item == "*":
            raise ConfigError(f"La variable {CORS_VARIABLE} no admite '*'; indica orígenes exactos.")
        if not _ORIGIN_PATTERN.match(item):
            raise ConfigError(f"La variable {CORS_VARIABLE} contiene un origen no válido: '{item}'; "
                              "usa http(s)://host[:puerto] sin ruta ni barra final.")
    return items


def load_cors_origins() -> tuple[str, ...]:
    """Carga los orígenes CORS desde `CORS_ALLOWED_ORIGINS` (defecto: panel público y localhost:4200)."""
    return parse_cors_origins(read_str(CORS_VARIABLE, DEFAULT_CORS_ORIGINS))
