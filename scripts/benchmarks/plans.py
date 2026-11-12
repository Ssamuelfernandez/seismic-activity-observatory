"""Lectura pura de los planes `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` de PostgreSQL (E6, K3).

Sin E/S: recibe el JSON ya parseado y extrae el tiempo del servidor, los buffers y los nodos usados.
"""
from dataclasses import dataclass

INDEX_NODE_PREFIXES = ("Index Scan", "Index Only Scan", "Bitmap Index Scan")


@dataclass(frozen=True)
class PlanInfo:
    """Resumen de un plan: tiempo de ejecución, buffers, tipos de nodo e índices nombrados."""

    execution_ms: float | None
    shared_hit: int | None
    shared_read: int | None
    node_types: tuple[str, ...]
    index_names: tuple[str, ...]

    @property
    def uses_index(self) -> bool:
        """True si algún nodo del plan es un recorrido por índice."""
        return any(node.startswith(INDEX_NODE_PREFIXES) for node in self.node_types)


def _walk(node: dict, types: list[str], indexes: list[str]) -> None:
    """Recorre el árbol del plan en profundidad anotando tipos de nodo e índices."""
    types.append(node.get("Node Type", ""))
    if node.get("Index Name"):
        indexes.append(node["Index Name"])
    for child in node.get("Plans", []):
        _walk(child, types, indexes)


def summarize_plan(plan: list[dict]) -> PlanInfo:
    """Resume el JSON de `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`.

    Recibe:
        plan: la lista de un elemento que devuelve PostgreSQL (`[{"Plan": ..., "Execution Time": ...}]`).
    Devuelve:
        `PlanInfo` con `Execution Time`, `Shared Hit/Read Blocks` del nodo raíz y los nodos usados.
    Por qué existe:
        Permite citar el nodo usado (`Seq Scan`/`Index Scan`) y contrastarlo con la teoría (K3, E6).
    """
    root = plan[0]["Plan"]
    types: list[str] = []
    indexes: list[str] = []
    _walk(root, types, indexes)
    return PlanInfo(plan[0].get("Execution Time"), root.get("Shared Hit Blocks"),
                    root.get("Shared Read Blocks"), tuple(types), tuple(indexes))


def theory_note(info: PlanInfo, expected_index: bool) -> str:
    """Texto para `notes`: vacío si el plan coincide con la teoría; avisa si no coincide."""
    if info.uses_index == expected_index:
        return ""
    used = ", ".join(info.node_types[:2])
    expected = "recorrido por índice" if expected_index else "recorrido secuencial"
    return f"el planificador no coincide con la teoría: usó {used}; se esperaba {expected}"
