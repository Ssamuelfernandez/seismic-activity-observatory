"""Conversión entre ISO 8601 y milisegundos Unix UTC. Puro: no importa `fastapi` ni `asyncpg`.

Todo se calcula con enteros y `timedelta`, nunca con coma flotante (data-model D4).
"""
from datetime import datetime, timedelta, timezone

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MS_PER_HOUR = 3_600_000
RECENT_WINDOW_HOURS = 24
ONE_MILLISECOND = timedelta(milliseconds=1)


def parse_iso_to_ms(text: str) -> int:
    """Convierte una fecha ISO 8601 a milisegundos Unix UTC.

    Qué hace:
        Interpreta solo fecha como 00:00 UTC y una fecha-hora sin zona como UTC; con zona, la normaliza.
    Recibe:
        text: fecha o fecha-hora ISO 8601.
    Devuelve:
        Milisegundos desde 1970-01-01T00:00Z.
    Por qué existe:
        Define el significado de `start` y `end` (api.md §3.1). Lanza `ValueError` si no es ISO 8601.
    """
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (parsed - EPOCH) // ONE_MILLISECOND


def ms_to_datetime(milliseconds: int) -> datetime:
    """Convierte milisegundos Unix a `datetime` UTC exacto (para parámetros SQL)."""
    return EPOCH + timedelta(milliseconds=milliseconds)
