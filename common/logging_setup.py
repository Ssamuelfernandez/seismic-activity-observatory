"""Configuración del registro (logging) común a todos los servicios."""
import logging

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
# El pool de asyncpg registra un traceback completo cada pocos segundos mientras la base está caída.
NOISY_TRACEBACK_LOGGERS = ("asyncpg.pool",)


class DropTracebackFilter(logging.Filter):
    """Conserva el aviso de una línea de un registro y descarta su traceback.

    Por qué existe:
        Con PostgreSQL caído el registro de la API se llenaría de trazas repetidas; el aviso basta para diagnosticar
        y las trazas no deben aparecer en el registro de la API (T015).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.exc_info = None
        record.exc_text = None
        return True


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
    for name in NOISY_TRACEBACK_LOGGERS:
        logging.getLogger(name).addFilter(DropTracebackFilter())
