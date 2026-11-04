"""Latido de los servicios y comprobación de salud para Docker (A4).

Los servicios sin puerto (productor y consumidor) escriben un archivo de latido tras cada
vuelta correcta de su bucle; el healthcheck de Compose comprueba que sea reciente.
Uso desde Compose:
    python -m common.health file    (lee HEALTH_FILE y HEALTH_MAX_AGE_SECONDS)
    python -m common.health http <url>
"""
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from common.config import ConfigError, load_health_settings

HTTP_TIMEOUT_SECONDS = 4


def touch_heartbeat(path: str) -> None:
    """Marca que el servicio sigue vivo y conectado.

    Qué hace:
        Crea el archivo de latido o actualiza su fecha de modificación.
    Recibe:
        path: ruta del archivo de latido.
    Devuelve:
        Nada.
    Por qué existe:
        «Saludable» debe significar listo para atender, no solo proceso existente (FR-006).
    """
    Path(path).touch()


def clear_heartbeat(path: str) -> None:
    """Borra el latido anterior al arrancar.

    Por qué existe:
        Un contenedor reiniciado conserva su sistema de archivos; sin borrarlo, el latido de la
        ejecución anterior lo haría parecer sano antes de reconectar (A4).
    """
    Path(path).unlink(missing_ok=True)


def heartbeat_age_seconds(path: str, now: float) -> float | None:
    """Devuelve los segundos desde el último latido, o None si no existe."""
    try:
        return now - Path(path).stat().st_mtime
    except FileNotFoundError:
        return None


def is_heartbeat_fresh(path: str, max_age_seconds: int, now: float) -> bool:
    """Decide si el último latido es suficientemente reciente.

    Qué hace:
        Compara la antigüedad del latido con el máximo permitido.
    Recibe:
        path: archivo de latido; max_age_seconds: máximo; now: hora actual (epoch).
    Devuelve:
        True si el latido existe y no es más antiguo que el máximo.
    Por qué existe:
        Lógica del healthcheck separada del arranque para poder probarla (A4).
    """
    age = heartbeat_age_seconds(path, now)
    return age is not None and age <= max_age_seconds


def check_http(url: str) -> bool:
    """Devuelve True si la URL responde con código 2xx."""
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, OSError):
        return False


def main(argv: list[str]) -> int:
    """Punto de entrada del healthcheck; devuelve el código de salida para Docker."""
    if len(argv) >= 2 and argv[0] == "http":
        return 0 if check_http(argv[1]) else 1
    if argv[:1] == ["file"]:
        try:
            settings = load_health_settings()
        except ConfigError as error:
            print(error, file=sys.stderr)
            return 1
        fresh = is_heartbeat_fresh(settings.heartbeat_file, settings.max_age_seconds, time.time())
        return 0 if fresh else 1
    print("Uso: python -m common.health file | http <url>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
