"""Registro de una medición (`Measurement`) y su identificador citable (K1, K2, data-model §2.1).

Puro: convierte una serie de tiempos y, si la hay, un plan de PostgreSQL en el registro que
guardará `resultados.json`. El identificador `<op>.<estrategia>.<tamaño>.<caso>` es el que citan
los veredictos y las propuestas.
"""
from dataclasses import asdict, dataclass, field

from scripts.benchmarks.measure import TimeResult
from scripts.benchmarks.plans import PlanInfo
from scripts.benchmarks.stats import summarize


@dataclass
class Measurement:
    """Una medición SINTÉTICA: tiempos en ms (base decimal), memoria en KiB (base 1024)."""

    id: str
    operation: str
    strategy: str
    size: int
    case: str
    samples_ms: list[float]
    n_requested: int
    n_real: int
    median_ms: float
    q1_ms: float
    q3_ms: float
    iqr_ms: float
    min_ms: float
    max_ms: float
    peak_kib: float | None = None
    plan_ref: str | None = None
    server_ms: float | None = None
    shared_hit: int | None = None
    shared_read: int | None = None
    notes: str = ""
    theory: str = ""
    nodes: list[str] = field(default_factory=list)
    index_used: bool | None = None

    def as_dict(self) -> dict:
        """Diccionario listo para `resultados.json`."""
        return asdict(self)


def measurement_id(operation: str, strategy: str, size: int, case: str) -> str:
    """Identificador `<op>.<estrategia>.<tamaño>.<caso>`, p. ej. `search.dict.100000.absent`."""
    return f"{operation}.{strategy}.{size}.{case}"


def build_measurement(operation: str, strategy: str, size: int, case: str, result: TimeResult, *,
                      peak_kib: float | None = None, plan_ref: str | None = None,
                      plan: PlanInfo | None = None, notes: str = "", theory: str = "") -> Measurement:
    """Arma el registro de una medición a partir de la serie de tiempos.

    Recibe:
        operation, strategy, size, case: las cuatro partes del identificador; result: serie de
        `measure_time`; peak_kib: pico de `tracemalloc` si se midió; plan_ref y plan: ruta y
        resumen del plan de PostgreSQL; notes y theory: texto libre y complejidad teórica.
    Devuelve:
        `Measurement` con los estadísticos de la serie y los datos del plan.
    Por qué existe:
        Un único sitio construye el registro, para que todas las operaciones guarden lo mismo (K2).
    """
    stats = summarize(result.samples_ms)
    server = {}
    if plan is not None:
        server = {"server_ms": plan.execution_ms, "shared_hit": plan.shared_hit,
                  "shared_read": plan.shared_read, "nodes": list(plan.node_types),
                  "index_used": plan.uses_index}
    return Measurement(measurement_id(operation, strategy, size, case), operation, strategy, size, case,
                       list(result.samples_ms), result.n_requested, result.n_real, stats.median, stats.q1,
                       stats.q3, stats.iqr, stats.minimum, stats.maximum, peak_kib, plan_ref,
                       notes=notes, theory=theory, **server)
