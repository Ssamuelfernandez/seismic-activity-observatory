"""Pruebas puente consumidor a API (feature 012, pruebas de aceptación 1, 3, 4, 5 y 7).

Cada prueba pasa mensajes SINTÉTICOS (`synthetic-acc-NN`, `is_synthetic = true`) por el consumidor
real (pipeline y localizador de países reales) en una `TempDatabase`, y comprueba a la vez el SQL y
las respuestas de `/api/eventos` y `/api/estadisticas`. Nunca se escribe en la base `live` real.
"""
import asyncio
import copy

from api.timeutil import MS_PER_HOUR
from tests.support.api_client import request_api
from tests.support.geo_harness import admin_rows, process_messages
from tests.support.messages import (
    ATLANTIC,
    E1_TIME_MS,
    E1_UPDATED_1005,
    MADRID,
    build_event,
    build_message,
)

EVENTS_PATH = "/api/eventos"
STATS_PATH = "/api/estadisticas"
RANGE = {"start": "2026-11-04", "end": "2026-11-05"}
UPDATE_STEP_MS = 60_000
LATER_TIME_MS = E1_TIME_MS + 4 * MS_PER_HOUR + 30 * 60_000  # 14:30 UTC, otra hora que 10:00
TOKYO = (139.69, 35.69)
VERSIONS_SQL = "SELECT event_id, updated_ms FROM live.event_version WHERE event_id = $1 ORDER BY updated_ms"
QUARANTINE_SQL = "SELECT count(*) FROM live.quarantine"


def _acc_message(number: int, lon: float, lat: float, *, mag: float | None = 3.0, time_ms: int = E1_TIME_MS,
                 updated_ms: int = E1_UPDATED_1005) -> dict:
    """Mensaje sintético `synthetic-acc-NN` (sobre del contrato) con coordenadas, magnitud y tiempos a medida."""
    event = build_event(f"synthetic-acc-{number:02d}", time_ms, updated_ms, mag)
    event["geometry"]["coordinates"] = [lon, lat, 10.0]
    return build_message(event)


def _version(message: dict, *, lon: float, lat: float, time_ms: int, updated_ms: int) -> dict:
    """Copia del mensaje con otras coordenadas, hora del evento y `updated` (otra versión del mismo evento)."""
    clone = copy.deepcopy(message)
    clone["event"]["geometry"]["coordinates"][:2] = [lon, lat]
    clone["event"]["properties"]["time"] = time_ms
    clone["event"]["properties"]["updated"] = updated_ms
    return clone


def _get(db, path: str, params: dict | None = None):
    """GET a la API con el rol real sobre lo que ya hay en la base (sin sembrar nada más)."""
    response = asyncio.run(request_api(db, path, params=params))
    assert response.status_code == 200
    return response.json()


def _features(db, params: dict | None = None) -> dict:
    """Features de `/api/eventos` del día de prueba indexadas por id."""
    body = _get(db, EVENTS_PATH, {**RANGE, **(params or {})})
    return {feature["id"]: feature for feature in body["features"]}


def _by_country(stats: dict) -> dict:
    """Recuento por país de `/api/estadisticas` (la clave `None` es «Sin país asignado»)."""
    return {item["country_id"]: item["count"] for item in stats["by_country"]["items"]}


def _by_hour(stats: dict) -> dict:
    """Recuento por hora UTC de `/api/estadisticas`, solo las horas con eventos."""
    return {bucket["hour_start"]: bucket["count"] for bucket in stats["by_hour"]["buckets"] if bucket["count"]}


def _hour_start(time_ms: int) -> int:
    """Inicio (ms) de la hora UTC que contiene `time_ms`."""
    return time_ms - time_ms % MS_PER_HOUR


def test_new_event_is_one_current_row_visible_in_api_and_stats(db) -> None:
    """Prueba 1: un evento nuevo deja 1 fila actual y se ve en la lista y en el total de estadísticas."""
    before = _get(db, STATS_PATH, RANGE)["total"]
    message = _acc_message(1, *MADRID)
    process_messages(db, [message])
    rows = admin_rows(db, "SELECT count(*) FROM live.current_event WHERE event_id = $1", "synthetic-acc-01")
    assert rows == [(1,)]
    features = _features(db)
    assert list(features) == ["synthetic-acc-01"]
    assert features["synthetic-acc-01"]["properties"]["is_synthetic"] is True
    assert _get(db, STATS_PATH, RANGE)["total"] == before + 1


