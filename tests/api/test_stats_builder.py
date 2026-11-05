"""Pruebas de api/stats_builder.py: horas, tramos, países y comparación (api.md §5)."""
import json
from api.stats_builder import (DEPTH_THRESHOLDS, MAGNITUDE_THRESHOLDS, build_bins, build_by_country,
                               build_by_hour, build_comparison, build_histogram, count_without_bucket,
                               effective_comparison_min_mag)

HOUR = 3_600_000
BASE = 1_793_455_200_000  # hora exacta (múltiplo de HOUR)


def test_hours_include_zero_counts_from_start_hour_to_last_millisecond():
    rows = [{"hour_start": BASE + HOUR, "count": 3}]
    buckets = build_by_hour(rows, BASE + 1_000, BASE + 3 * HOUR)["buckets"]
    assert [b["hour_start"] for b in buckets] == [BASE, BASE + HOUR, BASE + 2 * HOUR]
    assert [b["count"] for b in buckets] == [0, 3, 0]


def test_hours_end_exactly_on_the_hour_excludes_that_hour():
    buckets = build_by_hour([], BASE, BASE + HOUR)["buckets"]
    assert [b["hour_start"] for b in buckets] == [BASE]


def test_hours_end_one_ms_after_the_hour_includes_it():
    buckets = build_by_hour([], BASE, BASE + HOUR + 1)["buckets"]
    assert len(buckets) == 2


def test_by_hour_block_has_unit_and_no_value_zero():
    block = build_by_hour([], BASE, BASE + HOUR)
    assert (block["unit"], block["no_value"]) == ("events", 0)


def test_magnitude_bins_have_eight_ranges_with_open_ends_and_zeros():
    bins = build_bins([{"bucket": 0, "count": 5}, {"bucket": 4, "count": 2}], MAGNITUDE_THRESHOLDS)
    assert len(bins) == 8
    assert bins[0] == {"lower": None, "upper": 1, "count": 5}
    assert bins[4] == {"lower": 4, "upper": 5, "count": 2}
    assert bins[7] == {"lower": 7, "upper": None, "count": 0}
    assert [b["count"] for b in bins] == [5, 0, 0, 0, 2, 0, 0, 0]


def test_depth_bins_have_five_ranges():
    bins = build_bins([{"bucket": 4, "count": 1}], DEPTH_THRESHOLDS)
    assert [(b["lower"], b["upper"]) for b in bins] == [(None, 10), (10, 35), (35, 70), (70, 300), (300, None)]
    assert bins[4]["count"] == 1


def test_null_bucket_goes_to_no_value_and_not_to_bins():
    rows = [{"bucket": None, "count": 4}, {"bucket": 1, "count": 3}]
    assert count_without_bucket(rows) == 4
    histogram = build_histogram(rows, DEPTH_THRESHOLDS, "km", count_without_bucket(rows))
    assert histogram["no_value"] == 4 and sum(b["count"] for b in histogram["bins"]) == 3
    assert histogram["unit"] == "km"


def test_by_country_has_one_item_without_country_and_no_value_equals_its_count():
    rows = [{"country_id": "USA", "country_name": "Estados Unidos", "subregion": "N", "count": 151},
            {"country_id": None, "country_name": None, "subregion": None, "count": 47}]
    block = build_by_country(rows)
    assert block["no_value"] == 47
    assert block["items"][1] == {"country_id": None, "country_name": None, "subregion": None, "count": 47}
    assert [i["country_id"] for i in block["items"]].count(None) == 1


def test_by_country_without_unassigned_has_no_value_zero():
    rows = [{"country_id": "ESP", "country_name": "España", "subregion": "S", "count": 2}]
    assert build_by_country(rows)["no_value"] == 0


def test_comparison_reproduces_contract_example():
    generated = 1_793_543_640_000
    block = build_comparison(24, 12_410, None, generated)
    assert block["daily_mean_2025"] == 12_410 / 365
    assert round(block["daily_mean_2025"], 1) == 34.0
    assert round(block["diff_abs"], 1) == -10.0
    assert block["variation_pct"] == -29.41
    assert block["min_mag_applied"] == 4.0 and block["recent_incomplete"] is True
    assert block["recent_period"] == {"start": 1_793_457_240_000, "end": generated}
    assert block["reference_period"] == {"start": 1_735_689_600_000, "end": 1_767_225_600_000}
    assert block["unit"] == "events"


def test_comparison_variation_is_null_when_mean_is_zero():
    block = build_comparison(5, 0, None, BASE)
    assert block["daily_mean_2025"] == 0 and block["diff_abs"] == 5
    assert block["variation_pct"] is None
    json.dumps(block, allow_nan=False)


def test_min_mag_applied_is_the_larger_of_request_and_four():
    assert effective_comparison_min_mag(None) == 4.0
    assert effective_comparison_min_mag(2) == 4.0
    assert effective_comparison_min_mag(5.5) == 5.5
    assert effective_comparison_min_mag(-1.0) == 4.0
