"""Cliente `httpx` contra la aplicación con el rol real `observatory_api` (D13).

`ASGITransport` no ejecuta el `lifespan`, así que el pool y la configuración se asignan a mano.
Los datos se siembran como administrador (ver `api_seed.py`); la API solo lee.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from api.main import create_app
from common.api_config import ApiSettings
from tests.support.api_seed import SeedEvent, seed_countries, seed_events
from tests.support.temp_database import TempDatabase


async def seed_database(db: TempDatabase, live: list[SeedEvent] | None = None,
                        replay: list[SeedEvent] | None = None, countries: dict[str, str] | None = None) -> None:
    """Siembra países y eventos sintéticos como administrador."""
    admin = await db.admin()
    try:
        if countries:
            await seed_countries(admin, countries)
        for mode, events in (("live", live), ("replay", replay)):
            if events:
                await seed_events(admin, mode, events)
    finally:
        await admin.close()


@asynccontextmanager
async def api_client(db: TempDatabase, settings: ApiSettings | None = None) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente contra una aplicación nueva con un pool del rol `observatory_api`; cierra el pool al salir."""
    application = create_app()
    pool = await db.api_pool()
    application.state.pool = pool
    application.state.api_settings = settings or ApiSettings()
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        await pool.close()


async def request_api(db: TempDatabase, path: str, params: dict | list | None = None,
                      live: list[SeedEvent] | None = None, replay: list[SeedEvent] | None = None,
                      countries: dict[str, str] | None = None, settings: ApiSettings | None = None) -> httpx.Response:
    """Siembra los datos, hace un `GET` y devuelve la respuesta (una aplicación y un pool por llamada)."""
    await seed_database(db, live=live, replay=replay, countries=countries)
    async with api_client(db, settings) as client:
        return await client.get(path, params=params)
