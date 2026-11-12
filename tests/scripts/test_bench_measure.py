"""Pruebas sin Docker del arnés de medición (T074, K2). El reloj se simula en los casos caros."""
import time

from scripts.benchmarks.measure import measure_peak_kib, measure_time


class FakeClock:
    """Reloj simulado: cada llamada a `advance` mueve el tiempo, sin esperar de verdad."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_short_sleep_gives_positive_samples_and_n_up_to_15() -> None:
    result = measure_time(lambda: time.sleep(0.001), n_max=15, budget=90)
    assert result.n_real == len(result.samples_ms) <= 15
    assert all(sample > 0 for sample in result.samples_ms)


def test_expensive_function_reduces_n_to_three_without_skipping() -> None:
    clock = FakeClock()
    result = measure_time(lambda: setattr(clock, "now", clock.now + 40.0), n_max=15, budget=90, clock=clock)
    assert result.n_real == 3
    assert result.samples_ms == [40000.0, 40000.0, 40000.0]


def test_warmup_over_budget_counts_as_a_repetition() -> None:
    clock = FakeClock()
    calls = []
    result = measure_time(lambda: (calls.append(1), setattr(clock, "now", clock.now + 400.0)),
                          n_max=15, budget=90, clock=clock)
    assert len(calls) == 3  # calentamiento contado más dos repeticiones
    assert result.n_real == 3 == len(result.samples_ms)


def test_peak_memory_grows_with_the_structure() -> None:
    small = measure_peak_kib(lambda: list(range(1_000)))
    large = measure_peak_kib(lambda: list(range(100_000)))
    assert large > small > 0