def test_later_version_changes_current_and_aggregates(db) -> None:
    """Prueba 3: una versión posterior cambia país y hora en la API y en los recuentos, y se conservan ambas."""
    first = _acc_message(2, *MADRID, mag=3.0)
    process_messages(db, [first])
    stats_before = _get(db, STATS_PATH, RANGE)
    assert _by_country(stats_before) == {"ESP": 1}
    assert _by_hour(stats_before) == {_hour_start(E1_TIME_MS): 1}
    later = _version(first, lon=TOKYO[0], lat=TOKYO[1], time_ms=LATER_TIME_MS,
                     updated_ms=E1_UPDATED_1005 + UPDATE_STEP_MS)
    later["event"]["properties"]["mag"] = 4.5
    process_messages(db, [later], start_offset=1)
    properties = _features(db)["synthetic-acc-02"]["properties"]
    assert (properties["country_id"], properties["time"], properties["mag"]) == ("JPN", LATER_TIME_MS, 4.5)
    stats_after = _get(db, STATS_PATH, RANGE)
    assert stats_after["total"] == 1
    assert _by_country(stats_after) == {"JPN": 1}
    assert _by_hour(stats_after) == {_hour_start(LATER_TIME_MS): 1}
    versions = admin_rows(db, VERSIONS_SQL, "synthetic-acc-02")
    assert versions == [("synthetic-acc-02", E1_UPDATED_1005), ("synthetic-acc-02", E1_UPDATED_1005 + UPDATE_STEP_MS)]
    assert admin_rows(db, "SELECT count(*) FROM live.current_event") == [(1,)]


def test_late_older_version_keeps_current_and_api_unchanged(db) -> None:
    """Prueba 4: una versión tardía con `updated` menor no cambia la API ni las estadísticas; queda en el historial."""
    recent = _acc_message(3, *MADRID, mag=3.0, updated_ms=E1_UPDATED_1005 + UPDATE_STEP_MS)
    process_messages(db, [recent])
    events_before = _get(db, EVENTS_PATH, RANGE)["features"]
    stats_before = _get(db, STATS_PATH, RANGE)
    late = _version(recent, lon=TOKYO[0], lat=TOKYO[1], time_ms=LATER_TIME_MS, updated_ms=E1_UPDATED_1005)
    late["event"]["properties"]["mag"] = 6.0
    process_messages(db, [late], start_offset=1)
    events_after = _get(db, EVENTS_PATH, RANGE)["features"]
    stats_after = _get(db, STATS_PATH, RANGE)
    assert events_after == events_before
    for stats in (stats_before, stats_after):  # campos que dependen del reloj de la petición
        stats["metadata"].pop("generated")
        stats["comparison"].pop("recent_period")
    assert stats_after == stats_before
    assert admin_rows(db, VERSIONS_SQL, "synthetic-acc-03") == [
        ("synthetic-acc-03", E1_UPDATED_1005), ("synthetic-acc-03", E1_UPDATED_1005 + UPDATE_STEP_MS)]


def test_null_magnitude_stays_null_in_db_and_api(db) -> None:
    """Prueba 5: una magnitud nula sigue nula en SQL y en la API, nunca 0, y `min_mag=0` la cuenta como nula."""
    process_messages(db, [_acc_message(4, *MADRID, mag=None)])
    assert admin_rows(db, "SELECT count(*) FROM live.current_event WHERE mag IS NULL") == [(1,)]
    assert admin_rows(db, "SELECT count(*) FROM live.current_event WHERE mag = 0") == [(0,)]
    properties = _features(db)["synthetic-acc-04"]["properties"]
    assert properties["mag"] is None
    filtered = _get(db, EVENTS_PATH, {**RANGE, "min_mag": "0"})
    assert filtered["features"] == []
    assert (filtered["metadata"]["total"], filtered["metadata"]["null_mag_excluded"]) == (0, 1)
    stats = _get(db, STATS_PATH, RANGE)
    assert stats["histograms"]["magnitude"]["no_value"] == 1
    assert sum(bucket["count"] for bucket in stats["histograms"]["magnitude"]["bins"]) == 0


def test_sea_event_has_no_country_and_is_counted(db) -> None:
    """Prueba 7: un evento en el mar no tiene país ni va a cuarentena y entra en el total y en la hora."""
    process_messages(db, [_acc_message(5, *ATLANTIC)])
    assert admin_rows(db, "SELECT country_id FROM live.current_event") == [(None,)]
    assert admin_rows(db, QUARANTINE_SQL) == [(0,)]
    features = _features(db, {"country_id": "none"})
    assert list(features) == ["synthetic-acc-05"]
    assert features["synthetic-acc-05"]["properties"]["country_id"] is None
    stats = _get(db, STATS_PATH, RANGE)
    assert stats["total"] == 1
    assert _by_hour(stats) == {_hour_start(E1_TIME_MS): 1}
    assert _by_country(stats) == {None: 1}
