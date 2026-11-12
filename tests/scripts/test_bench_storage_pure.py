"""Pruebas sin Docker del almacenamiento y la transferencia medidos (T084, T085)."""
from pathlib import Path

from scripts.benchmarks.labels import NOT_COMPUTABLE, UNAVAILABLE
from scripts.benchmarks.storage import (StorageReport, TableStorage, bytes_per_row, directory_size,
                                        render_storage_md)
from scripts.benchmarks.transfer import (API_BASE, ROUTES, RouteBytes, bytes_per_visit, monthly_bytes,
                                         render_transfer_md)


def test_bytes_per_row_is_size_over_rows_and_none_without_rows() -> None:
    assert bytes_per_row(8192, 4) == 2048 and bytes_per_row(10, 0) is None


def test_directory_size_sums_files_and_missing_is_none(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"x" * 10)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.bin").write_bytes(b"y" * 5)
    assert directory_size(tmp_path) == 15 and directory_size(tmp_path / "no_existe") is None


def test_storage_md_has_tables_schema_totals_and_docker_volume_unavailable() -> None:
    report = StorageReport([TableStorage("live", "t", 4, 8192, 4096, 2048.0)], 123456,
                           {"data/historical": 100, "data/catalogo": None})
    text = render_storage_md(report, [{"rows": 10, "heap_bytes": 8192, "total_bytes": 16384, "indexes": {"ix": 8192}}])
    assert "| live | t | 4 | 8192 | 4096 | 2,048.0 |" in text and "| live | 8192 |" in text
    assert UNAVAILABLE in text and "SINTÉTICO" in text and "123456" in text


def test_transfer_uses_service_name_never_localhost_and_monthly_needs_visits() -> None:
    assert API_BASE == "http://api:8000" and all("localhost" not in path for _, path in ROUTES)
    routes = [RouteBytes(label, path, 200, 100 * (i + 1)) for i, (label, path) in enumerate(ROUTES)]
    assert bytes_per_visit(routes) == 100 + 300 + 400
    assert monthly_bytes(800, None) is None and monthly_bytes(800, 10) == 8000
    text = render_transfer_md(routes)
    assert NOT_COMPUTABLE in text and "PENDIENTE (alumno)" in text and "| 4 |" not in text
    assert UNAVAILABLE in render_transfer_md(None)
