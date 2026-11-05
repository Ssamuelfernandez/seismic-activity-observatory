"""Creación de la aplicación FastAPI: solo configura; la lógica está en los routers."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.errors import register_error_handlers
from api.routers import events, health, stats
from common.api_config import load_api_settings
from common.config import load_database_settings, load_log_level, load_retry_settings
from common.db import create_pool_with_retry
from common.logging_setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Abre el pool de conexiones (con reintentos) al arrancar y lo cierra al parar."""
    configure_logging(load_log_level())
    app.state.api_settings = load_api_settings()
    app.state.pool = await create_pool_with_retry(load_database_settings(), load_retry_settings())
    yield
    await app.state.pool.close()


def create_app() -> FastAPI:
    """Crea la aplicación sin documentación automática (constitución §10) y con errores comunes."""
    application = FastAPI(title="Observatorio sísmico", lifespan=lifespan,
                          docs_url=None, redoc_url=None, openapi_url=None)
    register_error_handlers(application)
    application.include_router(health.router)
    application.include_router(events.router)
    application.include_router(stats.router)
    return application


app = create_app()
