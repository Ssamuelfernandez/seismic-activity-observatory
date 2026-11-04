"""Un ciclo completo del productor: consulta, original, clasificación, publicación y marca (B1, B3, B6-B9).

Orquesta; la decisión, el mensaje y el hash son funciones puras de `common/`. Recibe sus dependencias
(cliente, almacén, publicador y reloj) como argumentos para probarlo sin red ni servicios.
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from common.config import FeedSettings
from common.db import RETRIABLE_DB_ERRORS
from common.ingest_decision import Decision, build_exclusion_row, decide_publication
from common.live_message import build_live_message, message_key
from common.usgs_feed import FeedFormatError, hash_features, parse_feed_body
from producer.publisher import RETRIABLE_KAFKA_ERRORS
from producer.usgs_client import FeedFetchError, FeedResponse

logger = logging.getLogger(__name__)

STATUS_OK = "ok"
STATUS_FETCH_ERROR = "fetch_error"
STATUS_KAFKA_ERROR = "kafka_error"
STATUS_DB_ERROR = "db_error"
INVALID_BODY_PREFIX = "invalid_body: "


class IngestStore(Protocol):
    """Operaciones de PostgreSQL que necesita el ciclo (las implementa `PoolIngestStore`)."""

    async def record_success(self, url: str, response: FeedResponse, event_count: int, sha256: str) -> bool: ...
    async def record_failure(self, url: str, run_at: datetime, status: int | None,
                             latency_ms: int, error: str) -> None: ...
    async def insert_exclusions(self, rows: list[dict]) -> None: ...
    async def load_state(self, event_ids: list[str]) -> dict[str, int]: ...
    async def mark_published(self, event_id: str, updated_ms: int, published_at: datetime) -> None: ...
    async def purge_raw_responses(self, retention_days: int) -> int: ...


@dataclass(frozen=True)
class CycleDeps:
    """Dependencias del ciclo: `fetch(url, timeout)`, almacén, `publish(key, message)` y reloj."""

    fetch: Callable[[str, float], Awaitable[FeedResponse]]
    store: IngestStore
    publish: Callable[[str | None, dict], Awaitable[None]]
    now: Callable[[], datetime]


@dataclass(frozen=True)
class CycleResult:
    """Resultado de un ciclo, base de la línea de log y de las pruebas (data-model.md §3 y §6)."""

    status: str
    http: int | None = None
    latency_ms: int = 0
    fetched: int = 0
    excluded: int = 0
    published: int = 0
    skipped: int = 0
    unmarked: int = 0


@dataclass(frozen=True)
class _Plan:
    """Lo que hará el ciclo con los elementos: publicar, anotar exclusiones y omitir."""

    to_publish: list[tuple[dict, Decision]]
    exclusions: list[dict]
    skipped: int


async def run_cycle(deps: CycleDeps, settings: FeedSettings) -> CycleResult:
    """Ejecuta un ciclo completo en el orden fijo de plan.md §1.

    Qué hace:
        Consulta el feed, guarda el original, anota exclusiones y publica lo nuevo o revisado;
        el estado de cada evento se marca solo después del ack de Kafka.
    Recibe:
        deps: cliente, almacén, publicador y reloj; settings: URL, timeout y retención.
    Devuelve:
        CycleResult con el estado (`ok`, `fetch_error`, `kafka_error` o `db_error`) y los contadores.
    Por qué existe:
        Garantiza al menos una vez sin republicar lo ya publicado (B6, B9).
    """
    try:
        return await _run(deps, settings)
    except RETRIABLE_DB_ERRORS as error:
        logger.error("Fallo de PostgreSQL en el ciclo: %s", error)
        return CycleResult(STATUS_DB_ERROR)


async def _run(deps: CycleDeps, settings: FeedSettings) -> CycleResult:
    """Pasos del ciclo; los errores de PostgreSQL suben a `run_cycle`."""
    fetched = await _fetch_and_validate(deps, settings)
    if isinstance(fetched, CycleResult):
        return fetched
    response, features = fetched
    await deps.store.record_success(settings.url, response, len(features), hash_features(features))
    plan = await _classify(deps, features, response.received_at)
    await deps.store.insert_exclusions(plan.exclusions)
    result = CycleResult(STATUS_OK, response.status, response.latency_ms, len(features),
                         len(plan.exclusions), skipped=plan.skipped)
    result = await _publish_all(deps, plan.to_publish, response.received_at, result)
    if result.status == STATUS_OK:
        await _purge(deps, settings.raw_retention_days)
    return result


async def _fetch_and_validate(deps: CycleDeps, settings: FeedSettings) -> tuple[FeedResponse, list[dict]] | CycleResult:
    """Consulta y valida el cuerpo; un fallo de USGS se registra y no toca el estado (B10)."""
    try:
        response = await deps.fetch(settings.url, settings.timeout_seconds)
    except FeedFetchError as error:
        logger.warning("Fallo al consultar USGS: %s", error.message)
        await deps.store.record_failure(settings.url, deps.now(), error.status, error.latency_ms, error.message)
        return CycleResult(STATUS_FETCH_ERROR, error.status, error.latency_ms)
    try:
        return response, parse_feed_body(response.body)
    except FeedFormatError as error:
        logger.warning("Cuerpo no válido de USGS: %s", error)
        await deps.store.record_failure(settings.url, response.received_at, response.status,
                                        response.latency_ms, f"{INVALID_BODY_PREFIX}{error}")
        return CycleResult(STATUS_FETCH_ERROR, response.status, response.latency_ms)


async def _classify(deps: CycleDeps, features: list[dict], received_at: datetime) -> _Plan:
    """Aplica `decide_publication` a cada elemento con el estado leído en una sola consulta."""
    ids = sorted({f["id"] for f in features if isinstance(f.get("id"), str)})
    state = await deps.store.load_state(ids) if ids else {}
    to_publish: list[tuple[dict, Decision]] = []
    exclusions: list[dict] = []
    skipped = 0
    for feature in features:
        event_id = feature.get("id")
        decision = decide_publication(feature, state.get(event_id) if isinstance(event_id, str) else None)
        if decision is Decision.EXCLUDE:
            exclusions.append(build_exclusion_row(feature, received_at))
        elif decision is Decision.SKIP:
            skipped += 1
        else:
            to_publish.append((feature, decision))
    return _Plan(to_publish, exclusions, skipped)


async def _publish_all(deps: CycleDeps, items: list[tuple[dict, Decision]], received_at: datetime,
                       result: CycleResult) -> CycleResult:
    """Publica uno a uno: ack primero y marca después; un fallo de Kafka corta el ciclo (B9)."""
    published = unmarked = 0
    for feature, decision in items:
        try:
            await deps.publish(message_key(feature), build_live_message(feature, received_at))
        except RETRIABLE_KAFKA_ERRORS as error:
            logger.error("Fallo de Kafka al publicar; se corta el ciclo: %s", error)
            return replace(result, status=STATUS_KAFKA_ERROR, published=published, unmarked=unmarked)
        published += 1
        if decision is Decision.PUBLISH:
            await deps.store.mark_published(feature["id"], feature["properties"]["updated"], deps.now())
        else:
            unmarked += 1
    return replace(result, published=published, unmarked=unmarked)


async def _purge(deps: CycleDeps, retention_days: int) -> None:
    """Purga los originales antiguos; un fallo solo se registra en el log (research §2)."""
    try:
        await deps.store.purge_raw_responses(retention_days)
    except RETRIABLE_DB_ERRORS as error:
        logger.warning("No se pudo purgar raw_response: %s", error)
