"""Pruebas de common/synthetic_event.py: el mensaje cumple kafka-message.md §3 y va marcado."""
from datetime import datetime, timezone

from common.kafka_topics import TOPIC_RETENTION_MS, build_topic
from common.synthetic_event import build_synthetic_event_id, build_synthetic_message

NOW = datetime(2026, 11, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_event_id_has_synthetic_prefix():
    assert build_synthetic_event_id(NOW).startswith("synthetic-")


def test_event_ids_differ_between_seconds():
    later = datetime(2026, 11, 3, 12, 0, 1, tzinfo=timezone.utc)
    assert build_synthetic_event_id(NOW) != build_synthetic_event_id(later)


def test_message_is_marked_synthetic_and_live():
    message = build_synthetic_message("synthetic-1", NOW)
    assert message["is_synthetic"] is True
    assert message["mode"] == "live"
    assert message["replay_at"] is None
    assert message["source"] == "replay_demo"


def test_message_has_all_required_envelope_fields():
    message = build_synthetic_message("synthetic-1", NOW)
    assert {"source", "mode", "ingested_at", "replay_at", "is_synthetic", "event"} <= set(message)
    assert message["ingested_at"] == "2026-11-03T12:00:00Z"


def test_event_keeps_times_in_milliseconds_and_id():
    event = build_synthetic_message("synthetic-1", NOW)["event"]
    assert event["id"] == "synthetic-1"
    assert event["properties"]["time"] == int(NOW.timestamp() * 1000)
    assert event["properties"]["type"] == "earthquake"
    assert event["geometry"]["type"] == "Point"


def test_topic_definition_matches_contract():
    topic = build_topic("earthquakes.live")
    assert topic.num_partitions == 1
    assert topic.replication_factor == 1
    assert topic.topic_configs["retention.ms"] == str(TOPIC_RETENTION_MS) == "604800000"
