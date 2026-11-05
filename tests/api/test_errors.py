"""Pruebas de api/errors.py y api/main.py: cuerpo de error común y superficie cerrada (F10, FR-013)."""
import asyncio

import httpx

from api.errors import ApiError, CODE_INVALID_PARAMETER
from api.main import create_app

JSON_TYPE = "application/json"


def _app():
    application = create_app()

    @application.get("/api/test-ok")
    async def ok() -> dict:
        return {"ok": True}

    @application.get("/api/test-api-error")
    async def api_error() -> None:
        raise ApiError(400, CODE_INVALID_PARAMETER, "El parámetro 'x' no es válido.")

    @application.get("/api/test-boom")
    async def boom() -> None:
        raise RuntimeError("SELECT secreto FROM tabla")

    return application


def _request(method: str, path: str) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path)
    return asyncio.run(run())


def _assert_common_error(response: httpx.Response, status: int, code: str) -> dict:
    assert response.status_code == status
    assert response.headers["content-type"] == JSON_TYPE
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    assert "detail" not in response.text
    return body


def test_api_error_uses_its_status_and_body():
    body = _assert_common_error(_request("GET", "/api/test-api-error"), 400, "invalid_parameter")
    assert body["error"]["message"] == "El parámetro 'x' no es válido."


def test_unknown_route_is_404_not_found():
    _assert_common_error(_request("GET", "/api/foo"), 404, "not_found")


def test_wrong_method_is_405_with_allow_header():
    response = _request("POST", "/api/test-ok")
    _assert_common_error(response, 405, "method_not_allowed")
    assert "GET" in response.headers["allow"]


def test_unhandled_exception_is_500_without_trace_or_sql():
    response = _request("GET", "/api/test-boom")
    _assert_common_error(response, 500, "internal_error")
    assert "SELECT" not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text


def test_documentation_routes_are_disabled():
    for path in ("/openapi.json", "/docs", "/redoc"):
        _assert_common_error(_request("GET", path), 404, "not_found")
