"""Operación b: asignar país a puntos con un bucle ingenuo y con `STRtree` (K1, K2, FR-002, FR-003).

Ambos métodos aplican la misma regla (D4): el borde cuenta como dentro y, con varios candidatos,
gana el `ADM0_A3` menor. El bucle ingenuo recorre los polígonos ordenados por `ADM0_A3` y se
detiene en el primer acierto; el método con `STRtree` llama a `common/geo.py::assign_country`.
Los puntos son SINTÉTICOS (derivados de `bench`); el conjunto «océano» no tiene país.
"""
import random

from shapely.geometry import Point

from common.geo import CountryCatalog, CountryIndex, assign_country, build_country_index
from scripts.benchmarks.measure import measure_peak_kib, measure_time
from scripts.benchmarks.records import Measurement, build_measurement
from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX

OPERATION = "geo"
THEORY = {"naive": "O(n*p), p = polígonos del catálogo", "strtree": "O(n*(log p + candidatos))",
          "strtree_build": "O(p log p)"}
OCEAN_SEED = 20251113

Points = list[tuple[float, float]]
Polygons = list[tuple[str, object]]


def sorted_polygons(catalog: CountryCatalog) -> Polygons:
    """Pares `(ADM0_A3, geometría)` ordenados por código: el primer acierto es el código menor."""
    return sorted(((e.row.country_id, e.geometry) for e in catalog.entries), key=lambda pair: pair[0])


def assign_naive(polygons: Polygons, lon: float, lat: float) -> str | None:
    """Bucle ingenuo: recorre los polígonos en orden y devuelve el primer país que cubre el punto."""
    point = Point(lon, lat)
    for code, geometry in polygons:
        if geometry.covers(point):
            return code
    return None


def classify_naive(polygons: Polygons, points: Points) -> list[str | None]:
    """País de cada punto con el bucle ingenuo."""
    return [assign_naive(polygons, lon, lat) for lon, lat in points]


def classify_tree(index: CountryIndex, points: Points) -> list[str | None]:
    """País de cada punto con `assign_country` (`STRtree`)."""
    return [assign_country(index, lon, lat).country_id for lon, lat in points]


def ocean_points(index: CountryIndex, count: int, rng_seed: int = OCEAN_SEED) -> Points:
    """Puntos deterministas sin país (peor caso del bucle ingenuo: recorre todos los polígonos).

    Sortea coordenadas con semilla fija y conserva las que el índice no asigna a ningún país.
    """
    rng, points = random.Random(rng_seed), []
    while len(points) < count:
        lon, lat = rng.uniform(-180, 180), rng.uniform(-90, 90)
        if assign_country(index, lon, lat).country_id is None:
            points.append((lon, lat))
    return points


def count_differences(naive: list[str | None], tree: list[str | None]) -> int:
    """Número de puntos cuyo resultado difiere entre los dos métodos."""
    return sum(1 for a, b in zip(naive, tree, strict=True) if a != b)


def points_of(rows: list[dict]) -> Points:
    """Coordenadas `(lon, lat)` de las filas sintéticas (conjunto «mixto»)."""
    return [(row["lon"], row["lat"]) for row in rows]


def run_geo(rows: list[dict], size: int, catalog: CountryCatalog, n_max: int = N_MAX,
            budget: float = BUDGET_SECONDS) -> list[Measurement]:
    """Mide ingenuo y `STRtree` en los conjuntos «mixto» y «océano», más la construcción del índice.

    Recibe:
        rows: filas sintéticas del tamaño; size: tamaño; catalog: catálogo real parseado;
        n_max y budget: repeticiones y presupuesto por combinación.
    Devuelve:
        5 mediciones (2 métodos x 2 conjuntos + construcción) con el recuento de puntos con
        resultado distinto en `notes`.
    Por qué existe:
        Contrasta el coste de recorrer los polígonos con el del índice espacial (K1, K2).
    """
    polygons, index = sorted_polygons(catalog), build_country_index(catalog)
    sets = {"mixed": points_of(rows), "ocean": ocean_points(index, size)}
    build = measure_time(lambda: build_country_index(catalog), n_max, budget)
    out = [build_measurement(OPERATION, "strtree_build", size, "build", build, theory=THEORY["strtree_build"],
                             peak_kib=measure_peak_kib(lambda: build_country_index(catalog)))]
    for case, points in sets.items():
        diffs = count_differences(classify_naive(polygons, points), classify_tree(index, points))
        note = f"puntos con resultado distinto entre métodos: {diffs} de {len(points)}"
        for strategy, fn in (("naive", lambda p=points: classify_naive(polygons, p)),
                             ("strtree", lambda p=points: classify_tree(index, p))):
            out.append(build_measurement(OPERATION, strategy, size, case, measure_time(fn, n_max, budget),
                                         peak_kib=measure_peak_kib(fn), notes=note, theory=THEORY[strategy]))
    return out
