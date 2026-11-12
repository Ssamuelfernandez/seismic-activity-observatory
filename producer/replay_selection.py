"""Selección de eventos reales para el replay (J1). Puro, sin E/S."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    """Caja geográfica en grados."""

    name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


DEFAULT_ZONE = "chile-norte"
ZONES = {
    "chile-norte": Zone("chile-norte", -27.0, -18.0, -72.0, -68.5),
    "japon-honshu": Zone("japon-honshu", 35.0, 41.0, 139.0, 142.5),
}


def _position(feature: dict) -> tuple[float, float] | None:
    """Devuelve (lon, lat) de la feature, o None si no tiene coordenadas numéricas."""
    geometry = feature.get("geometry")
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    lon, lat = coordinates[0], coordinates[1]
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return None
    return float(lon), float(lat)


def _in_zone(feature: dict, zone: Zone) -> bool:
    """Indica si la feature cae dentro de la caja de la zona (bordes incluidos)."""
    position = _position(feature)
    if position is None:
        return False
    lon, lat = position
    return zone.lat_min <= lat <= zone.lat_max and zone.lon_min <= lon <= zone.lon_max


def _time_of(feature: dict) -> int | None:
    """Devuelve `properties.time` (ms) si es entero."""
    properties = feature.get("properties")
    value = properties.get("time") if isinstance(properties, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def select_events(pairs: list[tuple[dict, str]], zone: Zone, count: int) -> list[tuple[dict, str]]:
    """Elige los primeros `count` eventos de la zona, ordenados por `(time, id)`.

    Qué hace:
        Descarta los de fuera de la caja o sin `time` o `id`, conserva un solo evento por `id`
        y devuelve los primeros `count` en orden ascendente.
    Recibe:
        pairs: pares `(feature, extracted_at)`; zone: caja; count: máximo a devolver.
    Devuelve:
        Lista de pares; con menos eventos que `count` devuelve los que hay.
    Por qué existe:
        El orden determinista hace el replay repetible (J1, FR-002, FR-003).
    """
    candidates = []
    for feature, extracted_at in pairs:
        event_id = feature.get("id")
        time_ms = _time_of(feature)
        if not isinstance(event_id, str) or time_ms is None or not _in_zone(feature, zone):
            continue
        candidates.append((time_ms, event_id, feature, extracted_at))
    candidates.sort(key=lambda row: (row[0], row[1]))
    seen: set[str] = set()
    selected: list[tuple[dict, str]] = []
    for _, event_id, feature, extracted_at in candidates:
        if event_id in seen:
            continue
        seen.add(event_id)
        selected.append((feature, extracted_at))
        if len(selected) == count:
            break
    return selected
