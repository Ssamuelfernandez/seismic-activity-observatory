"""Pasos 1 a 3 de la validación: el sobre del mensaje y su coherencia con el tema (kafka-message.md §6).

Funciones puras. Cada `check_*` devuelve el motivo de cuarentena (`str`) o None si pasa.
"""
import re
from datetime import datetime, timezone
from typing import Any

from common.kafka_topics import topic_mode

SOURCES = frozenset({"usgs_feed", "usgs_historical", "replay_demo"})
MODES = frozenset({"live", "replay"})
ENVELOPE_KEYS = ("source", "mode", "ingested_at", "is_synthetic", "event")
TIMESTAMP_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?Z", re.ASCII)
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"
MICROSECOND_DIGITS = 6
INVALID_ENVELOPE = "invalid_envelope"
MODE_TOPIC_MISMATCH = "mode_topic_mismatch"
REPLAY_AT_MISSING = "replay_at_missing"


def parse_utc_timestamp(value: Any) -> datetime | None:
    """Convierte `AAAA-MM-DDThh:mm:ss[.f{1,9}]Z` en un `datetime` UTC, o None si no es válido.

    Qué hace:
        Exige la forma exacta del contrato y una fecha real; las fracciones se truncan a microsegundos.
    Recibe:
        value: valor del sobre (`ingested_at` o `replay_at`).
    Devuelve:
        `datetime` con zona UTC o None.
    Por qué existe:
        El sobre solo admite ese formato (kafka-message.md §3) y `fromisoformat` aceptaría otros.
    """
    match = TIMESTAMP_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return None
    fraction = (match.group(2) or "").ljust(MICROSECOND_DIGITS, "0")[:MICROSECOND_DIGITS]
    try:
        parsed = datetime.strptime(match.group(1), TIMESTAMP_FORMAT)
    except ValueError:
        return None
    return parsed.replace(microsecond=int(fraction or 0), tzinfo=timezone.utc)


def check_envelope(obj: Any) -> str | None:
    """Paso 1: el sobre es un objeto con sus claves, valores permitidos y fechas reales."""
    if not isinstance(obj, dict) or any(key not in obj for key in ENVELOPE_KEYS):
        return INVALID_ENVELOPE
    valid_values = (
        isinstance(obj["source"], str)
        and obj["source"] in SOURCES
        and isinstance(obj["mode"], str)
        and obj["mode"] in MODES
        and type(obj["is_synthetic"]) is bool
        and isinstance(obj["event"], dict)
        and parse_utc_timestamp(obj["ingested_at"]) is not None
    )
    replay_at = obj.get("replay_at")
    if not valid_values or (replay_at is not None and parse_utc_timestamp(replay_at) is None):
        return INVALID_ENVELOPE
    return None


def check_mode(envelope: dict, topic: str) -> str | None:
    """Pasos 2 y 3: el modo coincide con el tema y un replay trae `replay_at`."""
    if envelope["mode"] != topic_mode(topic):
        return MODE_TOPIC_MISMATCH
    if envelope["mode"] == "replay" and envelope.get("replay_at") is None:
        return REPLAY_AT_MISSING
    return None
