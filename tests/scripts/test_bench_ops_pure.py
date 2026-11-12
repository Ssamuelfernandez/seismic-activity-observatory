"""Pruebas sin Docker de las operaciones a (búsqueda) y b (geografía) de las mediciones (T080, T081).

Los datos son SINTÉTICOS (derivados de la semilla real); el catálogo de países es el real.
"""
import json
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from common.geo import CountryCatalog, CountryEntry, assign_country, build_country_index, parse_country_catalog
from common.records import CountryRow
from scripts.benchmarks.op_geo import (assign_naive, classify_naive, classify_tree, count_differences,
                                       ocean_points, points_of, run_geo, sorted_polygons)
from scripts.benchmarks.op_search import (ABSENT_ID, CASES, build_dict, find_in_list, measure_memory_strategies,
                                          pick_ids)
from scripts.benchmarks.seed import load_seed
from scripts.benchmarks.synth import build_rows

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalog() -> CountryCatalog:
    return parse_country_catalog(json.loads((ROOT / "data" / "catalogo" / "paises.geojson").read_text("utf-8")))


@pytest.fixture(scope="module")
def rows(catalog: CountryCatalog) -> list[dict]:
    index = build_country_index(catalog)
    seed = load_seed(ROOT / "data" / "historical").events
    return build_rows(seed, 1_000, lambda lon, lat: assign_country(index, lon, lat).country_id)


def test_list_and_dict_find_same_event_and_absent(rows: list[dict]) -> None:
    ids, lookup = pick_ids(rows), build_dict(rows)
    for case in ("first", "middle", "last"):
        assert find_in_list(rows, ids[case]) is lookup[ids[case]] is not None
    assert ids["absent"] == ABSENT_ID
    assert find_in_list(rows, ids["absent"]) is None and lookup.get(ids["absent"]) is None


def test_memory_strategies_give_eight_measurements_plus_build(rows: list[dict]) -> None:
    result = measure_memory_strategies(rows, 1_000, n_max=3, budget=1)
    assert [m.id for m in result if m.strategy in ("list", "dict")] == [
        f"search.{s}.1000.{c}" for s in ("list", "dict") for c in CASES]
    build = [m for m in result if m.strategy == "dict_build"]
    assert len(build) == 1 and build[0].peak_kib > 0 and all(m.n_real >= 3 for m in result)


def test_both_geo_methods_agree_on_mixed_and_ocean(catalog: CountryCatalog, rows: list[dict]) -> None:
    index, polygons = build_country_index(catalog), sorted_polygons(catalog)
    mixed, ocean = points_of(rows), ocean_points(index, 1_000)
    for points in (mixed, ocean):
        assert count_differences(classify_naive(polygons, points), classify_tree(index, points)) == 0
    assert set(classify_tree(index, ocean)) == {None}
    assert any(classify_tree(index, mixed))


def test_run_geo_reports_five_measurements_with_zero_differences(catalog: CountryCatalog, rows: list[dict]) -> None:
    result = run_geo(rows[:50], 50, catalog, n_max=3, budget=1)
    assert sorted(m.id for m in result) == sorted([
        "geo.strtree_build.50.build", "geo.naive.50.mixed", "geo.naive.50.ocean",
        "geo.strtree.50.mixed", "geo.strtree.50.ocean"])
    assert all("distinto entre métodos: 0 de 50" in m.notes for m in result if m.case in ("mixed", "ocean"))


def _catalog(shapes: dict[str, Polygon]) -> CountryCatalog:
    return CountryCatalog(tuple(CountryEntry(CountryRow(code, code, "", "", ""), geometry)
                                for code, geometry in shapes.items()))


def test_border_and_overlap_points_give_same_result_in_both_methods() -> None:
    shapes = {"BBB": Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]), "AAA": Polygon([(1, 1), (3, 1), (3, 3), (1, 3)])}
    catalog = _catalog(shapes)
    points = [(0.0, 1.0), (1.5, 1.5), (5.0, 5.0)]  # borde de BBB, en ambos, fuera de ambos
    naive = classify_naive(sorted_polygons(catalog), points)
    assert naive == classify_tree(build_country_index(catalog), points) == ["BBB", "AAA", None]
    assert assign_naive(sorted_polygons(catalog), 2.0, 2.0) == "AAA"  # esquina compartida: el código menor
