"""Endpoint de estadísticas: GET /api/estadisticas (api.md §5)."""
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.db_access import read_transaction
from api.params import MODE_LIVE, QueryFilters, parse_filters
from api.queries import fetch_counts, fetch_last_ingestion_ms
from api.stats_builder import (DEPTH_THRESHOLDS, MAGNITUDE_THRESHOLDS, UNIT_DEPTH, UNIT_MAGNITUDE,
                               build_by_country, build_by_hour, build_comparison, build_histogram,
                               count_without_bucket)
from api.stats_queries import (fetch_comparison_counts, fetch_country_counts, fetch_histogram,
                               fetch_hour_counts)

router = APIRouter()

MS_PER_SECOND = 1000


async def _read_stats(request: Request, filters: QueryFilters, now_ms: int) -> dict[str, Any]:
    """Lee todas las agregaciones en una única transacción de lectura (misma instantánea, FR-010)."""
    timeout = request.app.state.api_settings.db_timeout_seconds
    async with read_transaction(request.app.state.pool, timeout) as connection:
        return {
            "counts": await fetch_counts(connection, filters),
            "hours": await fetch_hour_counts(connection, filters),
            "countries": await fetch_country_counts(connection, filters),
            "magnitude": await fetch_histogram(connection, filters, "magnitude", MAGNITUDE_THRESHOLDS),
            "depth": await fetch_histogram(connection, filters, "depth", DEPTH_THRESHOLDS),
            "comparison": (await fetch_comparison_counts(connection, filters, now_ms)
                           if filters.mode == MODE_LIVE else None),
            "last_ingestion": await fetch_last_ingestion_ms(connection),
        }


def _build_comparison(loaded: dict[str, Any], filters: QueryFilters, now_ms: int) -> dict[str, Any] | None:
    """`comparison` del contrato, o None en modo `replay` (no hay últimas 24 h ni histórico)."""
    counts = loaded["comparison"]
    if counts is None:
        return None
    return build_comparison(counts.n_recent, counts.n_2025, filters.min_mag, now_ms)


def _build_body(now_ms: int, filters: QueryFilters, loaded: dict[str, Any]) -> dict[str, Any]:
    counts = loaded["counts"]
    return {
        "metadata": {"generated": now_ms, "last_ingestion": loaded["last_ingestion"], "mode": filters.mode},
        "period": {"start": filters.start_ms, "end": filters.end_ms},
        "filters": {"min_mag": filters.min_mag, "country_id": filters.country_id},
        "total": counts.total,
        "by_hour": build_by_hour(loaded["hours"], filters.start_ms, filters.end_ms),
        "by_country": build_by_country(loaded["countries"]),
        "histograms": {
            "magnitude": build_histogram(loaded["magnitude"], MAGNITUDE_THRESHOLDS, UNIT_MAGNITUDE,
                                         counts.null_count),
            "depth": build_histogram(loaded["depth"], DEPTH_THRESHOLDS, UNIT_DEPTH,
                                     count_without_bucket(loaded["depth"])),
        },
        "comparison": _build_comparison(loaded, filters, now_ms),
    }


@router.get("/api/estadisticas")
async def get_stats(request: Request) -> JSONResponse:
    """Devuelve las estadísticas de todos los eventos que cumplen los filtros, calculadas en SQL.

    Qué hace:
        Valida los filtros (ignora `limit` y `cursor`), agrega en la base y arma el cuerpo de api.md §5.
    Recibe:
        request: petición; los parámetros se leen en crudo para dar 400 propio y no 422.
    Devuelve:
        200 con el JSON del contrato; 400 si un parámetro no es válido; 503 si falla la base.
    Por qué existe:
        El panel muestra estas cifras tal cual: el frontend no calcula estadísticas (F7).
    """
    now_ms = int(time.time() * MS_PER_SECOND)
    filters = parse_filters(request.query_params.multi_items(), now_ms)
    loaded = await _read_stats(request, filters, now_ms)
    return JSONResponse(_build_body(now_ms, filters, loaded))
