"""Pruebas de api/sql_filters.py: WHERE parametrizado y esquema por lista cerrada (F3, F10, FR-014)."""
import re
from decimal import Decimal

import pytest

from api.cursor import CursorPosition
from api.sql_filters import build_where, current_event_table
from api.timeutil import ms_to_datetime
from api.params import QueryFilters

START_MS, END_MS = 1_000_000_000_000, 1_000_086_400_000


def _filters(**overrides) -> QueryFilters:
    values = {"start_ms": START_MS, "end_ms": END_MS, "min_mag": None, "country_id": None, "mode": "live"}
    values.update(overrides)
    return QueryFilters(**values)


def test_only_range_by_default():
    where, params = build_where(_filters(), None)
    assert params == [ms_to_datetime(START_MS), ms_to_datetime(END_MS)]
    assert where == "e.event_time >= $1 AND e.event_time < $2"


def test_min_mag_country_and_cursor_add_parameters_in_order():
    where, params = build_where(_filters(min_mag=4.5, country_id="ESP"), CursorPosition(1_000_000_500_000, "a"))
    assert params == [ms_to_datetime(START_MS), ms_to_datetime(END_MS), Decimal("4.5"), "ESP",
                      ms_to_datetime(1_000_000_500_000), "a"]
    assert "e.mag >= $3" in where and "e.country_id = $4" in where
    assert "(e.event_time, e.event_id) < ($5, $6)" in where
    assert sorted(set(re.findall(r"\$(\d+)", where)), key=int) == ["1", "2", "3", "4", "5", "6"]


def test_none_country_uses_is_null_without_parameter():
    where, params = build_where(_filters(country_id="none"), None)
    assert "e.country_id IS NULL" in where
    assert len(params) == 2


def test_without_min_mag_can_be_skipped():
    where, params = build_where(_filters(min_mag=2.0, country_id="ESP"), None, with_min_mag=False)
    assert "mag" not in where
    assert len(params) == 3 and params[2] == "ESP"
    assert "e.country_id = $3" in where


def test_no_stray_conditions_without_optional_filters():
    where, _ = build_where(_filters(), None)
    assert "mag" not in where and "country" not in where and "<" in where
    assert where.count("AND") == 1


@pytest.mark.parametrize("hostile", ["x'; DROP TABLE live.current_event; --", 'a"b', "ESP' OR '1'='1"])
def test_client_values_never_appear_in_sql(hostile):
    where, params = build_where(_filters(country_id=hostile), CursorPosition(5, hostile))
    assert hostile not in where
    assert "'" not in where and '"' not in where
    assert params.count(hostile) == 2


def test_schema_comes_from_closed_list():
    assert current_event_table("live") == "live.current_event"
    assert current_event_table("replay") == "replay.current_event"


def test_unknown_mode_is_rejected():
    with pytest.raises(KeyError):
        current_event_table("public; DROP TABLE x")
