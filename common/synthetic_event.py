"""Construcción del mensaje Kafka de un evento sintético (kafka-message.md §3)."""
from datetime import datetime, timezone

SYNTHETIC_ID_PREFIX = "synthetic"
SYNTHETIC_PLACE = "Evento sintético de prueba (infra-compose)"
SYNTHETIC_MAGNITUDE = 1.0
SYNTHETIC_COORDINATES = [0.0, 0.0, 10.0]
SOURCE_DEMO = "replay_demo"
MODE_LIVE = "live"


def build_synthetic_event_id(now: datetime) -> str:
    """Devuelve un identificador único por segundo, con prefijo `synthetic`.

    Por qué existe:
        Ningún identificador sintético debe confundirse con uno real de USGS (FR-010).
    """
    return f"{SYNTHETIC_ID_PREFIX}-{int(now.timestamp())}"


def build_synthetic_message(event_id: str, now: datetime) -> dict:
    """Construye el valor del mensaje de un evento sintético.

    Qué hace:
        Rellena el sobre del contrato con `is_synthetic = true` y un evento GeoJSON ficticio.
    Recibe:
        event_id: identificador del evento; now: instante de publicación (UTC).
    Devuelve:
        Diccionario listo para serializar como JSON.
    Por qué existe:
        El «hola mundo» de punta a punta necesita un mensaje válido y marcado como sintético
        (constitución §7, A1).
    """
    # Supera ~30 líneas por el docstring de la plantilla (§7.4); el cuerpo son 22 líneas y hace una sola cosa: armar el mensaje.
    now_ms = int(now.timestamp() * 1000)
    return {
        "source": SOURCE_DEMO,
        "mode": MODE_LIVE,
        "ingested_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "replay_at": None,
        "is_synthetic": True,
        "event": {
            "type": "Feature",
            "properties": {
                "mag": SYNTHETIC_MAGNITUDE,
                "place": SYNTHETIC_PLACE,
                "time": now_ms,
                "updated": now_ms,
                "magType": "ml",
                "type": "earthquake",
                "title": f"M {SYNTHETIC_MAGNITUDE} - {SYNTHETIC_PLACE}",
            },
            "geometry": {"type": "Point", "coordinates": SYNTHETIC_COORDINATES},
            "id": event_id,
        },
    }
