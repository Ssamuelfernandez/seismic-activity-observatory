"""Medición de tiempo para funciones asíncronas (consultas a PostgreSQL), con la misma regla que `measure.py`.

La consulta se mide completa desde el cliente (ida y vuelta incluidas); el tiempo del servidor
sale aparte del plan `EXPLAIN ANALYZE`.
"""
import time
from collections.abc import Awaitable, Callable

from scripts.benchmarks.measure import MS_PER_SECOND, TimeResult
from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX, N_MIN, plan_repetitions, warmup_counts


async def _timed_ms(fn: Callable[[], Awaitable[object]], clock: Callable[[], float]) -> float:
    """Ejecuta `fn` una vez y devuelve su duración en milisegundos."""
    start = clock()
    await fn()
    return (clock() - start) * MS_PER_SECOND


async def measure_time_async(fn: Callable[[], Awaitable[object]], n_max: int = N_MAX,
                             budget: float = BUDGET_SECONDS,
                             clock: Callable[[], float] = time.perf_counter) -> TimeResult:
    """Mide una corrutina repetida con un calentamiento descartado (misma regla que `measure_time`).

    Recibe:
        fn: función sin argumentos que devuelve una corrutina; n_max, budget y clock como en
        `measure_time`.
    Devuelve:
        `TimeResult` con las muestras en ms y la N real (nunca menos de 3, nunca se omite).
    Por qué existe:
        Las consultas a la base son asíncronas y deben medirse con el mismo método (K2, FR-008).
    """
    warmup_ms = await _timed_ms(fn, clock)
    seconds = warmup_ms / MS_PER_SECOND
    n_real = plan_repetitions(seconds, budget, n_max, N_MIN)
    samples = [warmup_ms] if warmup_counts(seconds, budget) else []
    while len(samples) < n_real:
        samples.append(await _timed_ms(fn, clock))
    return TimeResult(samples, n_max, n_real)
