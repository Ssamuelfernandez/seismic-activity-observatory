"""Pruebas sin Docker del escenario `geo` de `scripts/verify_consumer.py` (T021)."""
from scripts.consumer_scenarios import geo
from scripts.consumer_scenarios.helpers import GEO_EVIDENCE_DIR, evidence_path
from scripts.verify_consumer import SCENARIOS


def test_catalog_load_results_reads_each_start_in_order() -> None:
    log = ("INFO catalog loaded total=177 inserted=177 updated=0\nINFO otra línea\n"
           "INFO catalog loaded total=177 inserted=0 updated=0\n")
    assert geo.catalog_load_results(log) == [(177, 177, 0), (177, 0, 0)]
    assert geo.catalog_load_results("sin línea") == []


def test_geo_is_registered_and_writes_to_geografia_pais() -> None:
    assert SCENARIOS["geo"] is geo.run
    assert evidence_path("geografia_catalogo", "out", GEO_EVIDENCE_DIR).parent.name == "geografia-pais"
    assert evidence_path("x", "out").parent.name == "consumidor-idempotente"
