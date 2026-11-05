"""Manifiesto de procedencia de los archivos históricos (data-model §2 y §3, B15)."""
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

MANIFEST_NAME = "manifest.json"
MANIFEST_VERSION = 1
TEMP_SUFFIX = ".tmp"
DEFAULT_PARAMETERS = {"minmagnitude": 4, "eventtype": "earthquake", "orderby": "time-asc", "format": "geojson"}


class ManifestFileError(Exception):
    """Un archivo del manifiesto falta o su sha256 no coincide."""


@dataclass(frozen=True)
class QueryRecord:
    """Una consulta ya hecha: URL, tramo, `count` de USGS y registros devueltos."""

    url: str
    start: str
    end: str
    usgs_count: int
    records: int


@dataclass(frozen=True)
class FileRecord:
    """Un archivo del manifiesto con su sha256, registros y consultas."""

    name: str
    sha256: str
    records: int
    extracted_at: str
    queries: list[QueryRecord]


@dataclass(frozen=True)
class Totals:
    """Totales de 2025: registros, duplicados descartados, únicos y `count` anual de USGS."""

    records: int
    duplicates_discarded: int
    unique: int
    usgs_count_year: int


@dataclass(frozen=True)
class Manifest:
    """Procedencia completa de la descarga."""

    year: int
    files: list[FileRecord]
    gaps: list[FileRecord]
    totals: Totals
    parameters: dict = field(default_factory=lambda: dict(DEFAULT_PARAMETERS))
    version: int = MANIFEST_VERSION


def sha256_of(data: bytes) -> str:
    """Devuelve el sha256 hexadecimal de unos bytes."""
    return hashlib.sha256(data).hexdigest()


def write_manifest(directory: Path, manifest: Manifest) -> None:
    """Escribe `manifest.json` de forma atómica (archivo temporal y renombrado)."""
    target = directory / MANIFEST_NAME
    temporary = directory / (MANIFEST_NAME + TEMP_SUFFIX)
    text = json.dumps(asdict(manifest), indent=2, ensure_ascii=False) + "\n"
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, target)


def _file_from_dict(data: dict) -> FileRecord:
    """Reconstruye un `FileRecord` desde el JSON."""
    queries = [QueryRecord(**query) for query in data["queries"]]
    return FileRecord(data["name"], data["sha256"], data["records"], data["extracted_at"], queries)


def read_manifest(directory: Path) -> Manifest | None:
    """Lee `manifest.json`; devuelve None si no existe."""
    path = directory / MANIFEST_NAME
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        year=data["year"],
        files=[_file_from_dict(item) for item in data["files"]],
        gaps=[_file_from_dict(item) for item in data["gaps"]],
        totals=Totals(**data["totals"]),
        parameters=data["parameters"],
        version=data["version"],
    )


def verify_file(directory: Path, record: FileRecord) -> None:
    """Comprueba que el archivo existe y que su sha256 coincide con el manifiesto.

    Lanza:
        ManifestFileError que nombra el archivo si falta o si el sha256 difiere.
    """
    path = directory / record.name
    if not path.is_file():
        raise ManifestFileError(f"falta el archivo {record.name}")
    actual = sha256_of(path.read_bytes())
    if actual != record.sha256:
        raise ManifestFileError(f"sha256 distinto en {record.name}: esperado {record.sha256}, real {actual}")
