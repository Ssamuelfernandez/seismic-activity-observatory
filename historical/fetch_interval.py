"""Descarga de un intervalo de USGS: `count`, división recursiva y reintentos (B13, FR-002, FR-007)."""
import json
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from common.backoff import PRODUCTION_BACKOFF, compute_backoff_seconds
from historical.intervals import KIND_COUNT, KIND_QUERY, Interval, build_query_url, format_query_time, split_interval
from historical.manifest import QueryRecord
from producer.usgs_client import FeedFetchError

logger = logging.getLogger(__name__)

MAX_RESULTS_PER_QUERY = 20_000
MAX_ATTEMPTS = 5
MIN_SPLITTABLE = timedelta(milliseconds=2)
EXTRACTED_AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class IntervalFetchError(Exception):
    """No se pudo descargar un intervalo completo y fiable."""


@dataclass(frozen=True)
class FetchTools:
    """Dependencias inyectables de la descarga: petición, URL base, espera, jitter y reloj."""

    fetch: Callable[[str], Awaitable[bytes]]
    base_url: str
    sleep: Callable[[float], Awaitable[None]]
    jitter: Callable[[], float] = random.random
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)


@dataclass(frozen=True)
class IntervalData:
    """Resultado de un intervalo: features fusionadas, consultas hechas y fecha de extracción."""

    features: list[dict]
    queries: list[QueryRecord]
    extracted_at: str
    metadata: dict


def describe_interval(interval: Interval) -> str:
    """Texto `inicio/fin` del intervalo para logs y errores."""
    return f"{format_query_time(interval.start)}/{format_query_time(interval.end)}"


async def _fetch_with_retries(url: str, interval: Interval, tools: FetchTools) -> bytes:
    """Pide la URL; ante `FeedFetchError` espera con backoff y reintenta hasta `MAX_ATTEMPTS`."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return await tools.fetch(url)
        except FeedFetchError as error:
            logger.warning("retry interval=%s attempt=%d error=%s", describe_interval(interval), attempt, error)
            if attempt == MAX_ATTEMPTS:
                raise IntervalFetchError(
                    f"intervalo {describe_interval(interval)}: {MAX_ATTEMPTS} intentos fallidos ({error})"
                ) from error
            await tools.sleep(compute_backoff_seconds(attempt, PRODUCTION_BACKOFF, tools.jitter()))
    raise AssertionError("inalcanzable: el bucle devuelve o lanza")


def _parse_count(body: bytes, interval: Interval) -> int:
    """Extrae el número de la respuesta de `count` (JSON `{"count": n}` o texto plano)."""
    text = body.decode("utf-8").strip()
    try:
        value = json.loads(text)
        count = value["count"] if isinstance(value, dict) else value
        if isinstance(count, int) and not isinstance(count, bool):
            return count
    except (ValueError, KeyError):
        pass
    raise IntervalFetchError(f"intervalo {describe_interval(interval)}: respuesta de count ilegible")


async def fetch_count(interval: Interval, tools: FetchTools) -> int:
    """Pregunta a USGS cuántos eventos hay en el intervalo."""
    url = build_query_url(interval, tools.base_url, KIND_COUNT)
    return _parse_count(await _fetch_with_retries(url, interval, tools), interval)


async def _fetch_leaf(interval: Interval, count: int, tools: FetchTools) -> IntervalData:
    """Descarga un intervalo con `count <= MAX_RESULTS_PER_QUERY` y comprueba registros == count."""
    url = build_query_url(interval, tools.base_url, KIND_QUERY)
    body = await _fetch_with_retries(url, interval, tools)
    extracted_at = tools.now().strftime(EXTRACTED_AT_FORMAT)
    collection = json.loads(body)
    features = collection["features"]
    logger.info("query interval=%s usgs_count=%d records=%d", describe_interval(interval), count, len(features))
    if len(features) != count:
        raise IntervalFetchError(
            f"intervalo {describe_interval(interval)}: USGS anunció {count} y devolvió {len(features)}; repetir"
        )
    record = QueryRecord(url, format_query_time(interval.start), format_query_time(interval.end), count, len(features))
    return IntervalData(features, [record], extracted_at, collection.get("metadata", {}))


def _merge(first: IntervalData, second: IntervalData) -> IntervalData:
    """Concatena dos resultados contiguos conservando `extracted_at` y `metadata` del primero."""
    return IntervalData(first.features + second.features, first.queries + second.queries,
                        first.extracted_at, first.metadata)


async def fetch_interval(interval: Interval, tools: FetchTools) -> IntervalData:
    """Descarga el intervalo completo, dividiéndolo si USGS anuncia más de 20000 eventos.

    Qué hace:
        Pide `count`; si cabe en una consulta la hace, si no parte por el punto medio y repite.
    Recibe:
        interval: tramo a descargar; tools: petición, espera y reloj inyectables.
    Devuelve:
        `IntervalData` con todas las features, una `QueryRecord` por consulta y la fecha de extracción.
    Por qué existe:
        USGS rechaza más de 20000 resultados; nunca se trunca en silencio (research D5).
    Lanza:
        IntervalFetchError si los registros no coinciden con `count`, si se agotan los reintentos
        o si un intervalo de 1 ms supera el máximo.
    """
    count = await fetch_count(interval, tools)
    if count <= MAX_RESULTS_PER_QUERY:
        return await _fetch_leaf(interval, count, tools)
    if interval.end - interval.start < MIN_SPLITTABLE:
        raise IntervalFetchError(
            f"intervalo de 1 ms {describe_interval(interval)} con {count} eventos: no se puede dividir más"
        )
    first, second = split_interval(interval)
    return _merge(await fetch_interval(first, tools), await fetch_interval(second, tools))
