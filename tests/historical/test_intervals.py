"""Pruebas de los intervalos de consulta y de la URL (T001, B13). Sin red."""
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from historical.intervals import Interval, build_query_url, month_intervals, split_interval

BASE = "https://example.invalid/fdsnws/event/1"


def test_month_intervals_are_twelve_contiguous_utc() -> None:
    intervals = month_intervals(2025)
    assert len(intervals) == 12
    assert intervals[0].start == datetime(2025, 1, 1, tzinfo=timezone.utc)
    for previous, following in zip(intervals, intervals[1:]):
        assert previous.end == following.start
    assert intervals[-1].end == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_split_interval_gives_two_contiguous_halves() -> None:
    original = Interval(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc))
    first, second = split_interval(original)
    assert first.start == original.start
    assert first.end == second.start
    assert second.end == original.end
    assert original.start < first.end < original.end


def test_build_query_url_has_contract_parameters() -> None:
    interval = Interval(datetime(2025, 3, 1, tzinfo=timezone.utc), datetime(2025, 4, 1, tzinfo=timezone.utc))
    url = build_query_url(interval, BASE, "query")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    assert parsed.path.endswith("/query")
    assert params["minmagnitude"] == ["4"]
    assert params["eventtype"] == ["earthquake"]
    assert params["orderby"] == ["time-asc"]
    assert params["format"] == ["geojson"]
    assert params["starttime"] == ["2025-03-01T00:00:00"]
    assert params["endtime"] == ["2025-04-01T00:00:00"]


def test_build_query_url_count_kind() -> None:
    interval = Interval(datetime(2025, 3, 1, tzinfo=timezone.utc), datetime(2025, 4, 1, tzinfo=timezone.utc))
    url = build_query_url(interval, BASE, "count")
    assert urlparse(url).path.endswith("/count")


def test_build_query_url_keeps_milliseconds_for_short_intervals() -> None:
    start = datetime(2025, 3, 1, 0, 0, 0, 125000, tzinfo=timezone.utc)
    interval = Interval(start, datetime(2025, 3, 1, 0, 0, 0, 126000, tzinfo=timezone.utc))
    params = parse_qs(urlparse(build_query_url(interval, BASE, "query")).query)
    assert params["starttime"] == ["2025-03-01T00:00:00.125"]
    assert params["endtime"] == ["2025-03-01T00:00:00.126"]


def test_split_interval_rounds_to_milliseconds() -> None:
    start = datetime(2025, 3, 1, tzinfo=timezone.utc)
    first, second = split_interval(Interval(start, datetime(2025, 3, 1, 0, 0, 0, 3000, tzinfo=timezone.utc)))
    assert first.end == second.start
    assert first.end.microsecond % 1000 == 0
