"""Pruebas de la coherencia entre el intervalo del productor y la caducidad del latido."""
import pytest

from common.config import HealthSettings
from producer.loop import validate_interval_against_health

HEALTH = HealthSettings(heartbeat_file="/tmp/producer.alive", max_age_seconds=120)


def test_interval_that_leaves_room_for_the_heartbeat_is_accepted():
    validate_interval_against_health(60, HEALTH)


def test_interval_longer_than_half_the_max_age_is_rejected():
    with pytest.raises(ValueError, match="PRODUCER_INTERVAL_SECONDS"):
        validate_interval_against_health(61, HEALTH)
