"""Pruebas de `scripts/geo_real_day.py` sin red, con un feed mínimo INVENTADO (SINTÉTICO, T019)."""
import json
from pathlib import Path

from scripts import geo_real_day

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "catalogo" / "paises.geojson"


def _feature(event_id: str, lon, lat) -> dict:
    return {"type": "Feature", "id": event_id, "properties": {"type": "earthquake", "title": "SINTÉTICO"},
            "geometry": {"type": "Point", "coordinates": [lon, lat, 10.0]}}


def _synthetic_feed() -> dict:
    return {"type": "FeatureCollection", "metadata": {"title": "SINTÉTICO"}, "features": [
        _feature("synthetic-madrid", -3.70, 40.42),
        _feature("synthetic-atlantico", -30.0, 35.0),
        _feature("synthetic-paris", 2.35, 48.85),
        {"type": "Feature", "id": "synthetic-linea", "properties": {},
         "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}},
    ]}


def test_summary_counts_with_without_and_skipped() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    summary = geo_real_day.summarize_day(_synthetic_feed(), catalog)
    assert (summary.total, summary.skipped, summary.with_country, summary.without_country) == (4, 1, 2, 1)
    assert dict(summary.by_country) == {"ESP": 1, "FRA": 1} and summary.unknown_codes == ()
    assert geo_real_day.format_summary(summary).endswith("resultado: sin error")


def test_main_prints_sin_error_and_exits_zero(tmp_path: Path, capsys) -> None:
    feed = tmp_path / "feed.geojson"
    feed.write_text(json.dumps(_synthetic_feed()), encoding="utf-8")
    assert geo_real_day.main([str(feed), "--catalog", str(CATALOG_PATH)]) == 0
    output = capsys.readouterr().out
    assert "con país: 2" in output and "sin país (country_id NULL): 1" in output and "sin error" in output
