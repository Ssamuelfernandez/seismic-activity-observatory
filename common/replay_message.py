"""Mensaje Kafka del replay y bloque controlado (kafka-message.md §3, data-model de replay). Puro, sin E/S."""
from dataclasses import dataclass
from datetime import datetime, timezone

from common.live_message import ISO_UTC_FORMAT

SOURCE_REPLAY = "replay_demo"
MODE_REPLAY = "replay"

E1_ID = "synthetic-replay-e1"
E2_ID = "synthetic-replay-e2"
SYNTHETIC_PLACE = "Sintético: bloque controlado del replay"
SYNTHETIC_LON = -70.0
SYNTHETIC_LAT = -22.0
SYNTHETIC_DEPTH_KM = 10.0


def _utc_ms(hour: int, minute: int, day: int = 30) -> int:
    """Milisegundos Unix de un instante de enero de 2025 (UTC)."""
    moment = datetime(2025, 1, day, hour, minute, tzinfo=timezone.utc)
    return int(moment.timestamp() * 1000)


E1_TIME_MS = _utc_ms(12, 0)
E2_TIME_MS = _utc_ms(12, 30)
E1_UPDATED_V1 = _utc_ms(10, 5)
E1_UPDATED_MIDDLE = _utc_ms(10, 7)
E1_UPDATED_V2 = _utc_ms(10, 9)
E2_UPDATED = _utc_ms(10, 12)
E1_MAG_V1 = 4.2
E1_MAG_MIDDLE = 4.4
E1_MAG_V2 = 4.6
E2_MAG = 3.1


@dataclass(frozen=True)
class ReplayItem:
    """Un elemento a publicar: el evento, si es sintético y su instante de ingesta."""

    feature: dict
    is_synthetic: bool
    ingested_at: datetime


def _format_utc(moment: datetime) -> str:
    """Formatea un instante como texto UTC con `Z`."""
    return moment.astimezone(timezone.utc).strftime(ISO_UTC_FORMAT)


def build_replay_message(item: ReplayItem, replay_at: datetime) -> dict:
    """Construye el valor del mensaje del replay con el evento sin modificar.

    Qué hace:
        Rellena el sobre del contrato: origen `replay_demo`, modo `replay`, `replay_at` con
        el instante de publicación; `event` es el mismo objeto recibido.
    Recibe:
        item: elemento a publicar; replay_at: instante UTC de publicación.
    Devuelve:
        Diccionario listo para serializar como JSON.
    Por qué existe:
        El consumidor espera este sobre; `time` y `updated` originales viajan intactos (J2, J6).
    """
    return {
        "source": SOURCE_REPLAY,
        "mode": MODE_REPLAY,
        "ingested_at": _format_utc(item.ingested_at),
        "replay_at": _format_utc(replay_at),
        "is_synthetic": item.is_synthetic,
        "event": item.feature,
    }


def _synthetic_feature(event_id: str, time_ms: int, updated_ms: int, mag: float) -> dict:
    """Feature GeoJSON sintética mínima y válida dentro de la zona `chile-norte`."""
    return {
        "type": "Feature",
        "properties": {
            "mag": mag,
            "place": SYNTHETIC_PLACE,
            "time": time_ms,
            "updated": updated_ms,
            "status": "reviewed",
            "url": f"https://example.invalid/{event_id}",
            "sig": 100,
            "magType": "ml",
            "type": "earthquake",
        },
        "geometry": {"type": "Point", "coordinates": [SYNTHETIC_LON, SYNTHETIC_LAT, SYNTHETIC_DEPTH_KM]},
        "id": event_id,
    }


def build_controlled_block(started_at: datetime) -> list[ReplayItem]:
    """Devuelve los 6 elementos sintéticos del bloque controlado, en orden de publicación.

    Qué hace:
        E1 v1, E1 v1 repetido, E1 v2, E1 v1 repetido tarde, E2 y E1 intermedia.
    Recibe:
        started_at: instante de arranque del replay, usado como `ingested_at`.
    Devuelve:
        Lista de 6 `ReplayItem` con `is_synthetic = True`.
    Por qué existe:
        Demuestra reenvío, versión posterior y versión antigua tardía (J6, FR-012).
    """
    e1_v1 = _synthetic_feature(E1_ID, E1_TIME_MS, E1_UPDATED_V1, E1_MAG_V1)
    e1_v2 = _synthetic_feature(E1_ID, E1_TIME_MS, E1_UPDATED_V2, E1_MAG_V2)
    e1_middle = _synthetic_feature(E1_ID, E1_TIME_MS, E1_UPDATED_MIDDLE, E1_MAG_MIDDLE)
    e2 = _synthetic_feature(E2_ID, E2_TIME_MS, E2_UPDATED, E2_MAG)
    sequence = [e1_v1, e1_v1, e1_v2, e1_v1, e2, e1_middle]
    return [ReplayItem(feature, True, started_at) for feature in sequence]
