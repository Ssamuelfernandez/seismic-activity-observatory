"""Muestra real de un día: asigna país a cada evento de un feed `all_day` guardado (T019, SC-007).

Uso:
    python scripts/geo_real_day.py docs/evidencias/geografia-pais/feed_all_day.geojson [--catalog RUTA]

Sin red, sin Kafka y sin base: lee el GeoJSON del feed y el catálogo, usa `common/geo.py` y escribe
cuántos eventos tienen país, cuántos no, los códigos distintos y si todo código asignado está en el
catálogo. Es una muestra de un momento: no afirma cobertura general. `print` está permitido (CLI).
"""
import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# El script se ejecuta como `python scripts/geo_real_day.py`: se añade la raíz para importar `common`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.geo import assign_country, build_country_index, parse_country_catalog  # noqa: E402

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalogo" / "paises.geojson"
EXIT_OK = 0
EXIT_ERROR = 1
TOP_CODES = 10


@dataclass(frozen=True)
class DaySummary:
    """Resultado de asignar país a los eventos de un feed."""

    total: int
    skipped: int
    with_country: int
    without_country: int
    by_country: Counter
    unknown_codes: tuple[str, ...]


def _point(feature: dict) -> tuple[float, float] | None:
    """Longitud y latitud de un evento, o None si la geometría no es un `Point` con números."""
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    if geometry.get("type") != "Point" or not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    lon, lat = coordinates[0], coordinates[1]
    numeric = all(type(value) in (int, float) for value in (lon, lat))
    return (lon, lat) if numeric else None


def summarize_day(feed: dict, catalog_geojson: dict) -> DaySummary:
    """Asigna país a cada evento del feed con el mismo código que usa el consumidor.

    Qué hace:
        Parsea el catálogo, construye el índice y llama a `assign_country` por evento. Los eventos
        sin `Point` válido se cuentan aparte (`skipped`) y no se asignan.
    Recibe:
        feed: FeatureCollection del feed de USGS; catalog_geojson: catálogo de países ya cargado.
    Devuelve:
        `DaySummary` con los recuentos y los códigos asignados que no están en el catálogo.
    Por qué existe:
        Comprueba con datos reales de un día que el país se asigna por geometría y que todo
        código asignado existe en `public.country` (C9, C12).
    """
    catalog = parse_country_catalog(catalog_geojson)
    index = build_country_index(catalog)
    known = {entry.row.country_id for entry in catalog.entries}
    by_country: Counter = Counter()
    without_country = skipped = 0
    features = feed.get("features", [])
    for feature in features:
        point = _point(feature)
        if point is None:
            skipped += 1
            continue
        country = assign_country(index, *point).country_id
        if country is None:
            without_country += 1
        else:
            by_country[country] += 1
    unknown = tuple(sorted(code for code in by_country if code not in known))
    return DaySummary(len(features), skipped, sum(by_country.values()), without_country, by_country, unknown)


def format_summary(summary: DaySummary) -> str:
    """Texto de la evidencia; termina en «sin error» solo si todo código asignado está en el catálogo."""
    top = ", ".join(f"{code}={count}" for code, count in summary.by_country.most_common(TOP_CODES))
    lines = [
        f"eventos en el feed: {summary.total}",
        f"sin geometría Point válida (no asignados): {summary.skipped}",
        f"con país: {summary.with_country}",
        f"sin país (country_id NULL): {summary.without_country}",
        f"códigos distintos: {len(summary.by_country)}",
        f"los {TOP_CODES} más frecuentes: {top}",
        f"códigos fuera del catálogo: {', '.join(summary.unknown_codes) or 'ninguno'}",
        "resultado: sin error" if not summary.unknown_codes else "resultado: ERROR",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Parser de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("feed", type=Path, help="GeoJSON del feed all_day guardado")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="catálogo de países (GeoJSON)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Lee el feed y el catálogo, imprime el resumen y devuelve el código de salida."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    feed = json.loads(args.feed.read_text(encoding="utf-8"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    summary = summarize_day(feed, catalog)
    print(format_summary(summary))
    return EXIT_ERROR if summary.unknown_codes else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
