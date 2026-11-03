"""Configuración del registro (logging) común a todos los servicios."""
import logging

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: str) -> None:
    """Configura el registro del proceso.

    Qué hace:
        Deja una línea por mensaje en la salida estándar, que Docker recoge.
    Recibe:
        level: nivel de registro (INFO, DEBUG, ...).
    Devuelve:
        Nada.
    Por qué existe:
        Los reintentos y las decisiones deben verse con `docker compose logs` (A4).
    """
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)
