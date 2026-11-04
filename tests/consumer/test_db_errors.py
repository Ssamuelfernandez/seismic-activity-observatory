"""Pruebas de `is_content_error` con excepciones reales de asyncpg (T032)."""
import asyncio

import asyncpg
import pytest
from asyncpg import exceptions as pg_exc

from consumer.db_errors import is_content_error


def _postgres_error(sqlstate: str) -> pg_exc.PostgresError:
    """PostgresError genérico con el SQLSTATE indicado (como lo rellena asyncpg al leer el servidor)."""
    error = pg_exc.PostgresError("x")
    error.sqlstate = sqlstate
    return error


CONTENT_ERRORS = [
    pytest.param(pg_exc.CheckViolationError("x"), id="check_23514"),
    pytest.param(pg_exc.UniqueViolationError("x"), id="unique_23505"),
    pytest.param(pg_exc.ForeignKeyViolationError("x"), id="fk_23503"),
    pytest.param(pg_exc.NotNullViolationError("x"), id="not_null_23502"),
    pytest.param(pg_exc.DataError("x"), id="data_error_22000"),
    pytest.param(pg_exc.CharacterNotInRepertoireError("x"), id="char_repertoire_22021"),
    pytest.param(pg_exc.NumericValueOutOfRangeError("x"), id="numeric_range_22003"),
    pytest.param(UnicodeEncodeError("utf-8", "\ud800", 0, 1, "surrogates not allowed"), id="unicode_encode"),
    pytest.param(_postgres_error("22012"), id="sqlstate_prefix_22"),
    pytest.param(_postgres_error("23001"), id="sqlstate_prefix_23"),
]

TRANSIENT_ERRORS = [
    pytest.param(pg_exc.CannotConnectNowError("x"), id="cannot_connect_57P03"),
    pytest.param(asyncpg.InterfaceError("conexión cerrada"), id="interface_error"),
    pytest.param(OSError("red caída"), id="os_error"),
    pytest.param(asyncio.TimeoutError(), id="timeout"),
    pytest.param(pg_exc.InsufficientResourcesError("x"), id="insufficient_resources_53"),
    pytest.param(_postgres_error("54001"), id="sqlstate_54"),
    pytest.param(pg_exc.InsufficientPrivilegeError("x"), id="insufficient_privilege_42501"),
]


@pytest.mark.parametrize("error", CONTENT_ERRORS)
def test_content_errors_are_classified_as_content(error: BaseException) -> None:
    assert is_content_error(error) is True


@pytest.mark.parametrize("error", TRANSIENT_ERRORS)
def test_transient_errors_are_not_content(error: BaseException) -> None:
    assert is_content_error(error) is False


@pytest.mark.parametrize("error", [TypeError("defecto"), KeyError("k")])
def test_program_defects_are_not_content(error: BaseException) -> None:
    assert is_content_error(error) is False


def test_real_exceptions_come_from_asyncpg_library() -> None:
    assert pg_exc.CheckViolationError.__module__.startswith("asyncpg")
    assert pg_exc.CannotConnectNowError.__module__.startswith("asyncpg")
