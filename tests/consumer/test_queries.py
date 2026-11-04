"""Pruebas de `consumer/queries.py`: sentencias SQL y lista cerrada de esquemas (T034)."""
import pytest

from consumer import queries


@pytest.mark.parametrize("mode", ["live", "replay"])
def test_schema_for_mode_accepts_closed_list(mode: str) -> None:
    assert queries.schema_for_mode(mode) == mode


@pytest.mark.parametrize("mode", ["", "LIVE", "public", "live; DROP TABLE x", "ingest"])
def test_schema_for_mode_rejects_anything_else(mode: str) -> None:
    with pytest.raises(ValueError):
        queries.schema_for_mode(mode)


def test_quarantine_statement_has_no_conflict_target() -> None:
    sql = queries.quarantine_insert("live")
    assert "ON CONFLICT DO NOTHING" in sql
    assert "ON CONFLICT (" not in sql
    assert "RETURNING" not in sql
    assert "ON CONSTRAINT" not in sql
    assert "DO UPDATE" not in sql
    assert "live.quarantine" in sql


def test_current_event_upsert_is_conditional_and_ignores_country() -> None:
    sql = queries.current_event_upsert("live")
    assert "ON CONFLICT (event_id) DO UPDATE" in sql
    assert "WHERE EXCLUDED.updated_ms >" in sql
    assert "country_id" not in sql


def test_event_version_insert_conflicts_on_primary_key() -> None:
    assert "ON CONFLICT (event_id, updated_ms) DO NOTHING" in queries.event_version_insert("replay")


def test_date_dim_insert_conflicts_on_date_id() -> None:
    assert "ON CONFLICT (date_id) DO NOTHING" in queries.DATE_DIM_INSERT


def test_country_upsert_is_conditional() -> None:
    sql = queries.COUNTRY_UPSERT
    assert "ON CONFLICT (country_id) DO UPDATE" in sql
    assert "IS DISTINCT FROM" in sql


def test_state_lookup_locks_the_row() -> None:
    assert "FOR UPDATE" in queries.select_stored_updated("live")


def test_schema_is_composed_only_from_closed_list() -> None:
    with pytest.raises(ValueError):
        queries.quarantine_insert("live.x; --")


def test_placeholders_match_column_count() -> None:
    sql = queries.current_event_upsert("live")
    assert f"${len(queries.CURRENT_COLUMNS)}" in sql
    assert f"${len(queries.CURRENT_COLUMNS) + 1}" not in sql
