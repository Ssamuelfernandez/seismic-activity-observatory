"""Reglas puras de versión de un evento (C4, FR-005 a FR-009, data-model.md §3).

Ninguna función registra nada: el aviso `inconsistent_state` lo escribe `consumer/writer.py`.
"""
from common.records import VersionOutcome


def is_newer_version(incoming_updated_ms: int, stored_updated_ms: int | None) -> bool:
    """Decide si una versión recibida debe sustituir al estado actual.

    Qué hace:
        Compara el `updated` entrante con el guardado. Solo gana si es estrictamente mayor.
    Recibe:
        incoming_updated_ms: `updated` de la versión recibida (ms Unix).
        stored_updated_ms: `updated` guardado, o None si el evento no existe.
    Devuelve:
        True si hay que actualizar; False si es igual o más antigua.
    Por qué existe:
        Evita que una versión antigua que llega tarde pise a la reciente (C4, prueba 4).
    """
    return stored_updated_ms is None or incoming_updated_ms > stored_updated_ms


def is_inconsistent_state(stored_updated_ms: int | None, incoming_updated_ms: int, version_inserted: bool) -> bool:
    """Detecta una fila actual sin su versión (imposible si solo escribe este consumidor).

    Qué hace:
        Es verdadero solo si el `updated` guardado es igual al entrante y la versión se
        acaba de insertar.
    Recibe:
        stored_updated_ms: `updated` actual o None; incoming_updated_ms: el entrante;
        version_inserted: si la sentencia sobre `event_version` insertó una fila.
    Devuelve:
        True en ese único caso.
    Por qué existe:
        Permite al escritor avisar sin que la decisión pura registre ni lance (FR-009).
    """
    return version_inserted and stored_updated_ms == incoming_updated_ms


def decide_version_outcome(
    stored_updated_ms: int | None,
    incoming_updated_ms: int,
    version_inserted: bool,
    content_differs: bool,
) -> VersionOutcome:
    """Decide qué ocurrió con una versión según la tabla de data-model.md §3.

    Qué hace:
        Sin inserción nueva: reenvío, o conflicto si el contenido difiere. Con inserción:
        evento nuevo, versión más reciente o versión antigua tardía (también con `updated`
        igual, estado inconsistente, que nunca sustituye ni lanza).
    Recibe:
        stored_updated_ms: `updated` de `current_event` antes de escribir, o None.
        incoming_updated_ms: `updated` del mensaje.
        version_inserted: si `event_version` insertó fila.
        content_differs: si el `original` guardado difiere del recibido (solo importa
            cuando no se insertó).
    Devuelve:
        El VersionOutcome correspondiente.
    Por qué existe:
        Concentra la regla de versiones para que el escritor, `historico-2025` y `replay`
        decidan igual (C4, FR-005 a FR-008, constitución §2).
    """
    if not version_inserted:
        return VersionOutcome.SAME_UPDATED_CONFLICT if content_differs else VersionOutcome.REDELIVERY
    if stored_updated_ms is None:
        return VersionOutcome.NEW_EVENT
    if is_newer_version(incoming_updated_ms, stored_updated_ms):
        return VersionOutcome.NEWER_VERSION
    return VersionOutcome.LATE_OLD_VERSION
