"""Registro de comprobaciones y escritura de evidencias de `verify_consumer.py`.

Las evidencias se escriben siempre en UTF-8 y con saltos de línea `\\n`, sin depender de la
codificación de la consola de Windows (cp1252). `print` está permitido (CC-DOC).
"""
from pathlib import Path

from scripts.consumer_scenarios.helpers import evidence_path

ENCODING = "utf-8"


class Checks:
    """Acumula las comprobaciones de un escenario; el código de salida es 0 solo si todas pasan."""

    def __init__(self) -> None:
        self.results: list[tuple[bool, str]] = []
        self._pending: list[str] = []

    def record(self, passed: bool, name: str, detail: str = "") -> None:
        """Registra e imprime una comprobación; queda pendiente de guardarse en una evidencia."""
        self.results.append((passed, name))
        line = f"{'PASS' if passed else 'FAIL'}  {name}" + (f" — {detail}" if detail else "")
        self._pending.append(line)
        say(line)

    def take_lines(self) -> str:
        """Devuelve (y vacía) las líneas de las comprobaciones registradas desde la última llamada."""
        lines, self._pending = self._pending, []
        return "\n".join(lines) or "(sin comprobaciones)"

    def exit_code(self) -> int:
        """0 si todas las comprobaciones pasaron; 1 si alguna falló o no hubo ninguna."""
        return 0 if self.results and all(passed for passed, _ in self.results) else 1


def say(text: str = "") -> None:
    """Imprime tolerando consolas que no admiten todos los caracteres (se sustituyen, no se rompe)."""
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)


class Evidence:
    """Un archivo de evidencia formado por bloques con cabecera `-- [n] etiqueta`."""

    def __init__(self, name: str, extension: str) -> None:
        self.path: Path = evidence_path(name, extension)
        self.blocks: list[str] = []

    def add(self, label: str, body: str) -> None:
        """Añade un bloque numerado y lo imprime."""
        block = f"-- [{len(self.blocks) + 1}] {label}\n{body}\n"
        self.blocks.append(block)
        say(f"\n{block}")

    def write(self) -> Path:
        """Guarda el archivo (UTF-8, `\\n`) y devuelve su ruta."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(self.blocks), encoding=ENCODING, newline="\n")
        return self.path
