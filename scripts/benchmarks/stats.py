"""Estadísticos y presupuesto de repeticiones de las mediciones. Puro, sin E/S (K2, FR-008, FR-009).

No mide nada: solo resume series ya medidas y decide cuántas repeticiones caben.
"""
import math
import statistics
from dataclasses import dataclass

N_MAX = 15
N_MIN = 3
BUDGET_SECONDS = 90


@dataclass(frozen=True)
class Summary:
    """Resumen de una serie: mediana, cuartiles, rango intercuartílico, mínimo y máximo."""

    median: float
    q1: float
    q3: float
    iqr: float
    minimum: float
    maximum: float


def summarize(samples: list[float]) -> Summary:
    """Resume una serie de muestras con estadísticos robustos.

    Qué hace:
        Calcula mediana, cuartiles (método inclusivo), rango intercuartílico, mínimo y máximo.
    Recibe:
        samples: muestras numéricas (al menos una).
    Devuelve:
        `Summary`; con una sola muestra los cuartiles valen esa muestra.
    Por qué existe:
        La mediana y el rango intercuartílico resisten el ruido del stack en marcha (K2, FR-009).
    """
    if not samples:
        raise ValueError("no hay muestras que resumir")
    if len(samples) == 1:
        value = samples[0]
        return Summary(value, value, value, 0.0, value, value)
    q1, _, q3 = statistics.quantiles(samples, n=4, method="inclusive")
    return Summary(statistics.median(samples), q1, q3, q3 - q1, min(samples), max(samples))


def warmup_counts(t_warmup: float, budget: float) -> bool:
    """Indica si el calentamiento supera el presupuesto y cuenta como una repetición."""
    return t_warmup > budget


def plan_repetitions(t_warmup: float, budget: float, n_max: int = N_MAX, n_min: int = N_MIN) -> int:
    """Decide cuántas repeticiones caben en el presupuesto de una combinación.

    Qué hace:
        Devuelve `floor(budget / t_warmup)` acotado entre `n_min` y `n_max`. Nunca baja de `n_min`:
        una combinación cara se mide con pocas repeticiones, no se omite ni se estima.
    Recibe:
        t_warmup: segundos que tardó el calentamiento; budget: segundos disponibles;
        n_max, n_min: cotas de repeticiones.
    Devuelve:
        Número de repeticiones N (si el calentamiento supera el presupuesto, ver `warmup_counts`).
    Por qué existe:
        Mantiene la corrida completa en un tiempo razonable sin ocultar la N real (K2, FR-008, SC-002).
    """
    if t_warmup <= 0:
        return n_max
    fit = math.floor(budget / t_warmup)
    return max(n_min, min(n_max, fit))
