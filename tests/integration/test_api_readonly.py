"""La API es de solo lectura: permisos del rol real y SQL de `api/` (T020: F10, F11, SC-008, FR-014, FR-017)."""
import ast
import asyncio
import re
from pathlib import Path

import asyncpg
import pytest

API_DIR = Path(__file__).resolve().parents[2] / "api"
INSERT_SQL = {
    "live.current_event": "INSERT INTO live.current_event (event_id) VALUES ('synthetic-x')",
    "replay.current_event": "INSERT INTO replay.current_event (event_id) VALUES ('synthetic-x')",
    "public.country": "INSERT INTO public.country (country_id, name_es) VALUES ('ZZZ', 'x')",
    "ingest.ingest_run": "INSERT INTO ingest.ingest_run (run_at, url, status) VALUES (now(), 'x', 200)",
}
TABLES = list(INSERT_SQL)
FORBIDDEN_SQL = re.compile(r"\b(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|DROP|ALTER|GRANT)\b")


async def _expect_denied(db, sql: str) -> None:
    pool = await db.api_pool()
    try:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await pool.execute(sql)
    finally:
        await pool.close()


@pytest.mark.parametrize("table", TABLES)
def test_insert_is_denied(db, table):
    asyncio.run(_expect_denied(db, INSERT_SQL[table]))


@pytest.mark.parametrize("table", TABLES)
def test_update_is_denied(db, table):
    asyncio.run(_expect_denied(db, f"UPDATE {table} SET url = 'x'" if table == "ingest.ingest_run"
                               else f"UPDATE {table} SET {'name_es' if table == 'public.country' else 'place'} = 'x'"))


@pytest.mark.parametrize("table", TABLES)
def test_delete_is_denied(db, table):
    asyncio.run(_expect_denied(db, f"DELETE FROM {table}"))


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Identifica los nodos de texto que son docstrings (se excluyen de la búsqueda)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def _string_constants(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstring_nodes(tree)
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip]


def test_no_sql_string_in_api_writes_or_changes_schema():
    files = sorted(API_DIR.rglob("*.py"))
    assert files, "No se encontró el código de api/"
    offenders = [f"{path.name}: {text[:60]!r}" for path in files for text in _string_constants(path)
                 if FORBIDDEN_SQL.search(text)]
    assert not offenders, offenders
