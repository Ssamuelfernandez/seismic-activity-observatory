"""Decisión de publicar, omitir o excluir un evento del feed (B3, B6, research.md §3). Puro, sin E/S."""
from datetime import datetime
from enum import Enum

EARTHQUAKE_TYPE = "earthquake"
EXCLUSION_KIND = "non_earthquake_type"
EXCLUSION_REASON = "properties.type distinto de earthquake"


class Decision(Enum):
    """Qué hace el productor con un elemento de `features`."""

    PUBLISH = "publish"
    PUBLISH_UNMARKED = "publish_unmarked"
    SKIP = "skip"
    EXCLUDE = "exclude"


def _properties(feature: dict) -> dict:
    """Devuelve `properties` o un diccionario vacío si falta o no es un objeto."""
    properties = feature.get("properties")
    return properties if isinstance(properties, dict) else {}


def _comparable_identity(feature: dict) -> tuple[str, int] | None:
    """Devuelve (id, updated) si se pueden comparar: id texto no vacío y updated entero no booleano."""
    event_id = feature.get("id")
    updated = _properties(feature).get("updated")
    if not isinstance(event_id, str) or event_id == "":
        return None
    if not isinstance(updated, int) or isinstance(updated, bool):
        return None
    return event_id, updated


def decide_publication(feature: dict, last_updated_ms: int | None) -> Decision:
    """Decide qué hacer con un elemento según la tabla de research.md §3.

    Qué hace:
        La invalidez (sin `id` o `updated` comparables) prevalece: se publica sin marca.
        Después, un `type` distinto de `earthquake` (o ausente) se excluye; por último se
        publica solo lo nuevo o con `updated` estrictamente mayor.
    Recibe:
        feature: elemento del feed; last_updated_ms: `updated` ya publicado, o None.
    Devuelve:
        La decisión.
    Por qué existe:
        Es la regla que evita republicar lo ya publicado (B6, FR-005).
    """
    identity = _comparable_identity(feature)
    if identity is None:
        return Decision.PUBLISH_UNMARKED
    if _properties(feature).get("type") != EARTHQUAKE_TYPE:
        return Decision.EXCLUDE
    if last_updated_ms is None or identity[1] > last_updated_ms:
        return Decision.PUBLISH
    return Decision.SKIP


def build_exclusion_row(feature: dict, fetched_at: datetime) -> dict:
    """Construye la fila de `live.exclusion` de un elemento excluido (data-model.md §2).

    Qué hace:
        Anota identificador, `updated`, tipo observado (nulo si falta) y el instante de la consulta.
    Recibe:
        feature: elemento con `id` y `updated` comparables; fetched_at: recepción del ciclo.
    Devuelve:
        Diccionario con las columnas de la tabla.
    Por qué existe:
        Lo excluido queda registrado y no se pierde en silencio (B3).
    """
    return {
        "event_id": feature["id"],
        "updated_ms": _properties(feature)["updated"],
        "kind": EXCLUSION_KIND,
        "reason": EXCLUSION_REASON,
        "observed_type": _properties(feature).get("type"),
        "fetched_at": fetched_at,
        "is_synthetic": False,
    }
