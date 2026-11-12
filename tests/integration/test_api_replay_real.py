"""API con el replay completo procesado: 22 eventos en `replay` y nada en `live` (T049; F12, J7, FR-015).

Los 20 eventos reales son de `data/historical/` (zona `chile-norte`); los 2 sintéticos son
`synthetic-replay-e1/e2`. Los 26 mensajes pasan por el consumidor real, como en T048.
"""
import asyncio

from tests.support.api_client import api_client
from tests.support.replay_harness import SYNTHETIC_PREFIX, build_replay_messages, process_messages

RANGE_2025 = {"start": "2025-01-01", "end": "2026-01-01"}
EVENTS = "/api/eventos"
STATS = "/api/estadisticas"


async def _load(db, with_replay: bool):
    """Procesa los 26 mensajes (si se pide) y devuelve los mensajes originales."""
    messages = build_replay_messages()
    if with_replay:
        consumer = await db.consumer()
        try:
            await process_messages(consumer, messages)
        finally:
            await consumer.close()
    return messages


def _call(db, requests: dict[str, tuple[str, dict]], with_replay: bool = True):
    """Carga los datos y hace cada petición; devuelve mensajes y respuestas por nombre."""
    async def scenario():
        messages = await _load(db, with_replay)
        async with api_client(db) as client:
            return messages, {name: await client.get(path, params=params)
                              for name, (path, params) in requests.items()}

    return asyncio.run(scenario())


def test_replay_mode_returns_22_events_with_original_times_and_synthetic_flags(db):
    messages, responses = _call(db, {"r": (EVENTS, {**RANGE_2025, "mode": "replay"})})
    body = responses["r"].json()
    assert responses["r"].status_code == 200
    assert body["metadata"]["mode"] == "replay" and body["metadata"]["total"] == 22
    features = {f["id"]: f["properties"] for f in body["features"]}
    assert len(features) == 22
    real_times = {m["event"]["id"]: m["event"]["properties"]["time"] for m in messages if not m["is_synthetic"]}
    assert len(real_times) == 20
    for event_id, time_ms in real_times.items():
        assert features[event_id]["time"] == time_ms and features[event_id]["is_synthetic"] is False
    synthetic = {event_id for event_id, props in features.items() if props["is_synthetic"]}
    assert synthetic == {event_id for event_id in features if event_id.startswith(SYNTHETIC_PREFIX)}
    assert len(synthetic) == 2


def test_without_mode_or_with_live_no_replay_event_appears(db):
    _, responses = _call(db, {"default": (EVENTS, RANGE_2025), "live": (EVENTS, {**RANGE_2025, "mode": "live"})})
    for response in responses.values():
        body = response.json()
        assert response.status_code == 200 and body["metadata"]["mode"] == "live"
        assert body["features"] == [] and body["metadata"]["total"] == 0


def test_replay_statistics_have_null_comparison_and_the_same_total(db):
    _, responses = _call(db, {"s": (STATS, {**RANGE_2025, "mode": "replay"})})
    body = responses["s"].json()
    assert responses["s"].status_code == 200
    assert body["metadata"]["mode"] == "replay" and body["total"] == 22 and body["comparison"] is None


def test_empty_replay_schema_returns_an_empty_list_not_an_error(db):
    _, responses = _call(db, {"e": (EVENTS, {**RANGE_2025, "mode": "replay"}),
                              "s": (STATS, {**RANGE_2025, "mode": "replay"})}, with_replay=False)
    assert responses["e"].status_code == 200 and responses["e"].json()["features"] == []
    assert responses["s"].status_code == 200 and responses["s"].json()["total"] == 0
