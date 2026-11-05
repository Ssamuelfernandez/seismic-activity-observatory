"""Pruebas de `common/geo.py`: catálogo de países y asignación por geometría (C9-C12).

Los catálogos sintéticos son cuadrados inventados; el real es `data/catalogo/paises.geojson`.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from common.geo import CatalogError, assign_country, build_country_index, parse_country_catalog

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "catalogo" / "paises.geojson"
EXPECTED_COUNTRIES = 177


def _square(code: str, x0: float, y0: float, size: float = 10.0) -> dict:
    """Entidad sintética: cuadrado de lado `size` con la esquina inferior en (x0, y0)."""
    ring = [[x0, y0], [x0 + size, y0], [x0 + size, y0 + size], [x0, y0 + size], [x0, y0]]
    return {
        "type": "Feature",
        "properties": {
            "ADM0_A3": code, "NAME_ES": f"Pais {code}", "ADMIN": f"Admin {code}",
            "CONTINENT": "Synthetic", "SUBREGION": "Synthetic",
        },
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def _catalog(*features: dict) -> dict:
    """Catálogo sintético mínimo con las entidades dadas."""
    return {"type": "FeatureCollection", "features": list(features)}


@pytest.fixture(scope="module")
def real_geojson() -> dict:
    """Catálogo real leído una vez."""
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def test_real_catalog_has_177_unique_codes(real_geojson):
    catalog = parse_country_catalog(real_geojson)
    codes = [entry.row.country_id for entry in catalog.entries]
    assert len(codes) == EXPECTED_COUNTRIES
    assert len(set(codes)) == EXPECTED_COUNTRIES


def test_real_catalog_maps_properties(real_geojson):
    catalog = parse_country_catalog(real_geojson)
    props = {f["properties"]["ADM0_A3"]: f["properties"] for f in real_geojson["features"]}
    for entry in catalog.entries:
        p = props[entry.row.country_id]
        assert entry.row.name_es == p["NAME_ES"]
        assert entry.row.admin == p["ADMIN"]
        assert entry.row.continent == p["CONTINENT"]
        assert entry.row.subregion == p["SUBREGION"]


def test_parsing_does_not_change_the_file(real_geojson):
    before = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    parse_country_catalog(real_geojson)
    assert hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest() == before


def test_duplicate_code_is_rejected_naming_it():
    with pytest.raises(CatalogError, match="AAA"):
        parse_country_catalog(_catalog(_square("AAA", 0, 0), _square("AAA", 20, 0)))


def test_missing_field_cites_field_and_position():
    broken = _square("BBB", 20, 0)
    del broken["properties"]["NAME_ES"]
    with pytest.raises(CatalogError, match="NAME_ES") as error:
        parse_country_catalog(_catalog(_square("AAA", 0, 0), broken))
    assert "1" in str(error.value)


def test_non_polygon_geometry_names_the_entity():
    point = copy.deepcopy(_square("CCC", 0, 0))
    point["geometry"] = {"type": "Point", "coordinates": [0, 0]}
    with pytest.raises(CatalogError, match="CCC"):
        parse_country_catalog(_catalog(point))


# --- Parte 2: asignación de país (C9, C11, C12) ---

REPEATS = 10


def _index(*features: dict):
    """Índice de un catálogo sintético."""
    return build_country_index(parse_country_catalog(_catalog(*features)))


@pytest.fixture(scope="module")
def real_index(real_geojson):
    """Índice del catálogo real, construido una vez."""
    return build_country_index(parse_country_catalog(real_geojson))


def test_madrid_is_spain(real_index):
    match = assign_country(real_index, -3.70, 40.42)
    assert match.country_id == "ESP"


def test_atlantic_has_no_country(real_index):
    match = assign_country(real_index, -30.0, 35.0)
    assert match.country_id is None
    assert match.candidates == ()


def test_interior_point_gets_its_country():
    index = _index(_square("AAA", 0, 0), _square("BBB", 20, 0))
    assert assign_country(index, 25, 5).country_id == "BBB"


def test_shared_edge_is_not_none_and_picks_lowest_code():
    index = _index(_square("BBB", 10, 0), _square("AAA", 0, 0))
    match = assign_country(index, 10, 5)
    assert match.country_id == "AAA"
    assert match.candidates == ("AAA", "BBB")


def test_overlapping_polygons_pick_lowest_code_and_list_both():
    index = _index(_square("ZZZ", 0, 0), _square("MMM", 5, 5))
    match = assign_country(index, 7, 7)
    assert match.country_id == "MMM"
    assert match.candidates == ("MMM", "ZZZ")


def test_same_result_in_repeated_runs_and_reversed_catalog():
    features = [_square("AAA", 0, 0), _square("BBB", 5, 5), _square("CCC", 20, 0)]
    results = {assign_country(_index(*features), 7, 7) for _ in range(REPEATS)}
    results.add(assign_country(_index(*reversed(features)), 7, 7))
    assert len(results) == 1


def test_real_polygon_vertex_is_not_none(real_geojson, real_index):
    spain = next(f for f in real_geojson["features"] if f["properties"]["ADM0_A3"] == "ESP")
    polygon = spain["geometry"]["coordinates"][0]
    lon, lat = (polygon[0] if spain["geometry"]["type"] == "Polygon" else polygon[0][0])
    assert assign_country(real_index, lon, lat).country_id is not None


@pytest.mark.parametrize("lon,lat", [(180, 0), (-180, 0), (0, 90), (0, -90), (180, 90), (-180, -90)])
def test_extreme_coordinates_do_not_raise(real_index, lon, lat):
    assert assign_country(real_index, lon, lat).candidates is not None
