"""Pruebas del mensaje del replay y del bloque controlado (T041). Sin Docker."""
from datetime import datetime, timezone

from common.replay_message import MODE_REPLAY, SOURCE_REPLAY, ReplayItem, build_controlled_block, build_replay_message

START = datetime(2026, 11, 12, 9, 0, 0, tzinfo=timezone.utc)
REPLAY_AT = datetime(2026, 11, 12, 9, 0, 5, tzinfo=timezone.utc)
YEAR_2025_START_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
YEAR_2025_END_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def test_real_event_message_keeps_event_untouched():
    feature = {"id": "us1", "properties": {"time": 1735718880000, "updated": 1735719000000, "mag": 4.5}}
    item = ReplayItem(feature, False, datetime(2025, 2, 1, 3, 4, 5, tzinfo=timezone.utc))
    message = build_replay_message(item, REPLAY_AT)
    assert message["mode"] == MODE_REPLAY == "replay"
    assert message["source"] == SOURCE_REPLAY == "replay_demo"
    assert message["replay_at"] == "2026-11-12T09:00:05Z"
    assert message["ingested_at"] == "2025-02-01T03:04:05Z"
    assert message["is_synthetic"] is False
    assert message["event"] == feature
    assert message["event"]["properties"]["time"] == 1735718880000


def test_controlled_block_order_and_content():
    block = build_controlled_block(START)
    assert len(block) == 6
    ids = [item.feature["id"] for item in block]
    assert ids == ["synthetic-replay-e1"] * 4 + ["synthetic-replay-e2", "synthetic-replay-e1"]
    assert len(set(ids)) == 2
    updated = [item.feature["properties"]["updated"] for item in block]
    v1, v2, middle = updated[0], updated[2], updated[5]
    assert updated[1] == updated[3] == v1
    assert v1 < middle < v2
    assert all(item.is_synthetic for item in block)
    assert all(item.ingested_at == START for item in block)
    for item in block:
        assert YEAR_2025_START_MS <= item.feature["properties"]["time"] < YEAR_2025_END_MS
