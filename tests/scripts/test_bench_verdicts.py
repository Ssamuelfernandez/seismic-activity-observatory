"""Pruebas sin Docker del veredicto de índices (T082, E6). Mediciones construidas a mano (SINTÉTICO)."""
from scripts.benchmarks.measure import TimeResult
from scripts.benchmarks.plans import PlanInfo
from scripts.benchmarks.records import build_measurement
from scripts.benchmarks.verdicts import INCONCLUSIVE, JUSTIFIED, NOT_JUSTIFIED, judge, overall_verdict


def make(strategy: str, samples: list[float], uses_index: bool | None = None):
    plan = None if uses_index is None else PlanInfo(1.0, 1, 0, ("Index Scan",) if uses_index else ("Seq Scan",), ())
    return build_measurement("agg", strategy, 1000, "day", TimeResult(samples, 15, len(samples)), plan=plan)


def test_clear_improvement_with_index_used_is_justified_and_cites_ids() -> None:
    without, with_index = make("q4_noindex", [10, 11, 12, 11, 10]), make("q4_time_index", [1, 1.1, 1.2, 1, 1.1], True)
    verdict = judge("ix_a", "q4", without, with_index, selectivity=0.01)
    assert verdict.verdict == JUSTIFIED
    assert verdict.measurement_ids == ("agg.q4_noindex.1000.day", "agg.q4_time_index.1000.day")


def test_index_not_used_is_not_justified() -> None:
    verdict = judge("ix_a", "q3", make("q3_noindex", [5, 5.1, 5.2]), make("q3_mag_index", [1, 1.1, 1.2], False))
    assert verdict.verdict == NOT_JUSTIFIED and "no usa" in verdict.reason


def test_overlapping_ranges_are_inconclusive() -> None:
    verdict = judge("ix_a", "q2", make("q2_noindex", [4, 5, 6, 7]), make("q2_country_index", [5, 5.5, 6.5], True))
    assert verdict.verdict == INCONCLUSIVE


def test_minimum_three_repetitions_is_judged_and_fewer_is_inconclusive() -> None:
    without, with_index = make("q4_noindex", [10, 11, 12]), make("q4_time_index", [1, 1.1, 1.2], True)
    assert judge("ix_a", "q4", without, with_index).verdict == JUSTIFIED
    short = make("q4_time_index", [1.0, 1.1], True)
    assert judge("ix_a", "q4", without, short).verdict == INCONCLUSIVE


def test_index_used_but_slower_is_not_justified_and_overall_prefers_justified() -> None:
    slower = judge("ix_a", "q4", make("q4_noindex", [1, 1.1, 1.2]), make("q4_time_index", [9, 9.1, 9.2], True))
    good = judge("ix_a", "q4", make("q4_noindex", [10, 11, 12]), make("q4_time_index", [1, 1.1, 1.2], True))
    assert slower.verdict == NOT_JUSTIFIED
    assert overall_verdict([slower, good]) == JUSTIFIED and overall_verdict([slower]) == NOT_JUSTIFIED
