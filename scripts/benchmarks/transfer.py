"""Transferencia MEDIDA: bytes reales de las respuestas de la API (K6, FR-020).

Las peticiones van al nombre de servicio `api:8000` de la red de Compose (nunca `localhost`, que
dentro del contenedor `tests` es él mismo). El volumen mensual es SUPUESTO: visitas x bytes por
visita, y sin visitas del alumno la fila dice «no calculable».
"""
import urllib.error
import urllib.request
from dataclasses import dataclass

from common.api_config import DEFAULT_API_MAX_EVENTS
from scripts.benchmarks.labels import NOT_COMPUTABLE, PENDING_STUDENT, UNAVAILABLE

API_BASE = "http://api:8000"
TIMEOUT_SECONDS = 30
BYTES_PER_KIB = 1024
DEFAULT_LABEL = "/api/eventos (limit por defecto)"
MAX_LABEL = f"/api/eventos?limit={DEFAULT_API_MAX_EVENTS} (máximo)"
VISIT_ROUTES = (DEFAULT_LABEL, "/api/estadisticas", "/api/salud")
ROUTES = (
    (DEFAULT_LABEL, "/api/eventos"),
    (MAX_LABEL, f"/api/eventos?limit={DEFAULT_API_MAX_EVENTS}"),
    ("/api/estadisticas", "/api/estadisticas"),
    ("/api/salud", "/api/salud"),
)


class TransferError(RuntimeError):
    """No se pudo medir una ruta de la API (no responde o devuelve un estado de error)."""


@dataclass(frozen=True)
class RouteBytes:
    """Bytes del cuerpo de una respuesta, sin compresión (el cliente no la pide)."""

    label: str
    path: str
    status: int
    body_bytes: int


def fetch_route(base: str, label: str, path: str, timeout: float = TIMEOUT_SECONDS) -> RouteBytes:
    """Pide una ruta y devuelve los bytes del cuerpo. Lanza `TransferError` si falla."""
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as response:
            return RouteBytes(label, path, response.status, len(response.read()))
    except (urllib.error.URLError, OSError) as error:
        raise TransferError(f"{base}{path}: {error}") from error


def measure_routes(base: str = API_BASE) -> list[RouteBytes]:
    """Mide `/api/eventos` (por defecto y máximo), `/api/estadisticas` y `/api/salud`."""
    return [fetch_route(base, label, path) for label, path in ROUTES]


def bytes_per_visit(routes: list[RouteBytes]) -> int:
    """Bytes de una visita SUPUESTA: eventos (límite por defecto) + estadísticas + salud."""
    return sum(r.body_bytes for r in routes if r.label in VISIT_ROUTES)


def monthly_bytes(per_visit: int, visits_per_month: float | None) -> float | None:
    """Volumen mensual = visitas/mes x bytes por visita; `None` si las visitas no se conocen."""
    return None if visits_per_month is None else visits_per_month * per_visit


def render_transfer_md(routes: list[RouteBytes] | None, visits_per_month: float | None = None) -> str:
    """Genera `transferencia.md`; sin rutas medidas dice «no disponible», sin visitas «no calculable»."""
    lines = ["# Transferencia medida", "",
             f"MEDIDO: bytes del cuerpo de cada respuesta de `{API_BASE}` (nombre de servicio de Compose), sin "
             "compresión, con los datos reales del stack en el momento de la medición. El límite por defecto de "
             "`/api/eventos` coincide con el máximo (`API_MAX_EVENTS`).", "",
             "| Ruta | Estado HTTP | Bytes | KiB |", "|---|---|---|---|"]
    if routes is None:
        return "\n".join(lines + [f"| (todas) | {UNAVAILABLE} | {UNAVAILABLE} | {UNAVAILABLE} |", ""])
    lines += [f"| {r.label} | {r.status} | {r.body_bytes} | {r.body_bytes / BYTES_PER_KIB:.1f} |" for r in routes]
    per_visit = bytes_per_visit(routes)
    monthly = monthly_bytes(per_visit, visits_per_month)
    visits = PENDING_STUDENT if visits_per_month is None else visits_per_month
    result = NOT_COMPUTABLE if monthly is None else f"{monthly:.0f} bytes"
    lines += ["", "SUPUESTO: una visita carga eventos (límite por defecto), estadísticas y salud.", "",
              "| Concepto | Valor |", "|---|---|", f"| Bytes por visita (MEDIDO) | {per_visit} |",
              f"| Visitas por mes | {visits} |",
              f"| Volumen mensual = visitas x bytes por visita (SUPUESTO) | {result} |", ""]
    return "\n".join(lines)
