"""Mensajes de prueba compartidos por unitarias, integración y publicador (T014).

Todos los datos son SINTÉTICOS (`is_synthetic = true`, ids `synthetic-...`), salvo
`build_real_looking_message`, que existe solo para la base temporal de pruebas (SC-008).
"""
import json
from copy import deepcopy

FAQ12_E1 = "synthetic-faq12-e1"
FAQ12_E2 = "synthetic-faq12-e2"
SOURCE_DEMO = "replay_demo"
SOURCE_FEED = "usgs_feed"
INGESTED_AT = "2026-11-04T10:00:00Z"
REPLAY_AT = "2026-11-04T10:30:00Z"

E1_TIME_MS = 1793786400000  # 2026-11-04T10:00:00Z
E1_UPDATED_1005 = 1793786700000
E1_UPDATED_1007 = 1793786820000  # versión antigua tardía, no vista
E1_UPDATED_1009 = 1793786940000
E2_TIME_MS = 1793787060000  # 10:11
E2_UPDATED_1012 = 1793787120000

DEFAULT_COORDINATES = (-116.7, 33.54, 6.4)


def build_event(event_id: str, time_ms: int, updated_ms: int, mag: float | None) -> dict:
    """Construye el objeto `event` (Feature GeoJSON) mínimo y válido."""
    return {
        "type": "Feature",
        "properties": {
            "mag": mag,
            "place": "Lugar sintético de prueba",
            "time": time_ms,
            "updated": updated_ms,
            "status": "reviewed",
            "url": f"https://example.invalid/{event_id}",
            "sig": 100,
            "magType": "ml",
            "type": "earthquake",
        },
        "geometry": {"type": "Point", "coordinates": list(DEFAULT_COORDINATES)},
        "id": event_id,
    }


def build_message(
    event: dict,
    *,
    source: str = SOURCE_DEMO,
    mode: str = "live",
    is_synthetic: bool = True,
    replay_at: str | None = None,
) -> dict:
    """Construye el sobre del contrato (kafka-message.md §3) alrededor de un `event`."""
    return {
        "source": source,
        "mode": mode,
        "ingested_at": INGESTED_AT,
        "replay_at": replay_at,
        "is_synthetic": is_synthetic,
        "event": event,
    }


def build_synthetic_message(event_id: str, time_ms: int, updated_ms: int, mag: float | None) -> dict:
    """Mensaje live sintético (`source = replay_demo`, `is_synthetic = true`)."""
    return build_message(build_event(event_id, time_ms, updated_ms, mag))


def build_real_looking_message(event_id: str, time_ms: int, updated_ms: int, mag: float | None) -> dict:
    """Mensaje con `is_synthetic = false`: SOLO para la base temporal de pruebas (SC-008).

    Nunca debe publicarse en Kafka ni escribirse en la base de la aplicación.
    """
    return build_message(build_event(event_id, time_ms, updated_ms, mag), source=SOURCE_FEED, is_synthetic=False)


def faq12_sequence() -> list[dict]:
    """Secuencia de 5 mensajes de la FAQ 12 (data-model.md §4)."""
    e1_v1 = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    e1_v2 = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1009, 4.6)
    e2 = build_synthetic_message(FAQ12_E2, E2_TIME_MS, E2_UPDATED_1012, 3.1)
    return [e1_v1, deepcopy(e1_v1), e1_v2, deepcopy(e1_v1), e2]


def late_old_version_message() -> dict:
    """E1 con `updated` 10:07 y mag 4.4: versión antigua tardía no vista (prueba 4)."""
    return build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1007, 4.4)


def to_bytes(message: dict) -> bytes:
    """Serializa un mensaje como lo haría el productor (JSON UTF-8)."""
    return json.dumps(message).encode("utf-8")
