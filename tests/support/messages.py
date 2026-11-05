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


MADRID = (-3.70, 40.42)
ATLANTIC = (-30.0, 35.0)
GEO_PREFIX = "synthetic-geo-"
GEO_DEPTH = 10.0
GEO_TIME_MS = E1_TIME_MS
GEO_UPDATED_MS = E1_UPDATED_1005
GEO_PLACE_ELSEWHERE = "5 km de París, Francia"
NEGATIVE_MAG = -0.06
NEGATIVE_DEPTH = -0.18
INVALID_LATITUDE = 145


def build_geo_message(case: str, lon: float, lat: float, *, mag: float | None = 3.0,
                      depth: float = GEO_DEPTH, place: str = "Lugar sintético de prueba") -> dict:
    """Mensaje sintético de F5 (`synthetic-geo-<caso>`) con coordenadas y magnitud a medida."""
    event = build_event(f"{GEO_PREFIX}{case}", GEO_TIME_MS, GEO_UPDATED_MS, mag)
    event["geometry"]["coordinates"] = [lon, lat, depth]
    event["properties"]["place"] = place
    return build_message(event)


def geo_cases() -> dict[str, dict]:
    """Los 9 casos de la feature geografía-país, todos sintéticos (`is_synthetic = true`).

    Qué hace:
        Construye madrid, atlantico, mag-nula, negativos, lat-145, lon-nan, no-point,
        sin-time y sin-updated con ids `synthetic-geo-<caso>`.
    Devuelve:
        Diccionario caso -> mensaje (sobre del contrato).
    Por qué existe:
        Las pruebas 5, 6 y 7 y el escenario `geo` comparten los mismos mensajes (C9, C12, C13).
    """
    madrid_lon, madrid_lat = MADRID
    cases = {
        "madrid": build_geo_message("madrid", madrid_lon, madrid_lat, place=GEO_PLACE_ELSEWHERE),
        "atlantico": build_geo_message("atlantico", *ATLANTIC),
        "mag-nula": build_geo_message("mag-nula", madrid_lon, madrid_lat, mag=None),
        "negativos": build_geo_message("negativos", madrid_lon, madrid_lat, mag=NEGATIVE_MAG, depth=NEGATIVE_DEPTH),
        "lat-145": build_geo_message("lat-145", madrid_lon, INVALID_LATITUDE),
        "lon-nan": build_geo_message("lon-nan", float("nan"), madrid_lat),
        "no-point": build_geo_message("no-point", madrid_lon, madrid_lat),
        "sin-time": build_geo_message("sin-time", madrid_lon, madrid_lat),
        "sin-updated": build_geo_message("sin-updated", madrid_lon, madrid_lat),
    }
    cases["no-point"]["event"]["geometry"] = {"type": "LineString", "coordinates": [[madrid_lon, madrid_lat], [0, 0]]}
    del cases["sin-time"]["event"]["properties"]["time"]
    del cases["sin-updated"]["event"]["properties"]["updated"]
    return cases


def to_bytes(message: dict) -> bytes:
    """Serializa un mensaje como lo haría el productor (JSON UTF-8)."""
    return json.dumps(message).encode("utf-8")
