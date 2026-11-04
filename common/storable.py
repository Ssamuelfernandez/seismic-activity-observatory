"""Comprobaciones de almacenabilidad del contenido (research.md §4 y §5, FR-011, FR-014).

Funciones puras y sin recursión: ningún contenido debe hacer fallar una escritura en la base.
"""
import math
from typing import Any

# Salvaguarda propia: un anidamiento extremo no debe causar un error 54001 persistente en la base.
MAX_JSON_DEPTH = 64
# Longitud máxima de `event.id` (research.md §3, paso 12); la usan validación y cuarentena.
MAX_EVENT_ID_CHARS = 512
NUL_ESCAPE = "\\x00"


def is_storable_text(text: str) -> bool:
    """Indica si una cadena puede guardarse como `text`/`jsonb` de PostgreSQL.

    Qué hace:
        Rechaza el carácter NUL y los sustitutos sueltos (los detecta al codificar a UTF-8).
    Recibe:
        text: cadena a comprobar.
    Devuelve:
        True si es almacenable.
    Por qué existe:
        La regla de FR-014 la comparten la validación y la fila de cuarentena (C5).
    """
    if "\x00" in text:
        return False
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _is_storable_scalar(value: Any) -> bool:
    """Comprueba un valor que no es contenedor JSON."""
    if isinstance(value, str):
        return is_storable_text(value)
    if isinstance(value, float):
        return math.isfinite(value)
    return value is None or isinstance(value, (bool, int))


def _container_children(node: Any) -> list[Any] | None:
    """Devuelve los hijos de un contenedor (claves incluidas) o None si no lo es."""
    if isinstance(node, dict):
        return [*node.keys(), *node.values()]
    if isinstance(node, list):
        return list(node)
    return None


def is_storable_json(obj: Any) -> bool:
    """Indica si un valor JSON deserializado puede guardarse como `jsonb`.

    Qué hace:
        Recorre el valor con una pila explícita (sin recursión) y devuelve False ante un
        número no finito (`NaN`, `±Infinity`, `1e400`), una cadena (valor o clave) con NUL o
        sustituto suelto, o una profundidad mayor que `MAX_JSON_DEPTH`.
    Recibe:
        obj: valor producido por `json.loads`.
    Devuelve:
        True si es almacenable.
    Por qué existe:
        Decide, sin tocar la base, si un mensaje puede fallar al insertarse (FR-014, C5).
    """
    stack: list[tuple[Any, int]] = [(obj, 0)]
    while stack:
        node, depth = stack.pop()
        children = _container_children(node)
        if children is None:
            if not _is_storable_scalar(node):
                return False
            continue
        if depth + 1 > MAX_JSON_DEPTH:
            return False
        stack.extend((child, depth + 1) for child in children)
    return True


def sanitize_raw_text(raw: bytes | None) -> str:
    """Convierte los bytes recibidos en texto almacenable para `quarantine.raw_text`.

    Qué hace:
        Decodifica como UTF-8 dejando cada byte inválido como `\\xNN` literal y cambia cada
        NUL real por la cadena de 4 caracteres `\\x00`. `None` o vacío dan cadena vacía.
    Recibe:
        raw: bytes del valor Kafka, o None.
    Devuelve:
        Texto sin NUL ni sustitutos. No es reversible: la referencia fiable es el SHA-256.
    Por qué existe:
        Conserva lo recibido aunque no sea JSON ni UTF-8 válido (FR-011, C5).
    """
    if not raw:
        return ""
    return raw.decode("utf-8", errors="backslashreplace").replace("\x00", NUL_ESCAPE)
