"""Lectura verificada de los archivos históricos para el replay (J1, J7). Lee disco."""
from pathlib import Path

from historical.dedup import dedup_features
from historical.download_files import read_features
from historical.manifest import MANIFEST_NAME, ManifestFileError, read_manifest, verify_file


class ReplaySourceError(Exception):
    """Un archivo de origen falta, está alterado o no se puede leer; el mensaje lo nombra."""


def load_verified_features(directory: Path) -> list[tuple[dict, str]]:
    """Lee los archivos mensuales del manifiesto tras verificar su sha256.

    Qué hace:
        Verifica todos los archivos antes de leer nada, deduplica por `id`/`updated` y
        devuelve cada evento con el `extracted_at` de su archivo. `usgs_gap_*` no se usa.
    Recibe:
        directory: carpeta con `manifest.json` y los archivos.
    Devuelve:
        Lista de pares `(feature, extracted_at)`.
    Lanza:
        ReplaySourceError que nombra el archivo si falta, difiere o no se puede leer.
    Por qué existe:
        Garantiza que el replay solo publica datos reales íntegros (FR-001, FR-006).
    """
    try:
        manifest = read_manifest(directory)
    except (OSError, ValueError, KeyError) as error:
        raise ReplaySourceError(f"no se puede leer {MANIFEST_NAME}: {error}") from error
    if manifest is None:
        raise ReplaySourceError(f"falta {MANIFEST_NAME} en {directory}")
    lists: list[list[dict]] = []
    for record in manifest.files:
        try:
            verify_file(directory, record)
            lists.append(read_features(directory, record.name))
        except ManifestFileError as error:
            raise ReplaySourceError(str(error)) from error
        except (OSError, ValueError, KeyError) as error:
            raise ReplaySourceError(f"no se puede leer {record.name}: {error}") from error
    extracted = {id(feature): record.extracted_at for record, features in zip(manifest.files, lists) for feature in features}
    return [(feature, extracted[id(feature)]) for feature in dedup_features(lists).features]
