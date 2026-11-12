"""Pruebas de CORS en api/main.py: orígenes exactos, solo GET/OPTIONS y sin credenciales (F9, FR-001 a FR-003)."""
import asyncio

import httpx
import pytest

from api.main import create_app
from common.config import ConfigError

PUBLIC = "https://observatorio.ssamuelfernandez.net"
LOCAL = "http://localhost:4200"
NETLIFY = "https://sitio.netlify.app"
OTHER = "https://otro.example"
HEADER = "ngrok-skip-browser-warning"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)


def _send(method: str, path: str, headers: dict[str, str]) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app(), raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers)
    return asyncio.run(run())


def _preflight(origin: str, method: str = "GET") -> httpx.Response:
    return _send("OPTIONS", "/api/eventos", {"Origin": origin, "Access-Control-Request-Method": method,
                                             "Access-Control-Request-Headers": HEADER})


@pytest.mark.parametrize("origin", [PUBLIC, LOCAL])
def test_preflight_allows_listed_origin(origin):
    response = _preflight(origin)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    methods = response.headers["access-control-allow-methods"]
    assert "GET" in methods and "OPTIONS" in methods
    assert HEADER in response.headers["access-control-allow-headers"].lower()


def test_unlisted_origin_gets_no_allow_origin():
    assert "access-control-allow-origin" not in _send("GET", "/api/foo", {"Origin": OTHER}).headers
    assert "access-control-allow-origin" not in _preflight(OTHER).headers


def test_no_credentials_and_no_wildcard():
    responses = [_preflight(PUBLIC), _send("GET", "/api/foo", {"Origin": PUBLIC})]
    for response in responses:
        assert "access-control-allow-credentials" not in response.headers
        assert response.headers["access-control-allow-origin"] != "*"


def test_extra_origin_from_environment(monkeypatch):
    assert "access-control-allow-origin" not in _preflight(NETLIFY).headers
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", f"{PUBLIC},{NETLIFY}")
    assert _preflight(NETLIFY).headers["access-control-allow-origin"] == NETLIFY
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS")
    assert "access-control-allow-origin" not in _preflight(NETLIFY).headers


def test_post_is_not_allowed_in_preflight():
    response = _preflight(PUBLIC, method="POST")
    assert "POST" not in response.headers.get("access-control-allow-methods", "")


def test_wildcard_origin_aborts_app_creation(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    with pytest.raises(ConfigError, match="CORS_ALLOWED_ORIGINS"):
        create_app()
