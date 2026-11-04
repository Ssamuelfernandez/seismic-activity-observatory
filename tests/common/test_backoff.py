"""Pruebas de `common/backoff.py`: espera creciente con jitter acotado (B10, SC-006)."""
import pytest

from common.backoff import (
    JITTER_MIN_FRACTION, PRODUCTION_BACKOFF, BackoffSettings, compute_backoff_seconds,
)


def test_production_constants():
    assert PRODUCTION_BACKOFF == BackoffSettings(initial_seconds=2, max_seconds=60)
    assert JITTER_MIN_FRACTION == 0.5


def test_sequence_with_jitter_one_is_2_4_8_16_32_60_60():
    waits = [compute_backoff_seconds(n, PRODUCTION_BACKOFF, 1.0) for n in range(1, 8)]
    assert waits == [2, 4, 8, 16, 32, 60, 60]


def test_jitter_zero_applies_the_minimum_factor():
    assert compute_backoff_seconds(1, PRODUCTION_BACKOFF, 0.0) == 2 * JITTER_MIN_FRACTION
    assert compute_backoff_seconds(3, PRODUCTION_BACKOFF, 0.0) == 4.0


def test_no_value_exceeds_the_maximum():
    for failures in range(1, 200):
        for jitter in (0.0, 0.5, 0.999999, 1.0):
            assert compute_backoff_seconds(failures, PRODUCTION_BACKOFF, jitter) <= 60


def test_zero_failures_waits_nothing():
    assert compute_backoff_seconds(0, PRODUCTION_BACKOFF, 1.0) == 0


def test_settings_in_milliseconds_are_supported_for_tests():
    tiny = BackoffSettings(initial_seconds=0.001, max_seconds=0.004)
    assert [compute_backoff_seconds(n, tiny, 1.0) for n in (1, 2, 3, 4)] == [0.001, 0.002, 0.004, 0.004]


def test_huge_failure_counts_do_not_overflow():
    assert compute_backoff_seconds(10_000, PRODUCTION_BACKOFF, 1.0) == 60


def test_negative_failures_are_rejected():
    with pytest.raises(ValueError):
        compute_backoff_seconds(-1, PRODUCTION_BACKOFF, 1.0)
