"""Arnés de medición: tiempo con calentamiento y pico de memoria con `tracemalloc` (K2, D2).

Tiempo y memoria se miden en pasadas distintas porque `tracemalloc` ralentiza el código.
Sin `psutil` (provisional 2): el pico es el de las estructuras de Python, no el RSS del proceso.
"""
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass

from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX, N_MIN, plan_repetitions, warmup_counts

MS_PER_SECOND = 1000.0
BYTES_PER_KIB = 1024


@dataclass(frozen=True)
class TimeResult:
    """Muestras en ms (sin el calentamiento descartado), N pedida y N real."""

    samples_ms: list[float]
    n_requested: int
    n_real: int


def _timed_ms(fn: Callable[[], object], clock: Callable[[], float]) -> float:
    """Ejecuta `fn` una vez y devuelve su duración en milisegundos."""
    start = clock()
    fn()
    return (clock() - start) * MS_PER_SECOND


def measure_time(fn: Callable[[], object], n_max: int = N_MAX, budget: float = BUDGET_SECONDS,
                 clock: Callable[[], float] = time.perf_counter) -> TimeResult:
    """Mide `fn` repetidas veces con un calentamiento descartado.

    Qué hace:
        Ejecuta un calentamiento, decide N con `plan_repetitions` y mide N veces con `clock`.
        Si el calentamiento ya supera el presupuesto, cuenta como una repetición y se hacen
        N - 1 más (nunca se omite la combinación).
    Recibe:
        fn: función sin argumentos; n_max: repeticiones pedidas; budget: segundos por combinación;
        clock: reloj en segundos (inyectable en las pruebas).
    Devuelve:
        `TimeResult` con las muestras en ms y la N real.
    Por qué existe:
        Da series comparables con N real visible en cada celda (K2, FR-007 a FR-009, SC-002).
    """
    warmup_ms = _timed_ms(fn, clock)
    seconds = warmup_ms / MS_PER_SECOND
    n_real = plan_repetitions(seconds, budget, n_max, N_MIN)
    samples = [warmup_ms] if warmup_counts(seconds, budget) else []
    while len(samples) < n_real:
        samples.append(_timed_ms(fn, clock))
    return TimeResult(samples, n_max, n_real)


def measure_peak_kib(fn: Callable[[], object]) -> float:
    """Pico de memoria de Python durante una pasada de `fn`, en KiB (base 1024).

    Recibe:
        fn: función sin argumentos, ejecutada una sola vez aparte de las series de tiempo.
    Devuelve:
        Pico de `tracemalloc` en KiB.
    Por qué existe:
        Informa la memoria de las estructuras (lista, `dict`, `STRtree`) sin `psutil` (K2, D2).
    """
    already_tracing = tracemalloc.is_tracing()
    if not already_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()
    try:
        result = fn()
        _, peak = tracemalloc.get_traced_memory()
        del result
    finally:
        if not already_tracing:
            tracemalloc.stop()
    return peak / BYTES_PER_KIB
