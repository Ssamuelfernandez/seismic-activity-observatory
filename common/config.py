"""Lectura y validación de la configuración desde variables de entorno (A10).

Toda la configuración variable entra por aquí; el resto del código no llama a `os.environ`.
"""
import os
from dataclasses import dataclass

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RETRY_INITIAL_SECONDS = 1
DEFAULT_RETRY_MAX_SECONDS = 30
DEFAULT_POLL_SECONDS = 60
DEFAULT_USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
DEFAULT_HTTP_TIMEOUT_SECONDS = 10
MAX_HTTP_TIMEOUT_SECONDS = 60
DEFAULT_RAW_RETENTION_DAYS = 7
ALLOWED_URL_SCHEMES = ("https://", "http://")
HEARTBEAT_MARGIN_FACTOR = 2


class ConfigError(Exception):
    """Falta una variable de entorno obligatoria o tiene un valor no válido."""


@dataclass(frozen=True)
class KafkaSettings:
    """Conexión al broker y tema con el que trabaja el servicio."""

    bootstrap_servers: str
    topic: str


@dataclass(frozen=True)
class DatabaseSettings:
    """Conexión a PostgreSQL con el rol propio del servicio."""

    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class RetrySettings:
    """Espera entre reintentos de conexión: crece al doble hasta un máximo."""

    initial_seconds: float
    max_seconds: float


@dataclass(frozen=True)
class HealthSettings:
    """Archivo de latido y antigüedad máxima para considerar sano al servicio."""

    heartbeat_file: str
    max_age_seconds: int


@dataclass(frozen=True)
class FeedSettings:
    """Consulta periódica al feed de USGS y retención de los originales (B1, B5)."""

    url: str
    poll_seconds: int
    timeout_seconds: int
    raw_retention_days: int


def read_str(name: str, default: str | None = None) -> str:
    """Lee una variable de texto.

    Qué hace:
        Devuelve el valor de la variable o el valor por defecto si no está definida.
    Recibe:
        name: nombre de la variable de entorno.
        default: valor si falta; None la hace obligatoria.
    Devuelve:
        El valor como texto, nunca vacío.
    Por qué existe:
        Un servicio sin una variable obligatoria debe fallar nombrándola (FR-036, A10).
    """
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise ConfigError(f"Falta la variable de entorno obligatoria {name}.")
    return value


