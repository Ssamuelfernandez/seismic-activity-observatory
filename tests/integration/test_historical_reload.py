"""Recarga del histórico x3 sin diferencias (T015, B17, SC-005, FR-012).

Fixture SINTÉTICO. Cada carga abre un pool nuevo (equivale a reiniciar la conexión). Se compara la
huella (recuento y md5 agregado) de `current_event`, `event_version` y `quarantine` y, además, las
filas completas, antes y después de cada recarga.
"""
from pathlib import Path

from tests.support import evidence
from tests.support.geo_harness import admin_rows
from tests.support.historical_fixtures import FIXTURE_QUARANTINED, FIXTURE_UNIQUE, FIXTURE_VALID, write_integration_fixture
from tests.support.historical_harness import load_directory

EVIDENCE_NAME = "historico_recarga_huella"
ROWS_SQL = {
    "current_event": "SELECT * FROM live.current_event ORDER BY event_id",
    "event_version": "SELECT * FROM live.event_version ORDER BY event_id, updated_ms",
    "quarantine": "SELECT * FROM live.quarantine ORDER BY id",
}
RELOADS = 2


def _rows(db) -> dict[str, list[tuple]]:
    return {name: admin_rows(db, sql) for name, sql in ROWS_SQL.items()}


def _describe(label: str, fingerprint: dict[str, tuple[int, str]]) -> str:
    lines = [f"{table}: filas={count} md5={digest}" for table, (count, digest) in fingerprint.items()]
    return f"{label}\n" + "\n".join(lines)


def test_reloading_three_times_changes_nothing(db, tmp_path: Path) -> None:
    write_integration_fixture(tmp_path)
    first = load_directory(db, tmp_path)
    assert first.summary.new_event == FIXTURE_VALID and first.verify.ok is True
    baseline_rows = _rows(db)
    evidence.record_text(EVIDENCE_NAME, _describe("Carga 1 (huella ANTES de recargar)", first.fingerprint),
                         "carga 1")
    for number in range(2, RELOADS + 2):
        again = load_directory(db, tmp_path)
        summary = again.summary
        assert (summary.new_event, summary.newer_version) == (0, 0)
        assert summary.unchanged == FIXTURE_VALID and summary.quarantined == FIXTURE_QUARANTINED
        assert summary.unique == FIXTURE_UNIQUE and again.verify.ok is True
        assert again.fingerprint == first.fingerprint
        assert _rows(db) == baseline_rows
        evidence.record_text(EVIDENCE_NAME, _describe(f"Carga {number} (huella DESPUÉS: idéntica a la carga 1; "
                                                      "resumen new=0 newer=0)", again.fingerprint), f"carga {number}")
