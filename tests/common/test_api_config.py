"""Pruebas de common/api_config.py: defectos y rangos de las variables de la API (F5, FR-019)."""
import pytest

from common.api_config import ApiSettings, load_api_settings
from common.config import ConfigError


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("API_MAX_EVENTS", raising=False)
    monkeypatch.delenv("API_DB_TIMEOUT_SECONDS", raising=False)


def test_defaults():
    assert load_api_settings() == ApiSettings(max_events=5000, db_timeout_seconds=5)


def test_valid_values(monkeypatch):
    monkeypatch.setenv("API_MAX_EVENTS", "10")
    monkeypatch.setenv("API_DB_TIMEOUT_SECONDS", "9")
    assert load_api_settings() == ApiSettings(max_events=10, db_timeout_seconds=9)


@pytest.mark.parametrize("name,value", [
    ("API_MAX_EVENTS", "abc"),
    ("API_MAX_EVENTS", "1.5"),
    ("API_MAX_EVENTS", "0"),
    ("API_DB_TIMEOUT_SECONDS", "x"),
    ("API_DB_TIMEOUT_SECONDS", "0"),
    ("API_DB_TIMEOUT_SECONDS", "10"),
])
def test_invalid_values_raise_config_error(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError, match=name):
        load_api_settings()
