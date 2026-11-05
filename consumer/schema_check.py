"""Comprobación del esquema al arrancar (FR-008, retoma T064-T065 de `003`)."""
from typing import Any

from consumer.queries import REGCLASS_CHECK

REQUIRED_TABLES = (
    "public.country", "public.date_dim",
    "live.current_event", "live.event_version", "live.quarantine",
    "replay.current_event", "replay.event_version", "replay.quarantine",
)


class SchemaNotReadyError(RuntimeError):
    """Falta una tabla que el consumidor necesita: el proceso termina y Compose lo reinicia."""


async def ensure_schema_ready(pool: Any) -> None:
    """Comprueba que existen las 8 tablas que usa el consumidor.

    Qué hace:
        Pregunta `to_regclass` por cada tabla; la primera que devuelve NULL lanza el error.
    Recibe:
        pool: pool de asyncpg (o doble con `fetchval`).
    Devuelve:
        Nada; lanza `SchemaNotReadyError` nombrando la tabla ausente.
    Por qué existe:
        Evita consumir mensajes contra una base sin esquema (no se comprueban columnas).
    """
    for table in REQUIRED_TABLES:
        if await pool.fetchval(REGCLASS_CHECK, table) is None:
            raise SchemaNotReadyError(f"falta la tabla {table} en la base de datos")
