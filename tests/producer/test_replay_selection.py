"""Pruebas de la selección del replay (T042). Sin Docker."""
from datetime import datetime, timezone
from pathlib import Path

from producer.replay_selection import ZONES, select_events
from producer.replay_source import load_verified_features

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "historical"
CHILE = ZONES["chile-norte"]
EXTRACTED = "2026-11-05T10:00:00Z"


def make(event_id: str, time_ms: int, lon: float, lat: float) -> tuple[dict, str]:
    """Feature sintética de prueba."""
    feature = {"id": event_id, "properties": {"time": time_ms, "updated": time_ms}, "geometry": {"coordinates": [lon, lat, 10]}}
    return feature, EXTRACTED


def test_order_box_unique_and_count():
    pairs = [
        make("c", 300, -70, -20),
        make("a", 100, -70, -20),
        make("out", 150, 10, 10),
        make("b", 200, -70, -20),
        make("a", 100, -70, -20),
    ]
    selected = select_events(pairs, CHILE, 10)
    assert [feature["id"] for feature, _ in selected] == ["a", "b", "c"]
    assert len(select_events(pairs, CHILE, 2)) == 2


def test_tie_on_time_breaks_by_id():
    pairs = [make("z", 100, -70, -20), make("m", 100, -70, -20)]
    assert [f["id"] for f, _ in select_events(pairs, CHILE, 5)] == ["m", "z"]


def test_real_files_chile_20():
    selected = select_events(load_verified_features(DATA_DIR), CHILE, 20)
    assert len(selected) == 20
    ids = [feature["id"] for feature, _ in selected]
    assert len(set(ids)) == 20
    times = [feature["properties"]["time"] for feature, _ in selected]
    assert times == sorted(times)
    first = datetime.fromtimestamp(times[0] / 1000, tz=timezone.utc)
    last = datetime.fromtimestamp(times[-1] / 1000, tz=timezone.utc)
    assert first.strftime("%Y-%m-%d %H:%M") == "2025-01-01 08:08"
    assert last.strftime("%Y-%m-%d %H:%M") == "2025-01-29 03:44"
    assert all(feature["properties"]["mag"] >= 4 for feature, _ in selected)
