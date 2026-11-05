"""Pruebas de la descarga de un hueco con `--start/--end` (T008, B12)."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from historical.download import download_gap, download_year
from historical.intervals import Interval
from historical.manifest import read_manifest, verify_file
from tests.historical.test_download import make_tools, year_events
from tests.support.fake_usgs_query import FakeUsgs, make_event

UTC = timezone.utc
GAP = Interval(datetime(2025, 12, 30, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
GAP_NAME = "usgs_gap_20251230T000000_20251231T000000.geojson"


def gap_event() -> dict:
    """Evento sintético dentro del hueco."""
    return make_event(900, datetime(2025, 12, 30, 5, tzinfo=UTC))


def test_gap_file_is_added_without_touching_year_totals(tmp_path: Path) -> None:
    events = year_events()
    before = asyncio.run(download_year(tmp_path, make_tools(FakeUsgs(events))))
    after = asyncio.run(download_gap(tmp_path, GAP, make_tools(FakeUsgs(events + [gap_event()]))))
    assert after.totals == before.totals
    assert after.files == before.files
    assert [record.name for record in after.gaps] == [GAP_NAME]
    assert after.gaps[0].records == after.gaps[0].queries[0].usgs_count
    verify_file(tmp_path, after.gaps[0])
    assert read_manifest(tmp_path) == after


def test_gap_without_previous_manifest_creates_one(tmp_path: Path) -> None:
    manifest = asyncio.run(download_gap(tmp_path, GAP, make_tools(FakeUsgs([gap_event()]))))
    assert manifest.files == [] and len(manifest.gaps) == 1


def test_gap_repeated_does_not_duplicate_entry(tmp_path: Path) -> None:
    fake = FakeUsgs([gap_event()])
    asyncio.run(download_gap(tmp_path, GAP, make_tools(fake)))
    manifest = asyncio.run(download_gap(tmp_path, GAP, make_tools(fake)))
    assert len(manifest.gaps) == 1


@pytest.mark.parametrize("end", [datetime(2025, 12, 30, tzinfo=UTC), datetime(2025, 12, 29, tzinfo=UTC)])
def test_gap_with_end_not_after_start_is_error(tmp_path: Path, end: datetime) -> None:
    with pytest.raises(ValueError, match="end"):
        asyncio.run(download_gap(tmp_path, Interval(GAP.start, end), make_tools(FakeUsgs([]))))
