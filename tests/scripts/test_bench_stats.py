"""Pruebas sin Docker de los estadísticos y el presupuesto de repeticiones (T073, K2)."""
import pytest

from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX, N_MIN, plan_repetitions, summarize, warmup_counts


def test_summarize_known_series_gives_expected_median_and_iqr() -> None:
    summary = summarize([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    assert summary.median == 5.0
    assert (summary.q1, summary.q3, summary.iqr) == (3.0, 7.0, 4.0)
    assert (summary.minimum, summary.maximum) == (1.0, 9.0)


def test_summarize_single_sample_and_empty() -> None:
    assert summarize([2.5]).iqr == 0.0
    with pytest.raises(ValueError):
        summarize([])


def test_constants_are_the_ones_of_the_plan() -> None:
    assert (N_MAX, N_MIN, BUDGET_SECONDS) == (15, 3, 90)


@pytest.mark.parametrize("t_warmup, expected", [(1, 15), (10, 9), (40, 3), (400, 3)])
def test_plan_repetitions_follows_the_budget(t_warmup: float, expected: int) -> None:
    assert plan_repetitions(t_warmup, BUDGET_SECONDS) == expected


def test_warmup_counts_only_when_it_exceeds_the_budget() -> None:
    assert warmup_counts(400, BUDGET_SECONDS) is True
    assert warmup_counts(40, BUDGET_SECONDS) is False
