"""Pruebas de common/api_config.py: defectos y rangos de las variables de la API (F5, FR-019)."""
import pytest

from common.api_config import ApiSettings, load_api_settings, load_cors_origins, parse_cors_origins
from common.config import ConfigError


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
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


def test_cors_defaults():
    assert load_cors_origins() == ("https://observatorio.ssamuelfernandez.net", "http://localhost:4200")


def test_cors_trims_spaces_and_removes_duplicates():
    raw = " https://a.example , http://localhost:4200,, https://a.example "
    assert parse_cors_origins(raw) == ("https://a.example", "http://localhost:4200")


@pytest.mark.parametrize("raw", [
    "*",
    "https://a.example,*",
    "observatorio.example.com",
    "http://localhost:4200/",
    "https://x.netlify.app/api",
    " , ",
])
def test_cors_invalid_origins_raise_config_error(raw):
    with pytest.raises(ConfigError, match="CORS_ALLOWED_ORIGINS"):
        parse_cors_origins(raw)


def test_cors_empty_variable_raises_config_error(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "")
    with pytest.raises(ConfigError, match="CORS_ALLOWED_ORIGINS"):
        load_cors_origins()


def test_cors_variable_overrides_default(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://sitio.netlify.app")
    assert load_cors_origins() == ("https://sitio.netlify.app",)
