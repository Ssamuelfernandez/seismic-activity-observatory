"""Pruebas sin Docker de los costes de K6 (T086): 6 categorías, sin valores inventados."""
from dataclasses import replace

from scripts.benchmarks.costs import (ASSUMED, CATEGORIES, FREE_QUOTA_NOTE, MEASURED, CostRow,
                                      build_rows, render_costs_md)
from scripts.benchmarks.labels import NOT_COMPUTABLE, PENDING_STUDENT


def _filled(row: CostRow, values: dict[str, float]) -> CostRow:
    """Copia de la fila con entradas de EJEMPLO (solo de la prueba), conservando origen y unidad."""
    inputs = {name: replace(entry, value=values.get(name, entry.value)) for name, entry in row.inputs.items()}
    return replace(row, inputs=inputs)


def test_exactly_six_categories_each_with_label_and_formula() -> None:
    rows = build_rows(1_000_000, 2_000)
    assert tuple(r.category for r in rows) == CATEGORIES and len(rows) == 6
    assert all(r.label in (MEASURED, ASSUMED) and r.formula.strip() for r in rows)


def test_without_filled_inputs_every_result_is_not_computable_never_zero() -> None:
    rows = build_rows(1_000_000, 2_000)
    assert all(r.result() is None for r in rows)
    text = render_costs_md(rows)
    assert text.count(NOT_COMPUTABLE) >= 6 and PENDING_STUDENT in text


def test_only_measured_values_are_filled_by_default() -> None:
    rows = {r.category: r for r in build_rows(2 * 1024 ** 3, 1024 ** 2)}
    assert rows["almacenamiento"].inputs["gib"].value == 2.0 and rows["almacenamiento"].inputs["gib"].origin == MEASURED
    assert rows["transferencia"].inputs["gib_visita"].origin == MEASURED
    assert rows["almacenamiento"].label == ASSUMED and rows["hardware"].label == ASSUMED
    assert all(repr(e.value) == "PENDING" for e in rows["hardware"].inputs.values())


def test_with_example_inputs_the_result_matches_the_formula() -> None:
    rows = {r.category: r for r in build_rows(2 * 1024 ** 3, 1024 ** 3)}
    assert _filled(rows["hardware"], {"precio": 1200, "vida_util": 48, "fraccion": 0.5}).result() == 1200 / 48 * 0.5
    assert _filled(rows["electricidad"], {"potencia": 100, "horas": 720, "tarifa": 0.2}).result() == 100 / 1000 * 720 * 0.2
    assert _filled(rows["almacenamiento"], {"tarifa": 0.1}).result() == 2.0 * 0.1
    assert _filled(rows["transferencia"], {"visitas": 1000, "tarifa": 0.05}).result() == 1.0 * 1000 * 0.05
    assert _filled(rows["mantenimiento"], {"horas": 4, "tarifa": 30}).result() == 120
    assert _filled(rows["horas de desarrollo"], {"horas": 100, "tarifa": 20}).result() == 2000


def test_free_quota_rows_say_free_is_not_zero_cost_and_are_pending() -> None:
    text = render_costs_md(build_rows())
    assert "cuota gratuita ≠ coste cero" in FREE_QUOTA_NOTE and FREE_QUOTA_NOTE in text
    assert "Fecha de consulta" in text and "Netlify" in text and "Cloudflare" in text
