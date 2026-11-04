"""Clasificación de errores de base de datos: contenido o transitorio (FR-014, research.md §7)."""
import asyncpg.exceptions as pg_exc

# Clases SQLSTATE que indican que el problema es el contenido del mensaje (datos 22, integridad 23).
CONTENT_SQLSTATE_CLASSES = frozenset({"22", "23"})
SQLSTATE_CLASS_LENGTH = 2
CONTENT_EXCEPTIONS = (pg_exc.IntegrityConstraintViolationError, pg_exc.DataError, UnicodeError)


def is_content_error(exc: BaseException) -> bool:
    """Indica si un error de base de datos lo causa el contenido del mensaje.

    Qué hace:
        Es verdadero si la excepción es de integridad (clase 23), de datos (clase 22) o un
        `UnicodeError` al codificar un argumento, o si su `sqlstate` empieza por 22 o 23.
        Es falso para fallos transitorios (conexión, recursos, permisos) y para defectos del
        programa (`TypeError`, `KeyError`), que el llamador no debe capturar.
    Recibe:
        exc: la excepción lanzada por el `INSERT` o el `COMMIT` de un mensaje ya validado.
    Devuelve:
        True si el mensaje debe ir a cuarentena como `db_constraint_violation`.
    Por qué existe:
        Separa lo que se reintenta (la base) de lo que no (el contenido) sin bloquear la
        partición con un mensaje venenoso (FR-014, FR-027).
    """
    if isinstance(exc, CONTENT_EXCEPTIONS):
        return True
    sqlstate = str(getattr(exc, "sqlstate", "") or "")
    return sqlstate[:SQLSTATE_CLASS_LENGTH] in CONTENT_SQLSTATE_CLASSES
