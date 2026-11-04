"""Gancho de prueba entre el commit de PostgreSQL y el del offset (prueba 8, SC-005, C2).

Solo se instala si `CONSUMER_FAULT_CRASH_AT_OFFSET` no está vacía (`consumer/main.py`); con la
variable vacía no existe ningún camino distinto del normal. Contrato: `consumer-runtime.md` §2.
"""
import logging
import os
from collections.abc import Callable
from pathlib import Path

from common.records import MessageRef

logger = logging.getLogger(__name__)

FAULT_MARKER_PATH = "/tmp/consumer_fault_done"
FAULT_EXIT_CODE = 137

# Firma de `after_db_commit`: recibe la referencia del mensaje y su marca `is_synthetic`.
AfterDbCommit = Callable[[MessageRef, bool], None]


def crash_once_at_offset(offset: int, marker_path: str, exit_fn: Callable[[int], None] = os._exit) -> AfterDbCommit:
    """Crea el gancho que termina el proceso una sola vez tras guardar el mensaje de `offset`.

    Qué hace:
        El gancho devuelto no hace nada en otro offset, con un mensaje no sintético o si el
        marcador ya existe; si no, escribe el marcador, registra
        `FAULT crash_after_db_commit offset=N` y llama a `exit_fn(137)`.
    Recibe:
        offset: offset del mensaje tras cuyo commit en PostgreSQL se corta; marker_path:
        archivo que evita volver a morir tras el reinicio; exit_fn: salida (`os._exit`;
        un doble en las pruebas).
    Devuelve:
        La función `after_db_commit(ref, is_synthetic)`.
    Por qué existe:
        Demuestra con Kafka real que un corte entre ambos commits no pierde ni duplica datos
        (C2, SC-005). Un dato real (`is_synthetic = false`) nunca lo dispara.
    """
    marker = Path(marker_path)

    def after_db_commit(ref: MessageRef, is_synthetic: bool) -> None:
        if not is_synthetic or ref.offset != offset or marker.exists():
            return
        marker.write_text("crash_after_db_commit\n", encoding="utf-8")
        logger.warning("FAULT crash_after_db_commit offset=%d", offset)
        exit_fn(FAULT_EXIT_CODE)

    return after_db_commit


def build_fault_hook(offset: int | None) -> AfterDbCommit | None:
    """Devuelve el gancho de caída para ese offset, o None si la variable está vacía."""
    if offset is None:
        return None
    return crash_once_at_offset(offset, FAULT_MARKER_PATH)
