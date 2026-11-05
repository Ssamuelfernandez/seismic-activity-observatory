"""Pruebas de api/params.py y api/timeutil.py: validación de parámetros (F3, F4, F5, FR-004)."""
import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest

from api.cursor import CursorPosition, encode_cursor
from api.errors import ApiError
from api.params import PageRequest, QueryFilters, parse_filters, parse_page
from api.timeutil import ms_to_datetime, parse_iso_to_ms

NOW_MS = 1793543640000
DAY_MS = 24 * 3_600_000
MAX_EVENTS = 5000


def utc_ms(*args: int, **kwargs: int) -> int:
    return int(datetime(*args, tzinfo=timezone.utc, **kwargs).timestamp() * 1000)


def raw(*pairs: tuple[str, str]) -> list[tuple[str, str]]:
    return list(pairs)


def filters(*pairs: tuple[str, str]) -> QueryFilters:
    return parse_filters(raw(*pairs), NOW_MS)


def invalid_param(call, name: str) -> ApiError:
    with pytest.raises(ApiError) as caught:
        call()
    assert caught.value.status == 400
    assert caught.value.code == "invalid_parameter"
    assert f"'{name}'" in caught.value.message
    return caught.value


# --- rango ---

def test_no_params_means_last_24_hours():
    result = filters()
    assert result == QueryFilters(NOW_MS - DAY_MS, NOW_MS, None, None, "live")


def test_only_start_ends_now():
    result = filters(("start", "2026-11-01T00:00:00Z"))
    assert result.start_ms == utc_ms(2026, 11, 1)
    assert result.end_ms == NOW_MS


def test_only_end_starts_24_hours_before():
    result = filters(("end", "2026-11-01T12:00:00Z"))
    assert result.end_ms == utc_ms(2026, 11, 1, 12)
    assert result.start_ms == result.end_ms - DAY_MS


def test_date_only_is_midnight_utc():
    result = filters(("start", "2025-03-01"), ("end", "2025-03-02"))
    assert result.start_ms == utc_ms(2025, 3, 1)
    assert result.end_ms == utc_ms(2025, 3, 2)


def test_no_timezone_is_utc_and_zone_is_converted():
    assert parse_iso_to_ms("2025-03-01T10:00:00") == utc_ms(2025, 3, 1, 10)
    assert parse_iso_to_ms("2025-03-01T10:00:00+02:00") == utc_ms(2025, 3, 1, 8)
    assert parse_iso_to_ms("2025-03-01T10:00:00.123Z") == utc_ms(2025, 3, 1, 10) + 123


def test_ms_round_trip_is_exact():
    ms = 1793536750750
    assert parse_iso_to_ms(ms_to_datetime(ms).isoformat()) == ms


@pytest.mark.parametrize("start,end", [
    ("2025-03-02", "2025-03-01"),
    ("2025-03-01", "2025-03-01"),
])
def test_start_not_before_end_is_error(start, end):
    invalid_param(lambda: filters(("start", start), ("end", end)), "start")


def test_only_start_in_the_future_is_error():
    invalid_param(lambda: filters(("start", "2030-01-01")), "start")


@pytest.mark.parametrize("name,value", [("start", "ayer"), ("end", "2025-13-45"), ("start", "")])
def test_bad_dates_name_the_parameter(name, value):
    invalid_param(lambda: filters((name, value)), name)


# --- min_mag ---

@pytest.mark.parametrize("text,expected", [("4.5", 4.5), ("0", 0.0), ("-0.06", -0.06), ("-2", -2.0)])
def test_valid_min_mag(text, expected):
    assert filters(("min_mag", text)).min_mag == expected


@pytest.mark.parametrize("text", ["abc", "nan", "NaN", "inf", "-inf", "Infinity", "", "1e999"])
def test_invalid_min_mag(text):
    invalid_param(lambda: filters(("min_mag", text)), "min_mag")


# --- country_id ---

@pytest.mark.parametrize("text,expected", [
    ("esp", "ESP"), ("ESP", "ESP"), ("none", "none"), ("NONE", "none"), ("None", "none"),
])
def test_valid_country_id(text, expected):
    assert filters(("country_id", text)).country_id == expected


@pytest.mark.parametrize("text", ["ES", "E1A", "ESPA", "", "ñññ"])
def test_invalid_country_id(text):
    invalid_param(lambda: filters(("country_id", text)), "country_id")


# --- mode ---

@pytest.mark.parametrize("text", ["live", "replay"])
def test_valid_mode(text):
    assert filters(("mode", text)).mode == text


@pytest.mark.parametrize("text", ["otro", "LIVE", ""])
def test_invalid_mode(text):
    invalid_param(lambda: filters(("mode", text)), "mode")


# --- repetidos y desconocidos ---

def test_repeated_known_parameter_is_error():
    invalid_param(lambda: filters(("min_mag", "1"), ("min_mag", "2")), "min_mag")


def test_unknown_parameter_is_ignored():
    assert filters(("foo", "bar"), ("foo", "baz")) == filters()


def test_filters_ignore_page_parameters():
    assert filters(("limit", "0"), ("cursor", "xx")) == filters()


# --- limit y cursor ---

def page(*pairs: tuple[str, str]) -> PageRequest:
    return parse_page(raw(*pairs), MAX_EVENTS)


def test_default_page():
    assert page() == PageRequest(limit=MAX_EVENTS, cursor=None)


@pytest.mark.parametrize("text", ["1", "10", str(MAX_EVENTS)])
def test_valid_limit(text):
    assert page(("limit", text)).limit == int(text)


@pytest.mark.parametrize("text", ["0", "-1", "1.5", "abc", "", str(MAX_EVENTS + 1)])
def test_invalid_limit(text):
    invalid_param(lambda: page(("limit", text)), "limit")


def test_repeated_limit_is_error():
    invalid_param(lambda: page(("limit", "1"), ("limit", "2")), "limit")


def test_valid_cursor_is_decoded():
    position = CursorPosition(1793536750750, "synthetic-1")
    assert page(("cursor", encode_cursor(position))).cursor == position


def test_bad_cursor_is_invalid_cursor():
    with pytest.raises(ApiError) as caught:
        page(("cursor", "xx"))
    assert caught.value.code == "invalid_cursor"


def test_page_ignores_filter_parameters():
    assert page(("min_mag", "abc")) == page()


# --- pureza ---

@pytest.mark.parametrize("module", ["params", "timeutil", "cursor"])
def test_pure_modules_do_not_import_fastapi_or_asyncpg(module):
    source = (Path(__file__).resolve().parents[2] / "api" / f"{module}.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"fastapi", "asyncpg", "starlette"}
