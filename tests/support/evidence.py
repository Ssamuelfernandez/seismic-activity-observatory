"""Escritura de evidencias desde las pruebas de integración (T036).

`print` está permitido aquí: la salida está pensada para el usuario y para la evidencia.
Semántica: la primera llamada de una sesión con un `name` trunca el archivo; cada llamada añade
al final un bloque con cabecera `-- [n] <label>`. Si `EVIDENCE_DIR` no existe o no es escribible,
solo se imprime.
"""
import os
from pathlib import Path
from typing import Any

EVIDENCE_DIR_ENV = "EVIDENCE_DIR"
ENCODING = "utf-8"
NULL_TEXT = "NULL"

_seen_files: set[Path] = set()
_block_counts: dict[Path, int] = {}


def _evidence_dir() -> Path | None:
    """Directorio de evidencias si está definido y es escribible; si no, None."""
    value = os.environ.get(EVIDENCE_DIR_ENV)
    if not value:
        return None
    path = Path(value)
    return path if path.is_dir() and os.access(path, os.W_OK) else None


def _append_block(name: str, extension: str, label: str, body: str) -> None:
    """Añade un bloque con cabecera numerada al archivo `<name>.<extension>` (trunca la 1.ª vez)."""
    directory = _evidence_dir()
    if directory is None:
        return
    path = directory / f"{name}.{extension}"
    mode = "a" if path in _seen_files else "w"
    _seen_files.add(path)
    number = _block_counts.get(path, 0) + 1
    _block_counts[path] = number
    with open(path, mode, encoding=ENCODING, newline="\n") as handle:
        handle.write(f"-- [{number}] {label}\n{body}\n\n")


def format_table(columns: list[str], rows: list[tuple]) -> str:
    """Tabla de texto alineada con cabecera y recuento de filas."""
    cells = [[NULL_TEXT if v is None else str(v) for v in row] for row in rows]
    widths = [max([len(c)] + [len(r[i]) for r in cells]) for i, c in enumerate(columns)]
    line = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    separator = "-+-".join("-" * w for w in widths)
    body = [" | ".join(v.ljust(w) for v, w in zip(r, widths)) for r in cells]
    return "\n".join([line, separator, *body, f"({len(rows)} filas)"])


async def record_query(conn: Any, name: str, sql: str, params: tuple = (), label: str = "") -> list[tuple]:
    """Ejecuta una consulta con el administrador, la imprime y guarda `.sql` y `.out`.

    Devuelve las filas como tuplas para que la prueba también pueda comprobarlas.
    """
    statement = await conn.prepare(sql)
    columns = [attribute.name for attribute in statement.get_attributes()]
    records = await statement.fetch(*params)
    rows = [tuple(r.values()) for r in records]
    table = format_table(columns, rows)
    shown_params = f"\n-- parámetros: {params!r}" if params else ""
    print(f"\n-- [{label}] {name}\n{sql}{shown_params}\n{table}")
    _append_block(name, "sql", label, f"{sql};{shown_params}")
    _append_block(name, "out", label, f"{sql}{shown_params}\n\n{table}")
    return rows


def record_text(name: str, text: str, label: str = "") -> None:
    """Imprime un texto y lo añade como bloque a `<name>.out`."""
    print(f"\n-- [{label}] {name}\n{text}")
    _append_block(name, "out", label, text)
