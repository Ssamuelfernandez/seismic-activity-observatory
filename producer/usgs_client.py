"""Cliente HTTP del feed de USGS: una consulta con timeout, sin interpretar el cuerpo (B1, B10)."""
import asyncio
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MS_PER_SECOND = 1000
HTTP_OK = 200
USER_AGENT = "seismic-observatory/0.1 (curso)"
TIMEOUT_MESSAGE = "timeout"


@dataclass(frozen=True)
class FeedResponse:
    """Resultado de una consulta correcta: código, cuerpo en bytes, latencia e instante de recepción."""

    status: int
    body: bytes
    latency_ms: int
    received_at: datetime


class FeedFetchError(Exception):
    """Fallo de HTTP (429, 5xx), de red o de timeout al consultar el feed."""

    def __init__(self, status: int | None, message: str, latency_ms: int) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.latency_ms = latency_ms


def _elapsed_ms(started: float) -> int:
    """Milisegundos transcurridos desde `started` (reloj monotónico)."""
    return int((time.monotonic() - started) * MS_PER_SECOND)


def _blocking_get(url: str, timeout_seconds: float) -> tuple[int, bytes]:
    """GET bloqueante; devuelve (código, cuerpo). Se ejecuta en un hilo."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.status, response.read()


async def fetch_feed(url: str, timeout_seconds: float) -> FeedResponse:
    """Consulta el feed una vez.

    Qué hace:
        Hace el GET en un hilo (`asyncio.to_thread`) y mide la latencia.
    Recibe:
        url: dirección del feed; timeout_seconds: espera máxima por operación de socket.
    Devuelve:
        FeedResponse con el cuerpo en bytes.
    Por qué existe:
        Aísla la red del ciclo para probarlo con dobles; sin dependencias nuevas (research §1).
    Lanza:
        FeedFetchError con `status` (HTTP) o `None` (timeout o red) y la latencia.
    """
    started = time.monotonic()
    try:
        status, body = await asyncio.to_thread(_blocking_get, url, timeout_seconds)
    except urllib.error.HTTPError as error:
        raise FeedFetchError(error.code, f"HTTP {error.code}", _elapsed_ms(started)) from error
    except (TimeoutError, urllib.error.URLError, OSError) as error:
        raise FeedFetchError(None, _network_message(error), _elapsed_ms(started)) from error
    if status != HTTP_OK:
        raise FeedFetchError(status, f"HTTP {status}", _elapsed_ms(started))
    return FeedResponse(status, body, max(_elapsed_ms(started), 1), datetime.now(timezone.utc))


def _network_message(error: Exception) -> str:
    """Texto corto del fallo de red: `timeout` si lo fue, si no el nombre y motivo del error."""
    reason = getattr(error, "reason", error)
    if isinstance(error, TimeoutError) or isinstance(reason, TimeoutError):
        return TIMEOUT_MESSAGE
    return f"{type(error).__name__}: {reason}"
