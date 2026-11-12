"""Pruebas sin Docker de la reescritura de índices y del análisis de planes (T079, E6)."""
import json

import pytest

from scripts.benchmarks.bench_load import find_index, index_columns, IndexDef, rewrite_index
from scripts.benchmarks.plans import summarize_plan, theory_note

PK = "CREATE UNIQUE INDEX current_event_pkey ON live.current_event USING btree (event_id)"
TIME = "CREATE INDEX ix_current_event_time ON live.current_event USING btree (event_time DESC, event_id DESC)"


def test_rewrite_index_replaces_schema_table_and_name_without_live() -> None:
    index = rewrite_index(TIME, "event_1000", "b1000")
    assert index.name == "ix_current_event_time_b1000"
    assert index.create_sql == ("CREATE INDEX ix_current_event_time_b1000 ON bench.event_1000 "
                                "USING btree (event_time DESC, event_id DESC)")
    assert "live." not in index.create_sql and "live." not in rewrite_index(PK, "event_1000", "b1000").create_sql
    assert rewrite_index(PK, "event_10", "x").create_sql.startswith("CREATE UNIQUE INDEX current_event_pkey_x ON bench.")


def test_rewrite_rejects_unknown_definitions_and_bad_tables() -> None:
    with pytest.raises(ValueError):
        rewrite_index("CREATE INDEX x ON public.country (a)", "event_1", "b")
    with pytest.raises(ValueError):
        rewrite_index(PK, "event_1; DROP SCHEMA live", "b")


def test_columns_are_read_from_definition_and_found_by_columns() -> None:
    assert index_columns(TIME) == ("event_time", "event_id")
    defs = [IndexDef("a", PK, index_columns(PK)), IndexDef("b", TIME, index_columns(TIME))]
    assert find_index(defs, ("event_id",)).name == "a"
    with pytest.raises(LookupError):
        find_index(defs, ("mag",))


def test_plan_summary_reads_nodes_time_and_buffers() -> None:
    plan = json.loads('[{"Plan": {"Node Type": "Aggregate", "Shared Hit Blocks": 7, "Shared Read Blocks": 2,'
                      ' "Plans": [{"Node Type": "Index Scan", "Index Name": "ix"}]}, "Execution Time": 0.5}]')
    info = summarize_plan(plan)
    assert (info.execution_ms, info.shared_hit, info.shared_read) == (0.5, 7, 2)
    assert info.uses_index and info.index_names == ("ix",)
    assert theory_note(info, expected_index=True) == "" and "no coincide" in theory_note(info, expected_index=False)