def read_int(name: str, default: int | None = None,
             minimum: int | None = None, maximum: int | None = None) -> int:
    """Lee una variable entera y comprueba que esté en el rango permitido.

    Qué hace:
        Convierte el valor a entero y valida los límites.
    Recibe:
        name: nombre de la variable; default: valor si falta; minimum y maximum: límites.
    Devuelve:
        El entero validado.
    Por qué existe:
        Evita arrancar con un intervalo o un puerto absurdo sin avisar (A10).
    """
    raw = read_str(name, None if default is None else str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise ConfigError(f"La variable {name} debe ser un entero; se recibió '{raw}'.") from error
    too_low = minimum is not None and value < minimum
    too_high = maximum is not None and value > maximum
    if too_low or too_high:
        raise ConfigError(f"La variable {name} debe estar entre {minimum} y {maximum}; se recibió {value}.")
    return value


def read_optional_int(name: str) -> int | None:
    """Lee una variable entera opcional y no negativa.

    Qué hace:
        Devuelve None si la variable falta o está vacía; si no, la convierte a entero >= 0.
    Recibe:
        name: nombre de la variable de entorno.
    Devuelve:
        El entero, o None si no se configuró.
    Por qué existe:
        El gancho de fallo de la prueba 8 (offset de caída) es opcional y su ausencia
        debe dejar el camino normal intacto (C2).
    """
    if os.environ.get(name, "") == "":
        return None
    return read_int(name, minimum=0)


def load_kafka_settings() -> KafkaSettings:
    """Carga el broker y el tema desde el entorno (A7, A10)."""
    return KafkaSettings(
        bootstrap_servers=read_str("KAFKA_BOOTSTRAP_SERVERS"),
        topic=read_str("KAFKA_TOPIC"),
    )


def load_database_settings() -> DatabaseSettings:
    """Carga la conexión a PostgreSQL con el rol del servicio (FR-030)."""
    return DatabaseSettings(
        host=read_str("DB_HOST"),
        port=read_int("DB_PORT", minimum=1, maximum=65535),
        name=read_str("DB_NAME"),
        user=read_str("DB_USER"),
        password=read_str("DB_PASSWORD"),
    )


def load_retry_settings() -> RetrySettings:
    """Carga la política de reintentos de conexión (A4)."""
    initial = read_int("RETRY_INITIAL_SECONDS", DEFAULT_RETRY_INITIAL_SECONDS, minimum=1)
    maximum = read_int("RETRY_MAX_SECONDS", DEFAULT_RETRY_MAX_SECONDS, minimum=initial)
    return RetrySettings(initial_seconds=initial, max_seconds=maximum)


def load_health_settings() -> HealthSettings:
    """Carga el archivo de latido y su antigüedad máxima (A4)."""
    return HealthSettings(
        heartbeat_file=read_str("HEALTH_FILE"),
        max_age_seconds=read_int("HEALTH_MAX_AGE_SECONDS", minimum=1),
    )


def load_log_level() -> str:
    """Devuelve el nivel de registro configurado."""
    return read_str("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()


def read_feed_url() -> str:
    """Lee la URL del feed y exige un esquema http(s).

    Por qué existe:
        Una URL sin esquema haría fallar a `urllib` en cada ciclo; es mejor detenerse al arrancar (A10).
    """
    url = read_str("USGS_FEED_URL", DEFAULT_USGS_FEED_URL)
    if not url.startswith(ALLOWED_URL_SCHEMES):
        raise ConfigError(f"La variable USGS_FEED_URL debe empezar por https:// o http://; se recibió '{url}'.")
    return url


def load_feed_settings() -> FeedSettings:
    """Carga la configuración del productor en vivo (B1, A10).

    Qué hace:
        Lee `POLL_SECONDS`, `USGS_FEED_URL`, `HTTP_TIMEOUT_SECONDS` y `RAW_RETENTION_DAYS`
        con sus valores por defecto y rangos (data-model.md §5).
    Devuelve:
        FeedSettings validada.
    Por qué existe:
        Sustituye al intervalo fijo del productor mínimo.
    """
    return FeedSettings(
        url=read_feed_url(),
        poll_seconds=read_int("POLL_SECONDS", DEFAULT_POLL_SECONDS, minimum=1),
        timeout_seconds=read_int("HTTP_TIMEOUT_SECONDS", DEFAULT_HTTP_TIMEOUT_SECONDS,
                                 minimum=1, maximum=MAX_HTTP_TIMEOUT_SECONDS),
        raw_retention_days=read_int("RAW_RETENTION_DAYS", DEFAULT_RAW_RETENTION_DAYS, minimum=1),
    )


def validate_poll_against_health(poll_seconds: int, max_age_seconds: int) -> None:
    """Exige que el latido pueda renovarse antes de caducar.

    Qué hace:
        Falla nombrando `POLL_SECONDS` si el doble del intervalo supera la antigüedad máxima.
    Recibe:
        poll_seconds: espera entre consultas; max_age_seconds: antigüedad máxima del latido.
    Por qué existe:
        Con un intervalo mayor, un productor sano se vería no sano (A10, spec US5.3).
    """
    if poll_seconds * HEARTBEAT_MARGIN_FACTOR > max_age_seconds:
        raise ConfigError(
            f"POLL_SECONDS ({poll_seconds}) debe ser como mucho la mitad de HEALTH_MAX_AGE_SECONDS ({max_age_seconds})."
        )
