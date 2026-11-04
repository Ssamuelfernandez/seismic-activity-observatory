"""Los contadores de C8 coinciden con SQL en los tres casos de FR-036 (T060, SC-009).

Bucle, `process_record` y `Counters` reales sobre la base temporal; una sesión de contadores por caso.
"""
import asyncio
import json

import pytest

from consumer.counters import Counters, check_identities, snapshot
from tests.support import evidence
from tests.support.loop_harness import ReplayConsumer, open_pool, run_session
from tests.support.messages import (
    E1_TIME_MS, E1_UPDATED_1005, FAQ12_E1, build_synthetic_message, faq12_sequence, to_bytes,
)
from tests.support.temp_database import TempDatabase

EVIDENCE_NAME = "bloque4_contadores_integracion"
QUARANTINE_BY_REASON = "SELECT reason, count(*) FROM live.quarantine GROUP BY reason ORDER BY reason"
TABLE_COUNTS = ("SELECT (SELECT count(*) FROM live.current_event), (SELECT count(*) FROM live.event_version), "
                "(SELECT count(*) FROM live.quarantine)")
DB_CONSTRAINT_VIOLATION = "db_constraint_violation"
LATITUDE_REASON = "coordinates_out_of_range"


def latitude_145() -> bytes:
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    message["event"]["geometry"]["coordinates"][1] = 145
    return to_bytes(message)


def dmin_nan() -> bytes:
    message = build_synthetic_message(FAQ12_E1, E1_TIME_MS, E1_UPDATED_1005, 4.2)
    message["event"]["properties"]["dmin"] = float("nan")
    return to_bytes(message)


FAQ12 = [to_bytes(m) for m in faq12_sequence()]
# nombre, mensajes, recibidos, conversiones, motivo de las cuarentenas y cuántas filas nuevas
CASES = [
    ("caso1_faq12", FAQ12, 5, 5, None, 0),
    ("caso2_faq12_latitud145_x2", FAQ12 + [latitude_145()] * 2, 7, 5, LATITUDE_REASON, 1),
    ("caso3_faq12_dmin_nan_x2", FAQ12 + [dmin_nan()] * 2, 7, 7, DB_CONSTRAINT_VIOLATION, 1),
]


def _evidence_text(data: dict, by_reason: dict, counts: tuple) -> str:
    """Contadores de la sesión junto a las cifras de SQL, para compararlos a simple vista."""
    counters_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return "\n".join([
        f"COUNTERS {counters_json}",
        f"SQL filas (current_event, event_version, quarantine): {counts}",
        f"SQL quarantine por motivo: {by_reason}",
    ])


async def _run_case(db: TempDatabase, raws: list[bytes], label: str) -> tuple[dict, dict, tuple]:
    counters = Counters()
    pool = await open_pool(db)
    try:
        await run_session(pool, ReplayConsumer(raws, 0, asyncio.Event()), counters)
    finally:
        await pool.close()
    admin = await db.admin()
    try:
        by_reason = {r["reason"]: r["count"] for r in await admin.fetch(QUARANTINE_BY_REASON)}
        counts = tuple(await admin.fetchrow(TABLE_COUNTS))
        evidence.record_text(EVIDENCE_NAME, _evidence_text(snapshot(counters), by_reason, counts), label=label)
        await evidence.record_query(admin, EVIDENCE_NAME, QUARANTINE_BY_REASON, label=f"{label}: cuarentena por motivo (SQL)")
    finally:
        await admin.close()
    return snapshot(counters), by_reason, counts


@pytest.mark.parametrize("label, raws, received, conversions, reason, new_rows", CASES, ids=[c[0] for c in CASES])
def test_counters_match_sql_and_satisfy_the_identities(db: TempDatabase, label, raws, received, conversions,
                                                       reason, new_rows):
    data, by_reason, counts = asyncio.run(_run_case(db, raws, label))
    assert data["received"] == received and data["ms_to_utc_conversions"] == conversions
    assert check_identities(data) == []
    assert (data["new_events"], data["newer_versions_applied"], data["redeliveries_ignored"]) == (2, 1, 2)
    assert counts == (2, 3, new_rows), "tablas: current_event, event_version, quarantine"
    assert data["quarantined"] == by_reason
    attempts = received - 5
    assert data["quarantined"].get(reason, 0) == new_rows
    assert data["quarantine_duplicates"].get(reason, 0) == attempts - by_reason.get(reason, 0)
