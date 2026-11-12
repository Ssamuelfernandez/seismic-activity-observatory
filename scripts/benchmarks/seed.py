"""Semilla real de las mediciones: los eventos únicos de 2025 verificados por sha256 (K4, FR-014).

Reutiliza `historical/manifest.py` (verificación) y `historical/dedup.py` (deduplicación): la
misma regla con la que se cargó el histórico, sin duplicar lógica.
"""
from dataclasses import dataclass
from pathlib import Path

from historical.dedup import dedup_features
from historical.download_files import read_features
from historical.manifest import MANIFEST_NAME, ManifestFileError, read_manifest, verify_file


class SeedError(Exception):
    """La semilla no se puede usar: falta el manifiesto, un archivo, o su sha256 no coincide."""


@dataclass(frozen=True)
class SeedData:
    """Eventos únicos de la semilla y nombres de los archivos cuyo sha256 se verificó."""

    events: list[dict]
    verified_files: list[str]


def load_seed(directory: Path) -> SeedData:
    """Lee `data/historical/`, verifica los sha256 y devuelve los eventos únicos.

    Qué hace:
        Lee `manifest.json`, comprueba el sha256 de cada archivo (mensuales y de hueco) antes de
        leer ninguno y deduplica por `id`/`updated` con `historical/dedup.py`.
    Recibe:
        directory: carpeta con `manifest.json` y los archivos GeoJSON.
    Devuelve:
        `SeedData` (en la carga real: 18.302 eventos únicos y 13 archivos verificados).
    Por qué existe:
        Las filas sintéticas parten de datos reales íntegros; ante un archivo alterado se
        detiene sin devolver nada (K4, FR-014, borde de la spec).
    """
    manifest = read_manifest(directory)
    if manifest is None:
        raise SeedError(f"falta {MANIFEST_NAME} en {directory}")
    records = manifest.files + manifest.gaps
    try:
        for record in records:
            verify_file(directory, record)
    except ManifestFileError as error:
        raise SeedError(str(error)) from error
    lists = [read_features(directory, record.name) for record in records]
    return SeedData(dedup_features(lists).features, [record.name for record in records])
