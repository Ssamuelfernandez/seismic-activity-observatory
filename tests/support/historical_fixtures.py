"""Fixtures del cargador histórico: archivos GeoJSON y manifiesto en un directorio (SINTÉTICOS).

Todos los eventos llevan `id` `synthetic-…` (los crea `tests/support/messages.py`); los archivos
se escriben con el mismo código que el descargador (`write_collection`, `write_manifest`).
"""
from pathlib import Path

from historical.download_files import write_collection
from historical.fetch_interval import IntervalData
from historical.manifest import FileRecord, Manifest, Totals, write_manifest
from tests.support.messages import E1_TIME_MS, E1_UPDATED_1005, build_event

EXTRACTED_AT = "2026-01-02T03:04:05Z"
FIXTURE_YEAR = 2025
MINUTE_MS = 60_000


def synthetic_feature(event_id: str, updated_ms: int = E1_UPDATED_1005, mag: float | None = 4.5,
                      lon: float = -3.70, lat: float = 40.42) -> dict:
    """Feature sintética válida en las coordenadas indicadas (por defecto Madrid)."""
    event = build_event(event_id, E1_TIME_MS, updated_ms, mag)
    event["geometry"]["coordinates"] = [lon, lat, 10.0]
    return event


def _write_one(directory: Path, name: str, features: list[dict], extracted_at: str) -> FileRecord:
    """Escribe un archivo con sus features y devuelve su registro de manifiesto."""
    return write_collection(directory, name, IntervalData(features, [], extracted_at, {}))


def write_fixture(directory: Path, files: dict[str, list[dict]], gaps: dict[str, list[dict]] | None = None,
                  extracted_at: str = EXTRACTED_AT) -> Manifest:
    """Escribe los archivos y un `manifest.json` coherente; devuelve el manifiesto."""
    records = [_write_one(directory, name, features, extracted_at) for name, features in files.items()]
    gap_records = [_write_one(directory, name, features, extracted_at) for name, features in (gaps or {}).items()]
    total = sum(record.records for record in records)
    manifest = Manifest(FIXTURE_YEAR, records, gap_records, Totals(total, 0, total, total))
    write_manifest(directory, manifest)
    return manifest


BASE_ID = "synthetic-hist-"
ATLANTIC_POINT = (-30.0, 35.0)
FILE_NAMES = ("usgs_2025-01.geojson", "usgs_2025-02.geojson", "usgs_2025-03.geojson")
REPEATED_NUMBER = 5
BAD_IDS = {"lat": f"{BASE_ID}bad-lat", "mag": f"{BASE_ID}bad-mag", "lon": f"{BASE_ID}bad-lon"}
FIXTURE_UNIQUE = 29
FIXTURE_QUARANTINED = 3
FIXTURE_VALID = FIXTURE_UNIQUE - FIXTURE_QUARANTINED
REPEATED_V2_UPDATED = E1_UPDATED_1005 + 900 * MINUTE_MS


def hist_id(number: int) -> str:
    """Id sintético `synthetic-hist-NNN` del evento número `number`."""
    return f"{BASE_ID}{number:03d}"


def _numbered(numbers: range) -> list[dict]:
    """Eventos válidos: los impares en el Atlántico (sin país) y los pares en Madrid (ESP)."""
    events = []
    for n in numbers:
        place = {"lon": ATLANTIC_POINT[0], "lat": ATLANTIC_POINT[1]} if n % 2 else {}
        events.append(synthetic_feature(hist_id(n), E1_UPDATED_1005 + n * MINUTE_MS, **place))
    return events


def write_integration_fixture(directory: Path) -> Manifest:
    """Fixture de ~30 eventos en 3 archivos: 1 `id` repetido (v2 gana) y 3 inválidos.

    Únicos = 29 (30 features - 1 repetida), cuarentena = 3, `current_event` esperado = 26.
    """
    repeated_v2 = synthetic_feature(hist_id(REPEATED_NUMBER), REPEATED_V2_UPDATED)
    invalid = [synthetic_feature(BAD_IDS["lat"], lat=145), synthetic_feature(BAD_IDS["mag"], mag=99),
               synthetic_feature(BAD_IDS["lon"], lon=200)]
    return write_fixture(directory, {
        FILE_NAMES[0]: _numbered(range(1, 11)),
        FILE_NAMES[1]: _numbered(range(11, 20)) + [repeated_v2],
        FILE_NAMES[2]: _numbered(range(20, 27)) + invalid,
    })
