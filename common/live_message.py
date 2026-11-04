"""Mensaje Kafka de un evento real del feed (kafka-message.md §2 y §3). Puro, sin E/S."""
from datetime import datetime, timezone

SOURCE_FEED = "usgs_feed"
MODE_LIVE = "live"
ISO_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def build_live_message(feature: dict, ingested_at: datetime) -> dict:
    """Construye el valor del mensaje con el evento sin modificar.

    Qué hace:
        Rellena el sobre del contrato: origen `usgs_feed`, modo `live`, `replay_at` nulo y
        `is_synthetic` falso; `event` es el mismo elemento recibido.
    Recibe:
        feature: elemento de `features`; ingested_at: instante de recepción del ciclo.
    Devuelve:
        Diccionario listo para serializar como JSON.
    Por qué existe:
        El consumidor espera exactamente este sobre; `mag` nulo o negativo viaja intacto (B7, B8).
    """
    return {
        "source": SOURCE_FEED,
        "mode": MODE_LIVE,
        "ingested_at": ingested_at.astimezone(timezone.utc).strftime(ISO_UTC_FORMAT),
        "replay_at": None,
        "is_synthetic": False,
        "event": feature,
    }


def message_key(feature: dict) -> str | None:
    """Devuelve la clave Kafka: el `id` del evento, o None si falta o no es texto."""
    event_id = feature.get("id")
    return event_id if isinstance(event_id, str) and event_id != "" else None
