"""503 en los tres endpoints con la base inaccesible (T018: F8, SC-004, FR-012).

El Postgres compartido no se para: se usa un pool hacia un puerto cerrado y otro cerrado a propósito.
"""
import asyncio
import socket
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
import httpx
import pytest

from api.errors import CODE_DATABASE_UNAVAILABLE, MESSAGE_DATABASE_UNAVAILABLE
from api.main import create_app
from common.api_config import ApiSettings
from tests.support.api_client import seed_database
from tests.support.api_seed import synthetic_event

PATHS = ["/api/eventos", "/api/estadisticas", "/api/salud"]
MAX_SECONDS = 10
DB_TIMEOUT_SECONDS = 2


def _closed_port() -> int:
    """Puerto libre del equipo en este momento: nadie escucha tras cerrar el socket."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def _dead_pool(db) -> asyncpg.Pool:
    """Pool hacia un puerto cerrado; `min_size=0` evita conectar al crearlo."""
    return await asyncpg.create_pool(host="127.0.0.1", port=_closed_port(), database=db.name, user=db.api_user,
                                     password=db.api_password, min_size=0, max_size=1, timeout=DB_TIMEOUT_SECONDS)


async def _closed_pool(db) -> asyncpg.Pool:
    pool = await db.api_pool()
    await pool.close()
    return pool


@asynccontextmanager
async def _client(pool) -> AsyncIterator[tuple[httpx.AsyncClient, object]]:
    application = create_app()
    application.state.pool = pool
    application.state.api_settings = ApiSettings(db_timeout_seconds=DB_TIMEOUT_SECONDS)
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, application


async def _assert_503(client: httpx.AsyncClient, path: str) -> None:
    started = time.monotonic()
    response = await client.get(path)
    elapsed = time.monotonic() - started
    assert response.status_code == 503, path
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"error": {"code": CODE_DATABASE_UNAVAILABLE, "message": MESSAGE_DATABASE_UNAVAILABLE}}
    assert "features" not in response.text and "detail" not in response.text
    assert elapsed < MAX_SECONDS, f"{path} tardó {elapsed:.1f} s"


@pytest.mark.parametrize("make_pool", [_dead_pool, _closed_pool], ids=["port_closed", "pool_closed"])
def test_all_endpoints_return_503(db, make_pool):
    async def scenario():
        pool = await make_pool(db)
        try:
            async with _client(pool) as (client, _):
                for path in PATHS:
                    await _assert_503(client, path)
        finally:
            await pool.close()
    asyncio.run(scenario())


def test_recovers_without_restart_when_pool_is_restored(db):
    async def scenario():
        await seed_database(db, live=[synthetic_event(1, time_ms=int(time.time() * 1000) - 1000)])
        dead = await _dead_pool(db)
        good = await db.api_pool()
        try:
            async with _client(dead) as (client, application):
                for path in PATHS:
                    await _assert_503(client, path)
                application.state.pool = good
                for path in PATHS:
                    response = await client.get(path)
                    assert response.status_code == 200, path
                assert (await client.get("/api/eventos")).json()["metadata"]["total"] == 1
        finally:
            await dead.close()
            await good.close()
    asyncio.run(scenario())
