"""Pruebas sin Docker de los informes (T087): unidades, N real, etiqueta SINTÉTICO y sin celdas vacías."""
import re

from scripts.benchmarks.records import Measurement
from scripts.benchmarks.report import (build_results_json, render_aislamiento_md, render_indices_md,
                                       render_tablas_md)
from scripts.benchmarks.verdicts import Verdict

PARAMS = {"sizes": [1000], "repeats": 3, "budget_seconds": 10}
EMPTY_CELL = re.compile(r"\|[ \t]*\|")


def _measurement(op: str = "search") -> Measurement:
    return Measurement(f"{op}.list.1000.first", op, "list", 1000, "first", [1.0, 2.0, 3.0], 3, 3, 2.0, 1.5, 2.5,
                       1.0, 1.0, 3.0)


def test_tablas_have_units_real_n_and_synthetic_label_without_empty_cells() -> None:
    text = render_tablas_md([_measurement("search"), _measurement("geo")], PARAMS)
    assert "SINTÉTICO" in text and "(ms)" in text and "(KiB)" in text and "3 (3)" in text
    assert "no aplica" in text and not EMPTY_CELL.search(text)


def test_results_json_carries_label_seed_and_each_sample() -> None:
    data = build_results_json(PARAMS, "2026-01-01T00:00:00+00:00", [_measurement()])
    assert data["etiqueta"] == "SINTETICO" and data["seed"] == 20251113
    assert data["measurements"][0]["samples_ms"] == [1.0, 2.0, 3.0]


def test_indices_md_cites_ids_and_marks_proposal() -> None:
    verdict = Verdict("ix_x", "q3", "mag4", "justificado", ("agg.q3_noindex.1000.mag4", "agg.q3_mag_index.1000.mag4"),
                      "baja la mediana", 0.1)
    text = render_indices_md(None, [verdict], [{"rows": 1000, "indexes": {"ix_x_s1000": 8192}}])
    assert "agg.q3_noindex.1000.mag4" in text and "PROPUESTA" in text and "SINTÉTICO" in text


def test_aislamiento_md_reports_violations_or_none() -> None:
    snap = {"bench_exists": False, "usgs_historical": 18302, "bench_rows_outside": {"live.current_event": 0}}
    assert "Violaciones: ninguna" in render_aislamiento_md(snap, snap, [])
    assert "sigue existiendo" in render_aislamiento_md(snap, snap, ["el esquema 'bench' sigue existiendo"])
