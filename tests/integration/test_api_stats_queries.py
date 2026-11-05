"""Consultas de estadísticas con el rol real frente a cuentas SQL directas como administrador (T013)."""
import asyncio

from api.db_access import read_transaction
from api.params import QueryFilters
from api.stats_builder import DEPTH_THRESHOLDS, MAGNITUDE_THRESHOLDS
from api.stats_queries import fetch_country_counts, fetch_histogram, fetch_hour_counts
from tests.support.api_client import seed_database
from tests.support.api_seed import BASE_TIME_MS, synthetic_event
from tests.support.temp_database import TempDatabase

HOUR = 3_600_000
START = BASE_TIME_MS - BASE_TIME_MS % HOUR
END = START + 3 * HOUR
TIMEOUT_SECONDS = 5
COUNTRIES = {"ESP": "España", "JPN": "Japón"}

# Tramos calculados con CASE (independientes de width_bucket): mismo criterio, inferior inclusivo.
MAG_CASE = ("CASE WHEN mag IS NULL THEN NULL WHEN mag < 1 THEN 0 WHEN mag < 2 THEN 1 WHEN mag < 3 THEN 2 "
            "WHEN mag < 4 THEN 3 WHEN mag < 5 THEN 4 WHEN mag < 6 THEN 5 WHEN mag < 7 THEN 6 ELSE 7 END")
DEPTH_CASE = ("CASE WHEN depth_km IS NULL THEN NULL WHEN depth_km < 10 THEN 0 WHEN depth_km < 35 THEN 1 "
              "WHEN depth_km < 70 THEN 2 WHEN depth_km < 300 THEN 3 ELSE 4 END")


def _events():
    return [
        synthetic_event(1, time_ms=START + 10, mag=-0.5, depth_km=-3.0, country_id="ESP"),
        synthetic_event(2, time_ms=START + 20, mag=None, depth_km=None, country_id=None),
        synthetic_event(3, time_ms=START + HOUR + 5, mag=1.0, depth_km=10.0, country_id="ESP"),
        synthetic_event(4, time_ms=START + HOUR + 6, mag=6.9, depth_km=299.9, country_id="JPN"),
        synthetic_event(5, time_ms=START + 2 * HOUR + 1, mag=7.0, depth_km=300.0, country_id=None),
        synthetic_event(6, time_ms=START + 2 * HOUR + 2, mag=4.0, depth_km=None, country_id="JPN"),
        synthetic_event(7, time_ms=END, mag=3.0, depth_km=5.0, country_id="ESP"),
    ]


def _filters(**overrides) -> QueryFilters:
    values = {"start_ms": START, "end_ms": END, "min_mag": None, "country_id": None, "mode": "live"}
    values.update(overrides)
    return QueryFilters(**values)


async def _api_rows(db: TempDatabase, filters: QueryFilters):
    pool = await db.api_pool()
    try:
        async with read_transaction(pool, TIMEOUT_SECONDS) as conn:
            return (await fetch_hour_counts(conn, filters), await fetch_country_counts(conn, filters),
                    await fetch_histogram(conn, filters, "magnitude", MAGNITUDE_THRESHOLDS),
                    await fetch_histogram(conn, filters, "depth", DEPTH_THRESHOLDS))
    finally:
        await pool.close()


async def _admin_rows(db: TempDatabase, sql: str, *args):
    admin = await db.admin()
    try:
        return await admin.fetch(sql, *args)
    finally:
        await admin.close()


def _as_dict(rows, key: str) -> dict:
    return {row[key]: row["count"] for row in rows}


def _expected_where(min_mag: float | None, country: str | None) -> tuple[str, list]:
    conditions, args = ["event_time_ms >= $1", "event_time_ms < $2"], [START, END]
    if min_mag is not None:
        conditions.append(f"mag >= ${len(args) + 1}")
        args.append(min_mag)
    if country is not None:
        conditions.append(f"country_id = ${len(args) + 1}")
        args.append(country)
    return " AND ".join(conditions), args


def _direct(db, key_expression: str, where: str, args: list) -> dict:
    sql = f"SELECT {key_expression} AS k, count(*) AS count FROM live.current_event WHERE {where} GROUP BY 1"
    return _as_dict(asyncio.run(_admin_rows(db, sql, *args)), "k")


def _check(db, filters: QueryFilters, country: str | None = None):
    hours, countries, magnitude, depth = asyncio.run(_api_rows(db, filters))
    where, args = _expected_where(filters.min_mag, country)
    assert _as_dict(hours, "hour_start") == _direct(db, "(event_time_ms / 3600000) * 3600000", where, args)
    assert _as_dict(countries, "country_id") == _direct(db, "country_id", where, args)
    assert _as_dict(magnitude, "bucket") == _direct(db, MAG_CASE, where, args)
    assert _as_dict(depth, "bucket") == _direct(db, DEPTH_CASE, where, args)
    return hours, countries, magnitude, depth


def test_all_aggregations_match_direct_sql(db):
    asyncio.run(seed_database(db, live=_events(), countries=COUNTRIES))
    hours, _, magnitude, depth = _check(db, _filters())
    assert sum(r["count"] for r in hours) == 6
    assert {r["bucket"] for r in magnitude} == {None, 0, 1, 4, 6, 7}
    assert {r["bucket"] for r in depth} == {None, 0, 1, 3, 4}


def test_country_rows_include_unassigned_and_names_ordered(db):
    asyncio.run(seed_database(db, live=_events(), countries=COUNTRIES))
    _, countries, _, _ = asyncio.run(_api_rows(db, _filters()))
    assert [(r["country_id"], r["count"]) for r in countries] == [("ESP", 2), ("JPN", 2), (None, 2)]
    assert countries[0]["country_name"] == "España" and countries[0]["subregion"] == "Subregión ESP"
    assert countries[2]["country_name"] is None


def test_min_mag_and_country_filters_match_direct_sql(db):
    asyncio.run(seed_database(db, live=_events(), countries=COUNTRIES))
    _check(db, _filters(min_mag=1.0))
    _check(db, _filters(min_mag=-1.0, country_id="ESP"), country="ESP")


def test_country_none_only_counts_events_without_country(db):
    asyncio.run(seed_database(db, live=_events(), countries=COUNTRIES))
    _, countries, magnitude, _ = asyncio.run(_api_rows(db, _filters(country_id="none")))
    assert [(r["country_id"], r["count"]) for r in countries] == [(None, 2)]
    assert {r["bucket"] for r in magnitude} == {None, 7}


def test_empty_range_returns_no_rows(db):
    asyncio.run(seed_database(db, live=_events(), countries=COUNTRIES))
    rows = asyncio.run(_api_rows(db, _filters(start_ms=END + HOUR, end_ms=END + 2 * HOUR)))
    assert all(len(r) == 0 for r in rows)
