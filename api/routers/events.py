"""Endpoint de eventos: GET /api/eventos (api.md §3)."""
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.cursor import CursorPosition, encode_cursor
from api.db_access import read_transaction
from api.params import PageRequest, QueryFilters, parse_filters, parse_page
from api.queries import fetch_counts, fetch_events_page, fetch_last_ingestion_ms, null_mag_excluded
from api.serializers import build_collection, build_feature, build_metadata

router = APIRouter()

MS_PER_SECOND = 1000


def _next_cursor(rows: list, has_more: bool) -> str | None:
    """Cursor de la página siguiente: la posición del último evento devuelto, o None si no hay más."""
    if not has_more:
        return None
    last = rows[-1]
    return encode_cursor(CursorPosition(time_ms=last["event_time_ms"], event_id=last["event_id"]))


async def _read_page(request: Request, filters: QueryFilters, page: PageRequest) -> tuple:
    """Lee recuentos, página y última ingesta en una única transacción de lectura."""
    timeout = request.app.state.api_settings.db_timeout_seconds
    async with read_transaction(request.app.state.pool, timeout) as connection:
        counts = await fetch_counts(connection, filters)
        rows, has_more = await fetch_events_page(connection, filters, page.cursor, page.limit)
        last_ingestion = await fetch_last_ingestion_ms(connection)
    return counts, rows, has_more, last_ingestion


def _build_body(now_ms: int, filters: QueryFilters, loaded: tuple) -> dict[str, Any]:
    counts, rows, has_more, last_ingestion = loaded
    metadata = build_metadata(generated=now_ms, last_ingestion=last_ingestion, mode=filters.mode,
                              count=len(rows), total=counts.total, next_cursor=_next_cursor(rows, has_more),
                              null_mag_excluded=null_mag_excluded(counts, filters))
    return build_collection([build_feature(row) for row in rows], metadata)


@router.get("/api/eventos")
async def get_events(request: Request) -> JSONResponse:
    """Devuelve los eventos que cumplen los filtros como `FeatureCollection` paginada.

    Qué hace:
        Valida los parámetros, lee recuentos y página en una transacción de lectura y arma la respuesta.
    Recibe:
        request: petición; los parámetros se leen en crudo para dar 400 propio y no 422 (D1).
    Devuelve:
        200 con el GeoJSON de api.md §3; 400 si un parámetro no es válido; 503 si falla la base.
    Por qué existe:
        Es el endpoint principal del mapa (F1-F5).
    """
    now_ms = int(time.time() * MS_PER_SECOND)
    raw_params = request.query_params.multi_items()
    filters = parse_filters(raw_params, now_ms)
    page = parse_page(raw_params, request.app.state.api_settings.max_events)
    loaded = await _read_page(request, filters, page)
    return JSONResponse(_build_body(now_ms, filters, loaded))
