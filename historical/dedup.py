"""Deduplicación de features por id y `updated`. Puro, sin E/S (B14, research D6)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DedupResult:
    """Features únicas y número de descartadas."""

    features: list[dict]
    discarded: int


def _group_key(feature: dict) -> tuple[str, int] | None:
    """Devuelve (id, updated) si la feature es agrupable; None si no lo es."""
    event_id = feature.get("id")
    properties = feature.get("properties")
    updated = properties.get("updated") if isinstance(properties, dict) else None
    if not isinstance(event_id, str) or event_id == "":
        return None
    if not isinstance(updated, int) or isinstance(updated, bool):
        return None
    return event_id, updated


def dedup_features(feature_lists: list[list[dict]]) -> DedupResult:
    """Conserva una feature por `id`: la de `updated` mayor, y la primera si empatan.

    Qué hace:
        Recorre las listas en orden. Las features sin `id` o con `updated` no entero
        pasan tal cual, sin agrupar, para que la validación las mande a cuarentena.
    Recibe:
        feature_lists: features de cada archivo, en el orden del manifiesto.
    Devuelve:
        `DedupResult` con las únicas (orden de primera aparición) y las descartadas.
    Por qué existe:
        Un evento puede aparecer en dos consultas; no debe contarse dos veces (B14, SC-003).
    """
    slots: list[dict] = []
    best: dict[str, tuple[int, int]] = {}
    discarded = 0
    for features in feature_lists:
        for feature in features:
            key = _group_key(feature)
            if key is None:
                slots.append(feature)
                continue
            event_id, updated = key
            if event_id not in best:
                best[event_id] = (len(slots), updated)
                slots.append(feature)
                continue
            discarded += 1
            position, current = best[event_id]
            if updated > current:
                slots[position] = feature
                best[event_id] = (position, updated)
    return DedupResult(slots, discarded)
