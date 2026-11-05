"""Endpoint de salud: GET /api/salud (api.md §4)."""
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.db_access import read_transaction
from api.queries import fetch_last_ingestion_ms

router = APIRouter()

MS_PER_SECOND = 1000


@router.get("/api/salud")
async def get_health(request: Request) -> JSONResponse:
    """Informa de si la API y la base responden y de la última ingesta.

    Qué hace:
        Consulta la última ingesta correcta con `read_transaction`; ignora `mode` y cualquier otro parámetro.
    Recibe:
        request: petición, de la que se toman el pool y la configuración.
    Devuelve:
        `{"status": "ok", "last_ingestion": <ms|null>, "generated": <ms>}`; 503 si la base falla.
    Por qué existe:
        Contrato api.md §4 y healthcheck de Compose: «saludable» implica que la API alcanza la base (A1).
    """
    timeout = request.app.state.api_settings.db_timeout_seconds
    async with read_transaction(request.app.state.pool, timeout) as connection:
        last_ingestion = await fetch_last_ingestion_ms(connection)
    return JSONResponse({
        "status": "ok",
        "last_ingestion": last_ingestion,
        "generated": int(time.time() * MS_PER_SECOND),
    })
