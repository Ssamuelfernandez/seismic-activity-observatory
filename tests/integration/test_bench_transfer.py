"""Transferencia medida contra la API real del stack, por nombre de servicio (T085, K6, FR-020)."""
from scripts.benchmarks.transfer import API_BASE, bytes_per_visit, measure_routes, render_transfer_md


def test_four_routes_measured_through_api_service_name_with_positive_bytes() -> None:
    routes = measure_routes()
    assert API_BASE == "http://api:8000" and len(routes) == 4
    assert all(r.status == 200 and r.body_bytes > 0 for r in routes)
    assert {r.path.split("?")[0] for r in routes} == {"/api/eventos", "/api/estadisticas", "/api/salud"}
    text = render_transfer_md(routes)
    assert "no calculable" in text and str(bytes_per_visit(routes)) in text
