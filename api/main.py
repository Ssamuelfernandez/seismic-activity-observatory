"""Creación de la aplicación FastAPI: solo configura; la lógica está en los routers."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers import health
from common.config import load_database_settings, load_log_level, load_retry_settings
from common.db import create_pool_with_retry
from common.logging_setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Abre el pool de conexiones (con reintentos) al arrancar y lo cierra al parar."""
    configure_logging(load_log_level())
    app.state.pool = await create_pool_with_retry(load_database_settings(), load_retry_settings())
    yield
    await app.state.pool.close()


app = FastAPI(title="Observatorio sísmico", lifespan=lifespan, docs_url=None, redoc_url=None)
app.include_router(health.router)
