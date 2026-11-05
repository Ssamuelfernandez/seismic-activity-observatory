"""Archivos GeoJSON crudos del histórico: nombres, escritura y reutilización (B13, B15)."""
import json
from pathlib import Path

from historical.fetch_interval import IntervalData
from historical.intervals import Interval
from historical.manifest import FileRecord, ManifestFileError, sha256_of, verify_file

GAP_TIME_FORMAT = "%Y%m%dT%H%M%S"


def month_file_name(interval: Interval) -> str:
    """Nombre del archivo mensual: `usgs_AAAA-MM.geojson`."""
    return f"usgs_{interval.start:%Y-%m}.geojson"


def gap_file_name(interval: Interval) -> str:
    """Nombre del archivo de un hueco: `usgs_gap_<inicio>_<fin>.geojson` (UTC, sin separadores)."""
    return f"usgs_gap_{interval.start.strftime(GAP_TIME_FORMAT)}_{interval.end.strftime(GAP_TIME_FORMAT)}.geojson"


def write_collection(directory: Path, name: str, data: IntervalData) -> FileRecord:
    """Escribe el `FeatureCollection` fusionado y devuelve su registro con el sha256 del archivo."""
    collection = {"type": "FeatureCollection", "metadata": data.metadata, "features": data.features}
    body = json.dumps(collection, ensure_ascii=False).encode("utf-8")
    (directory / name).write_bytes(body)
    return FileRecord(name, sha256_of(body), len(data.features), data.extracted_at, data.queries)


def read_features(directory: Path, name: str) -> list[dict]:
    """Lee las features de un archivo ya escrito."""
    return json.loads((directory / name).read_text(encoding="utf-8"))["features"]


def find_reusable(directory: Path, known: list[FileRecord], name: str) -> FileRecord | None:
    """Devuelve el registro del manifiesto si el archivo existe y su sha256 coincide; si no, None."""
    for record in known:
        if record.name != name:
            continue
        try:
            verify_file(directory, record)
        except ManifestFileError:
            return None
        return record
    return None
