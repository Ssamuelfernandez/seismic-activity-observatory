"""Pruebas de la CLI de descarga con USGS simulado (T009, B13, B15, B17)."""
import subprocess
import sys
from pathlib import Path

import pytest

from historical.download_main import main
from historical.manifest import read_manifest
from tests.historical.test_download import TOTAL_EVENTS, make_tools, year_events
from tests.support.fake_usgs_query import FakeUsgs


def test_start_without_end_exits_with_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--output-dir", str(tmp_path), "--start", "2025-12-30T00:00:00"])
    assert raised.value.code != 0


def test_invalid_date_exits_with_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--output-dir", str(tmp_path), "--start", "ayer", "--end", "hoy"])
    assert raised.value.code != 0


def test_year_download_leaves_files_in_output_dir(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events())
    assert main(["--output-dir", str(tmp_path)], tools=make_tools(fake)) == 0
    assert len(list(tmp_path.glob("usgs_2025-*.geojson"))) == 12
    assert read_manifest(tmp_path).totals.unique == TOTAL_EVENTS


def test_count_mismatch_returns_nonzero_exit_code(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events(), year_count=TOTAL_EVENTS + 1)
    assert main(["--output-dir", str(tmp_path)], tools=make_tools(fake)) != 0


def test_gap_options_download_gap_file(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events())
    args = ["--output-dir", str(tmp_path), "--start", "2025-12-30T00:00:00", "--end", "2025-12-31T00:00:00"]
    assert main(args, tools=make_tools(fake)) == 0
    assert len(read_manifest(tmp_path).gaps) == 1


def test_help_lists_the_options() -> None:
    result = subprocess.run([sys.executable, "-m", "historical.download_main", "--help"],
                            capture_output=True, text=True, check=True)
    for option in ("--force", "--start", "--end", "--output-dir"):
        assert option in result.stdout
