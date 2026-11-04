"""Contadores de transformaciones de C8: solo en memoria, una sesión (FR-023, FR-024, FR-036).

Nombres y significado: `specs/003-consumidor-idempotente/contracts/consumer-runtime.md` §3.
Se actualizan una vez por mensaje, después del commit del offset. La API no los lee (FR-024).
"""
from dataclasses import dataclass, field

from common.records import ProcessingResult, ResultKind, VersionOutcome

DB_CONSTRAINT_VIOLATION = "db_constraint_violation"
OUTCOME_COUNTER = {
    VersionOutcome.NEW_EVENT: "new_events",
    VersionOutcome.NEWER_VERSION: "newer_versions_applied",
    VersionOutcome.LATE_OLD_VERSION: "late_old_versions",
    VersionOutcome.REDELIVERY: "redeliveries_ignored",
    VersionOutcome.SAME_UPDATED_CONFLICT: "same_updated_conflicts",
}


@dataclass
class Counters:
    """Estado en memoria de la sesión: un entero por resultado y mapas por campo o por motivo."""

    received: int = 0
    new_events: int = 0
    newer_versions_applied: int = 0
    late_old_versions: int = 0
    redeliveries_ignored: int = 0
    same_updated_conflicts: int = 0
    ms_to_utc_conversions: int = 0
    nulls_kept: dict[str, int] = field(default_factory=dict)
    quarantined: dict[str, int] = field(default_factory=dict)
    quarantine_duplicates: dict[str, int] = field(default_factory=dict)


def _bump(mapping: dict[str, int], key: str) -> None:
    """Suma uno a `mapping[key]`, creándolo si hace falta."""
    mapping[key] = mapping.get(key, 0) + 1


def apply_result(counters: Counters, result: ProcessingResult) -> None:
    """Actualiza los contadores con el resultado de un mensaje ya confirmado.

    Qué hace:
        Suma `received`; el contador del resultado de la versión; la conversión si el mensaje
        se transformó; los nulos guardados (solo eventos); y, en cuarentena, la fila nueva
        (`quarantined`) o el duplicado (`quarantine_duplicates`) por motivo.
    Recibe:
        counters: estado a modificar; result: lo que devolvió `process_record`.
    Devuelve:
        Nada.
    Por qué existe:
        Registro de transformaciones para auditar el flujo (C8, FR-023); no es una estadística
        de la API (FR-024).
    """
    counters.received += 1
    if result.converted:
        counters.ms_to_utc_conversions += 1
    if result.kind is ResultKind.EVENT:
        name = OUTCOME_COUNTER[result.outcome]
        setattr(counters, name, getattr(counters, name) + 1)
        for null_field in result.nulls:
            _bump(counters.nulls_kept, null_field)
        return
    _bump(counters.quarantined if result.inserted else counters.quarantine_duplicates, result.reason)


def snapshot(counters: Counters) -> dict:
    """Copia los contadores a un diccionario nuevo con las claves ordenadas."""
    return {
        "late_old_versions": counters.late_old_versions,
        "ms_to_utc_conversions": counters.ms_to_utc_conversions,
        "new_events": counters.new_events,
        "newer_versions_applied": counters.newer_versions_applied,
        "nulls_kept": dict(sorted(counters.nulls_kept.items())),
        "quarantine_duplicates": dict(sorted(counters.quarantine_duplicates.items())),
        "quarantined": dict(sorted(counters.quarantined.items())),
        "received": counters.received,
        "redeliveries_ignored": counters.redeliveries_ignored,
        "same_updated_conflicts": counters.same_updated_conflicts,
    }


def _quarantine_totals(data: dict) -> tuple[int, int]:
    """Devuelve (V, D): cuarentenas de validación y de `db_constraint_violation` (nuevas + duplicadas)."""
    total = sum(data["quarantined"].values()) + sum(data["quarantine_duplicates"].values())
    db_violations = data["quarantined"].get(DB_CONSTRAINT_VIOLATION, 0) + \
        data["quarantine_duplicates"].get(DB_CONSTRAINT_VIOLATION, 0)
    return total - db_violations, db_violations


def check_identities(data: dict) -> list[str]:
    """Comprueba las identidades de FR-023 sobre un `snapshot`.

    Qué hace:
        1. `ms_to_utc_conversions = received - V` y 2. `ms_to_utc_conversions` = suma de los
        cinco resultados de versión + D, con V las cuarentenas de motivo distinto de
        `db_constraint_violation` y D las de ese motivo (nuevas + duplicadas).
    Recibe:
        data: diccionario devuelto por `snapshot` (o leído de la línea `COUNTERS`).
    Devuelve:
        Lista de identidades incumplidas (texto); vacía si todas se cumplen.
    Por qué existe:
        Permite a los tests y a `verify_consumer.py` detectar un contador manipulado o perdido
        (C8, FR-023, FR-036, SC-009).
    """
    validation, db_violations = _quarantine_totals(data)
    conversions = data["ms_to_utc_conversions"]
    outcomes = sum(data[name] for name in OUTCOME_COUNTER.values())
    failures = []
    if conversions != data["received"] - validation:
        failures.append(f"identidad 1: conversiones={conversions} != recibidos={data['received']} - validación={validation}")
    if conversions != outcomes + db_violations:
        failures.append(f"identidad 2: conversiones={conversions} != resultados={outcomes} + db_constraint_violation={db_violations}")
    return failures
