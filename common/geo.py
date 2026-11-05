"""Catálogo de países y asignación de país por geometría (C9-C12).

Módulo puro: recibe el GeoJSON ya cargado como `dict`, sin leer archivos ni tocar la base
ni Kafka. El país sale solo de la geometría del punto, nunca del texto `place` (constitución §4).
"""
import re
from dataclasses import dataclass

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from common.records import CountryRow

CODE_PATTERN = re.compile(r"^[A-Z]{3}$")
CODE_FIELD = "ADM0_A3"
TEXT_FIELDS = (
    ("NAME_ES", "name_es"),
    ("ADMIN", "admin"),
    ("CONTINENT", "continent"),
    ("SUBREGION", "subregion"),
)
POLYGON_TYPES = ("Polygon", "MultiPolygon")


class CatalogError(ValueError):
    """El catálogo de países no es utilizable (código repetido, campo ausente, geometría)."""


@dataclass(frozen=True)
class CountryEntry:
    """Una entidad del catálogo: su fila de `public.country` y su geometría."""

    row: CountryRow
    geometry: object


@dataclass(frozen=True)
class CountryCatalog:
    """Catálogo parseado; garantiza `ADM0_A3` único (C10)."""

    entries: tuple[CountryEntry, ...]


@dataclass(frozen=True)
class CountryIndex:
    """Índice espacial `STRtree` con los códigos alineados a las geometrías."""

    tree: STRtree
    codes: tuple[str, ...]


@dataclass(frozen=True)
class CountryMatch:
    """País asignado a un punto (`None` = sin país) y todos los candidatos, ordenados."""

    country_id: str | None
    candidates: tuple[str, ...]


def _text_property(props: dict, field: str, position: int) -> str:
    """Devuelve una propiedad de texto no vacía o lanza `CatalogError` citando campo y posición."""
    value = props.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"falta el campo '{field}' en la entidad {position}")
    return value


def _parse_row(props: dict, position: int) -> CountryRow:
    """Construye la fila de `public.country` de una entidad, comprobando el código."""
    code = _text_property(props, CODE_FIELD, position)
    if not CODE_PATTERN.match(code):
        raise CatalogError(f"{CODE_FIELD} inválido '{code}' en la entidad {position}")
    texts = [_text_property(props, source, position) for source, _ in TEXT_FIELDS]
    return CountryRow(code, *texts)


def _parse_geometry(raw: object, code: str):
    """Convierte la geometría a Shapely; solo `Polygon`/`MultiPolygon` no vacíos.

    No se exige validez: el archivo real trae USA y SDN con autointersecciones menores y se
    usa tal cual, sin `buffer(0)` (research.md D6); `covered_by` funciona igual con ellas.
    """
    kind = raw.get("type") if isinstance(raw, dict) else None
    if kind not in POLYGON_TYPES:
        raise CatalogError(f"la geometría de '{code}' no es Polygon ni MultiPolygon")
    geometry = shape(raw)
    if geometry.is_empty:
        raise CatalogError(f"la geometría de '{code}' está vacía")
    return geometry


def parse_country_catalog(geojson: dict) -> CountryCatalog:
    """Valida el GeoJSON del catálogo y lo convierte en entradas.

    Qué hace:
        Mapea `ADM0_A3`, `NAME_ES`, `ADMIN`, `CONTINENT` y `SUBREGION` a `CountryRow`,
        exige `ADM0_A3` único y geometría `Polygon`/`MultiPolygon`.
    Recibe:
        geojson: FeatureCollection ya cargado (CRS84, lon/lat).
    Devuelve:
        El catálogo con una entrada por entidad, en el orden del archivo.
    Por qué existe:
        Garantiza antes de tocar la base que `public.country` es coherente (C10).
    """
    entries: list[CountryEntry] = []
    seen: dict[str, int] = {}
    for position, feature in enumerate(geojson.get("features", [])):
        row = _parse_row(feature.get("properties") or {}, position)
        if row.country_id in seen:
            raise CatalogError(
                f"ADM0_A3 repetido '{row.country_id}' (entidades {seen[row.country_id]} y {position})"
            )
        seen[row.country_id] = position
        entries.append(CountryEntry(row, _parse_geometry(feature.get("geometry"), row.country_id)))
    return CountryCatalog(tuple(entries))


def build_country_index(catalog: CountryCatalog) -> CountryIndex:
    """Construye el índice espacial una sola vez (FR-019).

    Recibe:
        catalog: catálogo ya validado por `parse_country_catalog`.
    Devuelve:
        El `STRtree` con los códigos alineados a las geometrías.
    Por qué existe:
        Evita recorrer los 177 polígonos en cada mensaje (C9).
    """
    geometries = [entry.geometry for entry in catalog.entries]
    codes = tuple(entry.row.country_id for entry in catalog.entries)
    return CountryIndex(STRtree(geometries), codes)


def assign_country(index: CountryIndex, lon: float, lat: float) -> CountryMatch:
    """Asigna el país de un punto por geometría, con el borde incluido.

    Qué hace:
        Busca los polígonos que cubren el punto (`covered_by`); sin ninguno devuelve `None`;
        con varios elige el `ADM0_A3` menor, que no depende del orden del catálogo.
    Recibe:
        index: índice de `build_country_index`.
        lon, lat: coordenadas CRS84 del evento.
    Devuelve:
        `CountryMatch` con el país elegido y todos los candidatos ordenados.
    Por qué existe:
        Un punto en la frontera nunca queda sin país por error y el resultado es
        reproducible (C9, C11, C12).
    """
    hits = index.tree.query(Point(lon, lat), predicate="covered_by")
    candidates = tuple(sorted(index.codes[i] for i in hits))
    return CountryMatch(candidates[0] if candidates else None, candidates)
