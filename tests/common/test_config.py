"""Pruebas de common/config.py: variables obligatorias y rangos (A10, FR-036)."""
import pytest

from common.config import (
    DEFAULT_USGS_FEED_URL, ConfigError, load_feed_settings, read_int, read_optional_int, read_str,
    validate_poll_against_health,
)


def test_read_str_missing_variable_names_it(monkeypatch):
    monkeypatch.delenv("KAFKA_TOPIC", raising=False)
    with pytest.raises(ConfigError, match="KAFKA_TOPIC"):
        read_str("KAFKA_TOPIC")


def test_read_str_empty_value_is_rejected(monkeypatch):
    monkeypatch.setenv("KAFKA_TOPIC", "")
    with pytest.raises(ConfigError, match="KAFKA_TOPIC"):
        read_str("KAFKA_TOPIC")


def test_read_str_uses_default_when_missing(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert read_str("LOG_LEVEL", "INFO") == "INFO"


def test_read_int_rejects_non_integer(monkeypatch):
    monkeypatch.setenv("DB_PORT", "abc")
    with pytest.raises(ConfigError, match="DB_PORT"):
        read_int("DB_PORT")


def test_read_int_rejects_out_of_range(monkeypatch):
    monkeypatch.setenv("PRODUCER_INTERVAL_SECONDS", "0")
    with pytest.raises(ConfigError, match="PRODUCER_INTERVAL_SECONDS"):
        read_int("PRODUCER_INTERVAL_SECONDS", minimum=1, maximum=60)


def test_read_int_accepts_value_in_range(monkeypatch):
    monkeypatch.setenv("PRODUCER_INTERVAL_SECONDS", "30")
    assert read_int("PRODUCER_INTERVAL_SECONDS", minimum=1, maximum=60) == 30


def test_read_optional_int_missing_returns_none(monkeypatch):
    monkeypatch.delenv("CONSUMER_FAULT_CRASH_AT_OFFSET", raising=False)
    assert read_optional_int("CONSUMER_FAULT_CRASH_AT_OFFSET") is None


def test_read_optional_int_empty_returns_none(monkeypatch):
    monkeypatch.setenv("CONSUMER_FAULT_CRASH_AT_OFFSET", "")
    assert read_optional_int("CONSUMER_FAULT_CRASH_AT_OFFSET") is None


def test_read_optional_int_valid_value(monkeypatch):
    monkeypatch.setenv("CONSUMER_FAULT_CRASH_AT_OFFSET", "2")
    assert read_optional_int("CONSUMER_FAULT_CRASH_AT_OFFSET") == 2


def test_read_optional_int_rejects_non_integer(monkeypatch):
    monkeypatch.setenv("CONSUMER_FAULT_CRASH_AT_OFFSET", "abc")
    with pytest.raises(ConfigError, match="CONSUMER_FAULT_CRASH_AT_OFFSET"):
        read_optional_int("CONSUMER_FAULT_CRASH_AT_OFFSET")


def test_read_optional_int_rejects_negative(monkeypatch):
    monkeypatch.setenv("CONSUMER_FAULT_CRASH_AT_OFFSET", "-1")
    with pytest.raises(ConfigError, match="CONSUMER_FAULT_CRASH_AT_OFFSET"):
        read_optional_int("CONSUMER_FAULT_CRASH_AT_OFFSET")


FEED_VARIABLES = ("POLL_SECONDS", "USGS_FEED_URL", "HTTP_TIMEOUT_SECONDS", "RAW_RETENTION_DAYS")


@pytest.fixture
def clean_feed_env(monkeypatch):
    for name in FEED_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_feed_settings_defaults(clean_feed_env):
    settings = load_feed_settings()
    assert settings.poll_seconds == 60
    assert settings.url == DEFAULT_USGS_FEED_URL
    assert settings.url.endswith("all_day.geojson")
    assert settings.timeout_seconds == 10
    assert settings.raw_retention_days == 7


def test_feed_settings_read_overrides(clean_feed_env):
    clean_feed_env.setenv("POLL_SECONDS", "30")
    clean_feed_env.setenv("USGS_FEED_URL", "http://localhost:9999/feed.geojson")
    clean_feed_env.setenv("HTTP_TIMEOUT_SECONDS", "5")
    clean_feed_env.setenv("RAW_RETENTION_DAYS", "3")
    settings = load_feed_settings()
    assert (settings.poll_seconds, settings.timeout_seconds, settings.raw_retention_days) == (30, 5, 3)
    assert settings.url == "http://localhost:9999/feed.geojson"


def test_feed_url_without_scheme_is_rejected(clean_feed_env):
    clean_feed_env.setenv("USGS_FEED_URL", "earthquake.usgs.gov/feed.geojson")
    with pytest.raises(ConfigError, match="USGS_FEED_URL"):
        load_feed_settings()


def test_retention_days_zero_is_rejected(clean_feed_env):
    clean_feed_env.setenv("RAW_RETENTION_DAYS", "0")
    with pytest.raises(ConfigError, match="RAW_RETENTION_DAYS"):
        load_feed_settings()


@pytest.mark.parametrize("name,value", [("POLL_SECONDS", "0"), ("HTTP_TIMEOUT_SECONDS", "61"),
                                        ("HTTP_TIMEOUT_SECONDS", "0")])
def test_feed_numeric_ranges_are_rejected(clean_feed_env, name, value):
    clean_feed_env.setenv(name, value)
    with pytest.raises(ConfigError, match=name):
        load_feed_settings()


def test_poll_that_leaves_room_for_the_heartbeat_is_accepted():
    validate_poll_against_health(60, 120)


def test_poll_longer_than_half_the_max_age_names_the_variable():
    with pytest.raises(ConfigError, match="POLL_SECONDS"):
        validate_poll_against_health(61, 120)
