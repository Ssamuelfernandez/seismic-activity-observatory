"""Descarga del año 2025 y de huecos: archivos crudos, deduplicación y manifiesto (B12-B15)."""
import logging
from dataclasses import replace
from pathlib import Path

from historical.dedup import dedup_features
from historical.download_files import (
    find_reusable, gap_file_name, month_file_name, read_features, write_collection,
)
from historical.fetch_interval import FetchTools, fetch_count, fetch_interval
from historical.intervals import Interval, month_intervals
from historical.manifest import FileRecord, Manifest, Totals, read_manifest, write_manifest

logger = logging.getLogger(__name__)

DEFAULT_YEAR = 2025
EMPTY_TOTALS = Totals(records=0, duplicates_discarded=0, unique=0, usgs_count_year=0)


class CountMismatchError(Exception):
    """El total único descargado no coincide con el `count` anual de USGS."""


def _base_manifest(directory: Path, year: int) -> Manifest:
    """Manifiesto existente o uno vacío del año."""
    return read_manifest(directory) or Manifest(year=year, files=[], gaps=[], totals=EMPTY_TOTALS)


def _partial_totals(files: list[FileRecord]) -> Totals:
    """Totales provisionales mientras faltan meses: solo los registros sumados."""
    return replace(EMPTY_TOTALS, records=sum(record.records for record in files))


async def _download_months(directory: Path, tools: FetchTools, force: bool, base: Manifest) -> tuple[Manifest, bool]:
    """Descarga o reutiliza los 12 meses; escribe el manifiesto parcial tras cada mes."""
    files: list[FileRecord] = []
    reused_all = True
    for interval in month_intervals(base.year):
        name = month_file_name(interval)
        record = None if force else find_reusable(directory, base.files, name)
        if record is None:
            reused_all = False
            data = await fetch_interval(interval, tools)
            record = write_collection(directory, name, data)
            logger.info("file name=%s records=%d sha256=%s", name, record.records, record.sha256)
        files.append(record)
        write_manifest(directory, replace(base, files=files, totals=_partial_totals(files)))
    return replace(base, files=files, totals=_partial_totals(files)), reused_all


async def _annual_count(base: Manifest, tools: FetchTools, reuse_stored: bool) -> int:
    """`count` anual de USGS; con todo reutilizado se usa el guardado en el manifiesto."""
    if reuse_stored and base.totals.usgs_count_year > 0:
        return base.totals.usgs_count_year
    months = month_intervals(base.year)
    return await fetch_count(Interval(months[0].start, months[-1].end), tools)


async def download_year(directory: Path, tools: FetchTools, force: bool = False, year: int = DEFAULT_YEAR) -> Manifest:
    """Descarga los 12 meses del año, los deduplica y comprueba el total contra USGS.

    Qué hace:
        Reutiliza los archivos con sha256 válido (salvo `force`), descarga el resto, escribe
        el manifiesto tras cada mes y al final calcula duplicados, únicos y `count` anual.
    Recibe:
        directory: carpeta de salida; tools: red y reloj inyectables; force: ignora lo existente;
        year: año a descargar.
    Devuelve:
        El `Manifest` completo, ya escrito en disco.
    Por qué existe:
        Es la descarga repetible y verificable del histórico (B13-B15, SC-001).
    Lanza:
        IntervalFetchError si un mes falla (lo ya descargado se conserva y se puede reanudar);
        CountMismatchError si el total único no coincide con el `count` anual.
    """
    directory.mkdir(parents=True, exist_ok=True)
    base = _base_manifest(directory, year)
    manifest, reused_all = await _download_months(directory, tools, force, base)
    usgs_count = await _annual_count(base, tools, reused_all and not force)
    result = dedup_features([read_features(directory, record.name) for record in manifest.files])
    totals = Totals(manifest.totals.records, result.discarded, len(result.features), usgs_count)
    manifest = replace(manifest, totals=totals)
    write_manifest(directory, manifest)
    logger.info("dedup duplicates=%d unique=%d usgs_count_year=%d", result.discarded, totals.unique, usgs_count)
    if totals.unique != usgs_count:
        raise CountMismatchError(f"únicos descargados {totals.unique} distinto del count anual de USGS {usgs_count}")
    return manifest


async def download_gap(directory: Path, interval: Interval, tools: FetchTools) -> Manifest:
    """Descarga un intervalo arbitrario (hueco) y lo añade a `gaps` sin tocar los totales de 2025.

    Qué hace:
        Pide el intervalo con las mismas reglas, guarda `usgs_gap_<inicio>_<fin>.geojson` y
        sustituye o añade su registro en `gaps`.
    Recibe:
        directory: carpeta de salida; interval: tramo a recuperar; tools: red y reloj.
    Devuelve:
        El `Manifest` actualizado y escrito.
    Por qué existe:
        Procedimiento de recuperación de un hueco de más de 24 h (B12, research D2).
    Lanza:
        ValueError si `end` no es posterior a `start`; IntervalFetchError si falla o no coincide `count`.
    """
    if interval.end <= interval.start:
        raise ValueError("el intervalo es inválido: end debe ser posterior a start")
    directory.mkdir(parents=True, exist_ok=True)
    base = _base_manifest(directory, DEFAULT_YEAR)
    name = gap_file_name(interval)
    record = write_collection(directory, name, await fetch_interval(interval, tools))
    gaps = [item for item in base.gaps if item.name != name] + [record]
    manifest = replace(base, gaps=gaps)
    write_manifest(directory, manifest)
    logger.info("gap name=%s records=%d sha256=%s", name, record.records, record.sha256)
    return manifest
