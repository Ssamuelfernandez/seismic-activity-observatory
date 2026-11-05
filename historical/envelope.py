"""Mensaje del contrato para un evento histórico (kafka-message.md §3), sin Kafka. Puro (B16)."""
import json
from datetime import datetime, timezone

SOURCE_HISTORICAL = "usgs_historical"
MODE_LIVE = "live"
ISO_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
JSON_SEPARATORS = (",", ":")


def build_message_bytes(feature: dict, extracted_at: datetime, is_synthetic: bool = False) -> bytes:
    """Serializa el mensaje de un evento histórico con bytes estables.

    Qué hace:
        Rellena el sobre del contrato (`usgs_historical`, modo `live`, `replay_at` nulo)
        con la feature sin modificar y `ingested_at` igual a la fecha de extracción.
    Recibe:
        feature: elemento de `features`; extracted_at: fecha de extracción del archivo;
        is_synthetic: verdadero solo en fixtures de prueba.
    Devuelve:
        Bytes JSON UTF-8 con claves ordenadas y separadores fijos: dos llamadas iguales dan
        los mismos bytes, así el sha256 de cuarentena es estable al recargar (research D1).
    Por qué existe:
        El cargador entrega esto a `process_record` igual que si viniera de Kafka (B16, FR-010).
    """
    message = {
        "source": SOURCE_HISTORICAL,
        "mode": MODE_LIVE,
        "ingested_at": extracted_at.astimezone(timezone.utc).strftime(ISO_UTC_FORMAT),
        "replay_at": None,
        "is_synthetic": is_synthetic,
        "event": feature,
    }
    return json.dumps(message, sort_keys=True, separators=JSON_SEPARATORS, ensure_ascii=False).encode("utf-8")
