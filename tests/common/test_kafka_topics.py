"""Pruebas de `topic_mode` (T015)."""
import pytest

from common.kafka_topics import topic_mode


def test_topic_mode_live() -> None:
    assert topic_mode("earthquakes.live") == "live"


def test_topic_mode_replay() -> None:
    assert topic_mode("earthquakes.replay") == "replay"


def test_topic_mode_unknown_topic_raises_with_name() -> None:
    with pytest.raises(ValueError, match="otro.tema"):
        topic_mode("otro.tema")
