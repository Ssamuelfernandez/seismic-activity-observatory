"""Pruebas de common/config.py: variables obligatorias y rangos (A10, FR-036)."""
import pytest

from common.config import ConfigError, read_int, read_optional_int, read_str


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
