"""Base temporal, roles y comprobaciones comunes de las pruebas de integración (T036).

Cada sesión crea `observatory_test_<id>` con el administrador, le aplica `sql/001_schema.sql`
y los `GRANT` de `sql/002_roles.sql`, y la elimina al terminar. La base de la aplicación no se
toca. Sin `pytest-asyncio`: las pruebas llaman a `asyncio.run`.
"""
import asyncio
import os
import re
import uuid
from pathlib import Path

import asyncpg
import pytest

from tests.support.temp_database import CONNECT_TIMEOUT_SECONDS, TempDatabase

SQL_DIR = Path(os.environ.get("SQL_DIR", "/app/sql"))
SCHEMA_FILE = "001_schema.sql"
ROLES_FILE = "002_roles.sql"
TEMP_DB_PREFIX = "observatory_test_"
CONSUMER_ROLE = "observatory_consumer"
TABLES_TO_CLEAN = (
    "live.current_event, live.event_version, live.quarantine, live.exclusion, "
    "replay.current_event, replay.event_version, replay.quarantine, replay.exclusion, "
    "ingest.ingest_state, ingest.ingest_run, ingest.raw_response, public.date_dim, public.country"
)
GUARD_QUERIES = {
    "constraints": (
        "SELECT conrelid::regclass::text AS tbl, conname, pg_get_constraintdef(oid) AS def "
        "FROM pg_constraint WHERE connamespace::regnamespace::text IN ('public','live','replay','ingest') "
        "ORDER BY 1, 2"
    ),
    "triggers": (
        "SELECT tgrelid::regclass::text AS tbl, tgname FROM pg_trigger WHERE NOT tgisinternal ORDER BY 1, 2"
    ),
    "functions": (
        "SELECT n.nspname, p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname IN ('public','live','replay','ingest') ORDER BY 1, 2"
    ),
    "grants": (
        "SELECT table_schema, table_name, privilege_type FROM information_schema.role_table_grants "
        f"WHERE grantee = '{CONSUMER_ROLE}' AND table_schema IN ('public','live','replay','ingest') ORDER BY 1, 2, 3"
    ),
}


def _grant_statements(roles_sql: str) -> list[str]:
    """Extrae las sentencias GRANT de 002_roles.sql (el resto usa metacomandos de psql)."""
    without_comments = re.sub(r"--[^\n]*", "", roles_sql)
    statements = [s.strip() for s in without_comments.split(";")]
    return [s for s in statements if s.upper().startswith("GRANT")]


async def _create_database(env: dict, name: str) -> None:
    conn = await asyncpg.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]), database=env["DB_NAME"],
                                 user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
                                 timeout=CONNECT_TIMEOUT_SECONDS)
    try:
        await conn.execute(f'CREATE DATABASE "{name}"')
    finally:
        await conn.close()


async def _drop_database(env: dict, name: str) -> None:
    conn = await asyncpg.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]), database=env["DB_NAME"],
                                 user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
                                 timeout=CONNECT_TIMEOUT_SECONDS)
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    finally:
        await conn.close()


async def _apply_schema_and_grants(db: TempDatabase) -> None:
    conn = await db.admin()
    try:
        await conn.execute((SQL_DIR / SCHEMA_FILE).read_text(encoding="utf-8"))
        for statement in _grant_statements((SQL_DIR / ROLES_FILE).read_text(encoding="utf-8")):
            await conn.execute(statement)
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def db() -> TempDatabase:
    """Base temporal de la sesión, con el DDL y los permisos de los roles; se elimina al final."""
    env = {key: os.environ[key] for key in
           ("DB_HOST", "DB_PORT", "DB_NAME", "POSTGRES_USER", "POSTGRES_PASSWORD", "DB_USER", "DB_PASSWORD")}
    name = f"{TEMP_DB_PREFIX}{uuid.uuid4().hex[:12]}"
    asyncio.run(_create_database(env, name))
    database = TempDatabase(name, env["DB_HOST"], int(env["DB_PORT"]), env["POSTGRES_USER"],
                            env["POSTGRES_PASSWORD"], env["DB_USER"], env["DB_PASSWORD"],
                            producer_password=os.environ["DB_PRODUCER_PASSWORD"])
    try:
        asyncio.run(_apply_schema_and_grants(database))
        yield database
    finally:
        asyncio.run(_drop_database(env, name))


async def _truncate(db: TempDatabase) -> None:
    conn = await db.admin()
    try:
        await conn.execute(f"TRUNCATE {TABLES_TO_CLEAN} RESTART IDENTITY")
    finally:
        await conn.close()


@pytest.fixture(autouse=True)
def clean_tables(db: TempDatabase) -> None:
    """Vacía las tablas antes de cada prueba para que no dependa del orden."""
    asyncio.run(_truncate(db))


async def _snapshot(db: TempDatabase) -> dict[str, list[tuple]]:
    conn = await db.admin()
    try:
        return {key: [tuple(r.values()) for r in await conn.fetch(sql)] for key, sql in GUARD_QUERIES.items()}
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def schema_snapshot(db: TempDatabase) -> dict[str, list[tuple]]:
    """Instantánea inicial de restricciones, disparadores, funciones y permisos del consumidor."""
    return asyncio.run(_snapshot(db))


@pytest.fixture(autouse=True)
def schema_guard(db: TempDatabase, schema_snapshot: dict[str, list[tuple]]):
    """Tras cada prueba, falla si el esquema o los permisos difieren de la instantánea inicial."""
    yield
    current = asyncio.run(_snapshot(db))
    changed = [key for key in schema_snapshot if current[key] != schema_snapshot[key]]
    if changed:
        pytest.fail(f"La prueba dejó alterado el esquema o los permisos: {', '.join(changed)}", pytrace=False)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marca como `integration` toda prueba de este directorio."""
    here = Path(__file__).parent
    for item in items:
        if here in item.path.parents:
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def mock_usgs():
    """Servidor simulado de USGS (eventos sintéticos) que se apaga al terminar la prueba."""
    from tests.support.mock_usgs import MockUsgs
    server = MockUsgs().start()
    yield server
    server.stop()
