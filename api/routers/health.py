"""Endpoint de salud: GET /api/salud (api.md §4)."""
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.queries import fetch_last_ingestion_ms
from common.db import RETRIABLE_DB_ERRORS

logger = logging.getLogger(__name__)

router = APIRouter()

DATABASE_UNAVAILABLE_BODY = {
    "error": {
        "code": "database_unavailable",
        "message": "No se pudo consultar la base de datos. Inténtalo de nuevo más tarde.",
    }
}


@router.get("/api/salud")
async def get_health(request: Request) -> JSONResponse:
    """Informa de si la API y la base responden y de la última ingesta.

    Qué hace:
        Consulta la última ingesta correcta; si la base falla, responde 503 con el error común.
    Recibe:
        request: petición, de la que se toma el pool de conexiones.
    Devuelve:
        `{"status": "ok", "last_ingestion": <ms|null>, "generated": <ms>}` o 503.
    Por qué existe:
        Contrato api.md §4 y healthcheck de Compose: «saludable» implica que la API alcanza la base (A1).
    """
    try:
        last_ingestion = await fetch_last_ingestion_ms(request.app.state.pool)
    except RETRIABLE_DB_ERRORS as error:
        logger.error("La comprobación de salud no pudo consultar la base: %s", type(error).__name__)
        return JSONResponse(status_code=503, content=DATABASE_UNAVAILABLE_BODY)
    return JSONResponse({
        "status": "ok",
        "last_ingestion": last_ingestion,
        "generated": int(time.time() * 1000),
    })
