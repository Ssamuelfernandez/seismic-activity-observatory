"""Ciclo de vida del esquema temporal `bench` y comprobación de aislamiento (K4, FR-012 a FR-017).

Es lo único que escribe en la base y solo en `bench`: la lista cerrada de sentencias de escritura
califica siempre con `bench.` (una prueba estática lo comprueba). Las lecturas de `live`,
`replay` y `public` no pasan por aquí salvo el recuento de aislamiento.
"""
import asyncio
import contextlib
import signal
from collections.abc import AsyncIterator, Mapping

import asyncpg

SCHEMA = "bench"
MARK = "SINTETICO-BENCH-TEMPORAL"
SCHEMA_COMMENT = f"{MARK}: datos sinteticos de mediciones-costes"
CONNECT_TIMEOUT_SECONDS = 10
ADMIN_ENV = ("DB_HOST", "DB_PORT", "DB_NAME", "POSTGRES_USER", "POSTGRES_PASSWORD")

# Lista cerrada de sentencias de escritura (FR-016): todo lo que este módulo escribe.
CREATE_SCHEMA_SQL = "CREATE SCHEMA bench"
COMMENT_SCHEMA_SQL = f"COMMENT ON SCHEMA bench IS '{SCHEMA_COMMENT}'"
# La estructura sale de la tabla real (D5): sin CHECK ni índices, que se añaden al medir.
CREATE_TABLE_SQL = "CREATE TABLE bench.event_{size} (LIKE live.current_event INCLUDING DEFAULTS)"
DROP_SCHEMA_SQL = "DROP SCHEMA IF EXISTS bench CASCADE"

REPLAY_TABLES = ("replay.current_event", "replay.event_version", "replay.quarantine", "replay.exclusion")
BENCH_ID_PATTERN = "synthetic-bench-%"
OUTSIDE_TABLES = ("live.current_event", "live.quarantine", "live.exclusion",
                  "replay.current_event", "replay.quarantine", "replay.exclusion")
NAMESPACE_SQL = "SELECT to_regnamespace('bench') IS NOT NULL"
COMMENT_SQL = "SELECT obj_description(to_regnamespace('bench'), 'pg_namespace')"
CREATE_PRIVILEGE_SQL = "SELECT has_database_privilege(current_user, current_database(), 'CREATE')"


class BenchSchemaError(RuntimeError):
    """No se puede crear o limpiar `bench` sin riesgo (existe uno ajeno, falta base o permiso)."""


async def connect_admin(env: Mapping[str, str]) -> asyncpg.Connection:
    """Conecta como administrador a la base del stack, o falla sin crear nada.

    Recibe:
        env: variables del servicio `tests` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `POSTGRES_USER`,
        `POSTGRES_PASSWORD`).
    Devuelve:
        Conexión abierta con permiso de crear esquemas.
    Por qué existe:
        Sin base o sin administrador la ejecución se detiene antes de escribir nada (prov. 1 y 3).
    """
    missing = [name for name in ADMIN_ENV if not env.get(name)]
    if missing:
        raise BenchSchemaError(f"faltan variables de entorno: {', '.join(missing)}")
    try:
        conn = await asyncpg.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]), database=env["DB_NAME"],
                                     user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
                                     timeout=CONNECT_TIMEOUT_SECONDS)
    except (OSError, asyncpg.PostgresError, asyncio.TimeoutError) as error:
        raise BenchSchemaError(f"no se pudo conectar a la base: {error}") from error
    if not await conn.fetchval(CREATE_PRIVILEGE_SQL):
        await conn.close()
        raise BenchSchemaError("el usuario no puede crear esquemas (se necesita el administrador)")
    return conn


async def bench_state(conn: asyncpg.Connection) -> tuple[bool, str | None]:
    """Devuelve si `bench` existe y su comentario."""
    exists = await conn.fetchval(NAMESPACE_SQL)
    return exists, (await conn.fetchval(COMMENT_SQL)) if exists else None


async def clean_if_marked(conn: asyncpg.Connection) -> bool:
    """Elimina `bench` solo si existe y lleva la marca de este script.

    Devuelve:
        True si lo eliminó, False si no existía.
    Lanza:
        `BenchSchemaError` si existe pero no lleva la marca (es ajeno: no se toca).
    Por qué existe:
        `--clean` nunca debe borrar un esquema que no creó este script (FR-012, D3).
    """
    exists, comment = await bench_state(conn)
    if not exists:
        return False
    if comment is None or MARK not in comment:
        raise BenchSchemaError("existe un esquema 'bench' sin la marca SINTETICO-BENCH-TEMPORAL: no se toca")
    await conn.execute(DROP_SCHEMA_SQL)
    return True


