"""Arnés del replay para integración: los 26 mensajes reales y el bloque controlado, sin Kafka.

Los 20 eventos son REALES (de `data/historical/`, zona `chile-norte`); los 6 del bloque
controlado son SINTÉTICOS (`synthetic-replay-e1/e2`). Los mensajes pasan por las funciones
reales del consumidor (`tests/support/db_helpers.py::process_raw`) contra PostgreSQL real.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from common.kafka_topics import TOPIC_REPLAY
from common.replay_message import build_replay_message
from producer.replay import DEFAULT_COUNT, build_items
from producer.replay_selection import ZONES, select_events
from producer.replay_source import load_verified_features
from tests.support.db_helpers import process_raw, to_raw

DATA_DIR = Path(os.environ.get("REPLAY_DATA_DIR", "data/historical"))
STARTED_AT = datetime(2026, 11, 12, 10, 0, 0, tzinfo=timezone.utc)
SYNTHETIC_PREFIX = "synthetic-replay-"


def build_replay_messages(started_at: datetime = STARTED_AT) -> list[dict]:
    """Devuelve los 26 mensajes del replay, con `replay_at` creciente (un segundo entre cada uno)."""
    pairs = load_verified_features(DATA_DIR)
    selected = select_events(pairs, ZONES["chile-norte"], DEFAULT_COUNT)
    items = build_items(selected, started_at)
    return [build_replay_message(item, started_at + timedelta(seconds=index)) for index, item in enumerate(items)]


async def process_messages(conn: Any, messages: list[dict], topic: str = TOPIC_REPLAY, first_offset: int = 0) -> list:
    """Procesa cada mensaje con el consumidor real y devuelve los resultados en orden."""
    return [await process_raw(conn, to_raw(message), first_offset + index, topic)
            for index, message in enumerate(messages)]
