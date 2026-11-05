"""Pruebas de la descarga anual con USGS simulado (T007, B13-B15)."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from historical.download import CountMismatchError, download_year
from historical.fetch_interval import FetchTools, IntervalFetchError
from historical.intervals import month_intervals
from historical.manifest import read_manifest, sha256_of, verify_file
from producer.usgs_client import FeedFetchError
from tests.support.fake_usgs_query import BASE_URL, FakeUsgs, make_event

UTC = timezone.utc
NOW = datetime(2026, 11, 5, 10, 0, 0, tzinfo=UTC)
EVENTS_PER_MONTH = 3
TOTAL_EVENTS = 12 * EVENTS_PER_MONTH


def year_events() -> list[dict]:
    """Tres eventos sintéticos por mes."""
    events = []
    for index, interval in enumerate(month_intervals(2025)):
        for offset in range(EVENTS_PER_MONTH):
            events.append(make_event(index * 10 + offset, interval.start.replace(day=2 + offset)))
    return events


def make_tools(fake) -> FetchTools:
    """Herramientas de descarga sobre el doble, sin dormir."""
    async def no_sleep(seconds: float) -> None:
        return None

    return FetchTools(fetch=fake.fetch, base_url=BASE_URL, sleep=no_sleep, jitter=lambda: 0.5, now=lambda: NOW)


def test_download_year_writes_twelve_files_and_manifest(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events())
    manifest = asyncio.run(download_year(tmp_path, make_tools(fake)))
    assert len(list(tmp_path.glob("usgs_2025-*.geojson"))) == 12
    assert read_manifest(tmp_path) == manifest
    assert manifest.totals.unique == manifest.totals.usgs_count_year == TOTAL_EVENTS
    for record in manifest.files:
        verify_file(tmp_path, record)
        assert record.sha256 == sha256_of((tmp_path / record.name).read_bytes())
        assert record.records == sum(query.records for query in record.queries)
        assert record.extracted_at == "2026-11-05T10:00:00Z"


def test_boundary_duplicate_is_counted_once(tmp_path: Path) -> None:
    """Un id aparece en enero y en febrero (frontera); el count anual cuenta ids únicos."""
    events = year_events()
    border = make_event(0, datetime(2025, 2, 3, tzinfo=UTC), updated=2_000)
    border["id"] = events[0]["id"]
    fake = FakeUsgs(events + [border], year_count=TOTAL_EVENTS)
    manifest = asyncio.run(download_year(tmp_path, make_tools(fake)))
    assert manifest.totals.duplicates_discarded == 1
    assert manifest.totals.records == TOTAL_EVENTS + 1
    assert manifest.totals.unique == manifest.totals.usgs_count_year == TOTAL_EVENTS


def test_unique_total_different_from_annual_count_raises(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events(), year_count=TOTAL_EVENTS + 7)
    with pytest.raises(CountMismatchError, match=r"43.*36|36.*43"):
        asyncio.run(download_year(tmp_path, make_tools(fake)))


def test_second_run_makes_no_requests_and_force_asks_again(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events())
    first = asyncio.run(download_year(tmp_path, make_tools(fake)))
    fake.urls.clear()
    second = asyncio.run(download_year(tmp_path, make_tools(fake)))
    assert fake.request_count == 0
    assert second == first
    asyncio.run(download_year(tmp_path, make_tools(fake), force=True))
    assert fake.request_count > 0


def test_altered_file_is_downloaded_again(tmp_path: Path) -> None:
    fake = FakeUsgs(year_events())
    asyncio.run(download_year(tmp_path, make_tools(fake)))
    fake.urls.clear()
    (tmp_path / "usgs_2025-04.geojson").write_bytes(b"{}")
    asyncio.run(download_year(tmp_path, make_tools(fake)))
    month_urls = [url for url in fake.urls if "endtime=2026" not in url]
    assert len(month_urls) == 2
    assert all("starttime=2025-04" in url for url in month_urls)


class FailingMonthFake(FakeUsgs):
    """Falla siempre en el mes de marzo mientras `broken` sea verdadero."""

    broken = True

    async def fetch(self, url: str) -> bytes:
        if self.broken and "starttime=2025-03" in url:
            raise FeedFetchError(503, "HTTP 503", 1)
        return await super().fetch(url)


def test_failed_month_keeps_previous_and_resumes(tmp_path: Path) -> None:
    fake = FailingMonthFake(year_events())
    with pytest.raises(IntervalFetchError, match="2025-03-01"):
        asyncio.run(download_year(tmp_path, make_tools(fake)))
    partial = read_manifest(tmp_path)
    assert [record.name for record in partial.files] == ["usgs_2025-01.geojson", "usgs_2025-02.geojson"]
    fake.broken = False
    fake.urls.clear()
    manifest = asyncio.run(download_year(tmp_path, make_tools(fake)))
    assert len(manifest.files) == 12
    month_urls = [url for url in fake.urls if "endtime=2026" not in url]
    assert not any("starttime=2025-01" in url or "starttime=2025-02" in url for url in month_urls)