async def create_bench(conn: asyncpg.Connection, sizes: list[int], clean: bool = False) -> None:
    """Crea `bench` con una tabla por tamaño, o aborta si ya existe uno.

    Qué hace:
        Si `bench` existe: con `clean` y marca lo elimina; en otro caso aborta sin tocarlo.
        Crea esquema, comentario y tablas en una transacción (todo o nada).
    Recibe:
        conn: conexión del administrador; sizes: tamaños de tabla; clean: permiso de limpiar.
    Por qué existe:
        Aísla los datos sintéticos de `live`, `replay`, `public` e `ingest` (K4, FR-012, FR-013).
    """
    exists, _ = await bench_state(conn)
    if exists:
        if not clean:
            raise BenchSchemaError("el esquema 'bench' ya existe: usa --clean si es de una ejecución anterior")
        await clean_if_marked(conn)
    async with conn.transaction():
        await conn.execute(CREATE_SCHEMA_SQL)
        await conn.execute(COMMENT_SCHEMA_SQL)
        for size in sizes:
            await conn.execute(CREATE_TABLE_SQL.format(size=int(size)))


async def drop_bench(conn: asyncpg.Connection) -> None:
    """Elimina `bench` si existe. Solo se llama tras haberlo creado esta misma ejecución."""
    await conn.execute(DROP_SCHEMA_SQL)


@contextlib.contextmanager
def _cancel_on_sigterm():
    """Convierte SIGTERM en la cancelación de la tarea actual, para que corra el `finally`.

    En plataformas sin `add_signal_handler` (Windows) no instala nada: el `finally` cubre el resto.
    """
    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGTERM, asyncio.current_task().cancel)
    except (NotImplementedError, RuntimeError):
        yield
        return
    try:
        yield
    finally:
        loop.remove_signal_handler(signal.SIGTERM)


@contextlib.asynccontextmanager
async def bench_session(conn: asyncpg.Connection, sizes: list[int], clean: bool = False) -> AsyncIterator[None]:
    """Crea `bench`, cede el control y lo elimina siempre (error, Ctrl+C o SIGTERM).

    Por qué existe:
        `DROP SCHEMA bench CASCADE` garantizado ante cualquier salida (FR-012, FR-017).
    """
    await create_bench(conn, sizes, clean)
    try:
        with _cancel_on_sigterm():
            yield
    finally:
        await drop_bench(conn)


async def take_snapshot(conn: asyncpg.Connection) -> dict:
    """Recuentos para comprobar el aislamiento (FR-017): lecturas, sin escribir nada.

    Devuelve:
        Diccionario con `bench_exists`, el recuento de cada tabla de `replay`, el de
        `usgs_historical` en `live.current_event` y las filas con id de bench fuera de `bench`.
    """
    snapshot: dict = {"bench_exists": await conn.fetchval(NAMESPACE_SQL)}
    for table in REPLAY_TABLES:
        snapshot[table] = await conn.fetchval(f"SELECT count(*) FROM {table}")
    snapshot["usgs_historical"] = await conn.fetchval(
        "SELECT count(*) FROM live.current_event WHERE source = 'usgs_historical'")
    key = "event_id"
    snapshot["bench_rows_outside"] = {
        table: await conn.fetchval(f"SELECT count(*) FROM {table} WHERE {key} LIKE $1", BENCH_ID_PATTERN)
        for table in OUTSIDE_TABLES}
    return snapshot


def verify_isolation(before: dict, after: dict) -> list[str]:
    """Compara dos instantáneas y devuelve las violaciones de aislamiento (lista vacía = correcto).

    Comprueba que `bench` no existe al final, que no hay filas de bench fuera del esquema y que
    los recuentos de `replay.*` y de `usgs_historical` no cambiaron. No compara el total de
    `live`: el consumidor sigue ingiriendo.
    """
    problems = []
    if after["bench_exists"]:
        problems.append("el esquema 'bench' sigue existiendo")
    for table, count in after["bench_rows_outside"].items():
        if count:
            problems.append(f"{count} filas de bench en {table}")
    for name in (*REPLAY_TABLES, "usgs_historical"):
        if before[name] != after[name]:
            problems.append(f"cambió el recuento de {name}: {before[name]} -> {after[name]}")
    return problems
