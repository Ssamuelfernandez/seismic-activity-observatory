"""Pruebas sin Docker del generador sintético (T077, K4). Semilla real; todo lo generado es SINTÉTICO."""
import json
from datetime import timedelta
from pathlib import Path

import pytest

from common.geo import assign_country, build_country_index, parse_country_catalog
from scripts.benchmarks.seed import load_seed
from scripts.benchmarks.synth import (COLUMNS, EPOCH, ID_PREFIX, SOURCE, YEAR_END_MS, YEAR_START_MS, build_rows,
                                      row_values)

ROOT = Path(__file__).resolve().parents[2]
REAL_SOURCES = {"usgs_feed", "usgs_historical", "replay_demo"}
LARGE = 100_000


def fast_locate(lon: float, lat: float) -> str | None:
    """Localizador de mentira (determinista y rápido) para las pruebas de volumen."""
    return None if lat < 0 else "AAA"


@pytest.fixture(scope="module")
def seed_events() -> list[dict]:
    return load_seed(ROOT / "data" / "historical").events


@pytest.fixture(scope="module")
def large_rows(seed_events: list[dict]) -> list[dict]:
    return build_rows(seed_events, LARGE, fast_locate)


def test_same_seed_gives_identical_rows(seed_events: list[dict]) -> None:
    assert build_rows(seed_events, 1_000, fast_locate) == build_rows(seed_events, 1_000, fast_locate)
    assert build_rows(seed_events, 1_000, fast_locate) != build_rows(seed_events, 1_000, fast_locate, rng_seed=1)


def test_all_rows_are_labelled_synthetic_with_unique_ids(large_rows: list[dict]) -> None:
    assert len(large_rows) == LARGE
    assert all(r["event_id"].startswith(ID_PREFIX) and r["is_synthetic"] is True for r in large_rows)
    assert {r["source"] for r in large_rows} == {SOURCE}
    assert not {r["source"] for r in large_rows} & REAL_SOURCES
    assert len({r["event_id"] for r in large_rows}) == LARGE


def test_requested_size_equals_returned_rows(seed_events: list[dict]) -> None:
    for size in (1_000, 10_000, 18_302):
        assert len(build_rows(seed_events, size, fast_locate)) == size


def test_coherence_and_ranges_hold_in_every_row(large_rows: list[dict]) -> None:
    for r in large_rows:
        assert YEAR_START_MS <= r["event_time_ms"] <= YEAR_END_MS
        assert r["event_time"] == EPOCH + timedelta(milliseconds=r["event_time_ms"])
        assert r["updated_ms"] >= r["event_time_ms"]
        assert r["updated_at"] - r["event_time"] == timedelta(milliseconds=r["updated_ms"] - r["event_time_ms"])
        assert r["date_id"] == r["event_time"].date()
        assert -180 <= r["lon"] <= 180 and -90 <= r["lat"] <= 90
        assert r["mag"] is None or -10 <= r["mag"] <= 15
        assert r["depth_km"] is None or -100 <= r["depth_km"] <= 1000
        assert tuple(r) == COLUMNS


def test_nulls_of_the_seed_are_kept_as_nulls(seed_events: list[dict]) -> None:
    null_mag = [e for e in seed_events if e["properties"].get("mag") is None]
    rows = build_rows(seed_events, 18_302, fast_locate)
    assert sum(r["mag"] is None for r in rows) == len(null_mag)
    assert all(r["mag"] != 0 for r in rows if r["mag"] is None)


def test_country_comes_from_the_real_geometry(seed_events: list[dict]) -> None:
    catalog = parse_country_catalog(json.loads((ROOT / "data" / "catalogo" / "paises.geojson").read_text("utf-8")))
    index = build_country_index(catalog)
    rows = build_rows(seed_events, 1_000, lambda lon, lat: assign_country(index, lon, lat).country_id)
    codes = {entry.row.country_id for entry in catalog.entries}
    assert {r["country_id"] for r in rows if r["country_id"]} <= codes
    assert any(r["country_id"] is None for r in rows) and any(r["country_id"] for r in rows)


def test_row_values_follow_the_column_order(seed_events: list[dict]) -> None:
    row = build_rows(seed_events, 1, fast_locate)[0]
    assert row_values(row) == tuple(row.values())
