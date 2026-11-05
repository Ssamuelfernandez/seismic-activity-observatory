"""Cargador del histórico: lee los archivos verificados y los procesa como el consumidor (B16).

No valida, no convierte tiempos ni asigna país: cada evento se entrega a
`consumer.pipeline.process_record`, la misma canalización del consumo en vivo (research D1).
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from common.kafka_topics import TOPIC_LIVE
from common.records import ProcessingResult, RawRecord, ResultKind, VersionOutcome
from consumer.pipeline import PipelineDeps, process_record
from historical.dedup import dedup_features
from historical.download_files import read_features
from historical.envelope import ISO_UTC_FORMAT, build_message_bytes
from historical.manifest import FileRecord, Manifest, ManifestFileError, MANIFEST_NAME, read_manifest, verify_file

logger = logging.getLogger(__name__)


@dataclass
class LoadSummary:
    """Resumen de una carga (FR-013): únicos, resultado por evento y eventos por archivo."""

    unique: int = 0
    new_event: int = 0
    newer_version: int = 0
    unchanged: int = 0
    late_old: int = 0
    same_updated_conflict: int = 0
    quarantined: int = 0
    by_file: dict[str, int] = field(default_factory=dict)
    event_ids: list[str] = field(default_factory=list)
    quarantined_ids: list[str] = field(default_factory=list)


OUTCOME_FIELDS = {
    VersionOutcome.NEW_EVENT: "new_event",
    VersionOutcome.NEWER_VERSION: "newer_version",
    VersionOutcome.REDELIVERY: "unchanged",
    VersionOutcome.LATE_OLD_VERSION: "late_old",
    VersionOutcome.SAME_UPDATED_CONFLICT: "same_updated_conflict",
}


def _read_verified(directory: Path) -> Manifest:
    """Lee el manifiesto y comprueba cada archivo antes de escribir nada."""
    manifest = read_manifest(directory)
    if manifest is None:
        raise ManifestFileError(f"falta {MANIFEST_NAME} en {directory}")
    for record in manifest.files + manifest.gaps:
        verify_file(directory, record)
    return manifest


def _origins(records: list[FileRecord], lists: list[list[dict]]) -> dict[int, FileRecord]:
    """Asocia cada feature (por identidad del objeto) con el archivo del que viene."""
    return {id(feature): record for record, features in zip(records, lists) for feature in features}


def _to_raw_record(feature: dict, record: FileRecord, is_synthetic: bool) -> RawRecord:
    """Arma el `RawRecord` sin referencia Kafka con el mensaje del contrato."""
    extracted = datetime.strptime(record.extracted_at, ISO_UTC_FORMAT).replace(tzinfo=timezone.utc)
    return RawRecord(TOPIC_LIVE, None, None, None, build_message_bytes(feature, extracted, is_synthetic))


def _tally(summary: LoadSummary, result: ProcessingResult, file_name: str) -> None:
    """Suma el resultado de un evento al resumen."""
    summary.by_file[file_name] = summary.by_file.get(file_name, 0) + 1
    if result.kind is ResultKind.QUARANTINE:
        summary.quarantined += 1
        if result.event_id is not None:
            summary.quarantined_ids.append(result.event_id)
        return
    name = OUTCOME_FIELDS[result.outcome]
    setattr(summary, name, getattr(summary, name) + 1)


def _collect_id(summary: LoadSummary, feature: dict) -> None:
    """Anota el `id` de la feature si lo tiene (conjunto U de la verificación, research D7)."""
    event_id = feature.get("id")
    if isinstance(event_id, str) and event_id != "":
        summary.event_ids.append(event_id)


async def load_historical(directory: Path, deps: PipelineDeps, is_synthetic: bool = False) -> LoadSummary:
    """Carga en la base los archivos del manifiesto de `directory`.

    Qué hace:
        Verifica el sha256 de todos los archivos (si falla, no escribe nada), deduplica entre
        archivos y entrega cada evento único a `process_record`. Una cuarentena no detiene la carga.
    Recibe:
        directory: carpeta con `manifest.json`; deps: dependencias de `process_record`;
        is_synthetic: verdadero solo con fixtures de prueba.
    Devuelve:
        `LoadSummary` con los conteos por resultado y por archivo.
    Por qué existe:
        Reutiliza las reglas del consumidor para el histórico, sin duplicarlas (B16, FR-009).
    """
    manifest = _read_verified(directory)
    records = manifest.files + manifest.gaps
    lists = [read_features(directory, record.name) for record in records]
    origins = _origins(records, lists)
    unique = dedup_features(lists).features
    summary = LoadSummary(unique=len(unique))
    for feature in unique:
        record = origins[id(feature)]
        _collect_id(summary, feature)
        result = await process_record(_to_raw_record(feature, record, is_synthetic), deps)
        _tally(summary, result, record.name)
    for name, events in summary.by_file.items():
        logger.info("historical_load file=%s events=%d", name, events)
    return summary
