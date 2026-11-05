"""Errores y superficie de la API con el rol real (T019: F10, SC-005, FR-013, FR-016)."""
import asyncio

import pytest

from api.errors import (CODE_INTERNAL_ERROR, CODE_INVALID_CURSOR, CODE_INVALID_PARAMETER,
                        CODE_METHOD_NOT_ALLOWED, CODE_NOT_FOUND)
from api.main import create_app
from tests.support.api_client import api_client

READ_PATHS = {"/api/eventos", "/api/estadisticas", "/api/salud"}
FORBIDDEN_IN_BODY = ("detail", "Traceback", "SELECT", "FROM", "asyncpg")

BAD_PARAMS = [
    ("/api/eventos", {"min_mag": "abc"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"min_mag": "nan"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"limit": "0"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"limit": "1.5"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"cursor": "xx"}, CODE_INVALID_CURSOR),
    ("/api/eventos", {"mode": "otro"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"start": "ayer"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"start": "2026-11-02", "end": "2026-11-01"}, CODE_INVALID_PARAMETER),
    ("/api/eventos", {"country_id": "ES"}, CODE_INVALID_PARAMETER),
    ("/api/estadisticas", {"min_mag": "abc"}, CODE_INVALID_PARAMETER),
    ("/api/estadisticas", {"mode": "otro"}, CODE_INVALID_PARAMETER),
    ("/api/estadisticas", {"country_id": "E1A"}, CODE_INVALID_PARAMETER),
    ("/api/estadisticas", {"start": "2026-11-02", "end": "2026-11-01"}, CODE_INVALID_PARAMETER),
]


def _call(db, method, path, params=None):
    async def scenario():
        async with api_client(db) as client:
            return await client.request(method, path, params=params)
    return asyncio.run(scenario())


def _assert_common_error(response, status, code):
    assert response.status_code == status
    assert response.status_code != 422
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code and body["error"]["message"]
    assert not any(fragment in response.text for fragment in FORBIDDEN_IN_BODY)


@pytest.mark.parametrize("path,params,code", BAD_PARAMS)
def test_invalid_parameters_return_400(db, path, params, code):
    _assert_common_error(_call(db, "GET", path, params), 400, code)


@pytest.mark.parametrize("path", ["/api/foo", "/", "/api", "/api/eventos/1", "/docs", "/redoc", "/openapi.json"])
def test_unknown_routes_return_404(db, path):
    _assert_common_error(_call(db, "GET", path), 404, CODE_NOT_FOUND)


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", sorted(READ_PATHS))
def test_write_methods_return_405_with_allow(db, method, path):
    response = _call(db, method, path)
    _assert_common_error(response, 405, CODE_METHOD_NOT_ALLOWED)
    assert "GET" in response.headers["allow"]


def _flatten_routes(routes):
    """Rutas reales de la app: FastAPI agrupa cada `include_router` en un `_IncludedRouter`."""
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _flatten_routes(original.routes)
        else:
            yield route


def test_route_list_is_exactly_the_three_read_routes():
    routes = [(route.path, frozenset(route.methods)) for route in _flatten_routes(create_app().routes)]
    assert sorted(routes) == sorted((path, frozenset({"GET"})) for path in READ_PATHS)


def test_unexpected_failure_returns_500_without_trace_or_sql(db, monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("SELECT secreto FROM live.current_event")
    monkeypatch.setattr("api.routers.events.fetch_counts", boom)
    monkeypatch.setattr("api.routers.stats.fetch_counts", boom)
    for path in ("/api/eventos", "/api/estadisticas"):
        response = _call(db, "GET", path)
        _assert_common_error(response, 500, CODE_INTERNAL_ERROR)
        assert "secreto" not in response.text
