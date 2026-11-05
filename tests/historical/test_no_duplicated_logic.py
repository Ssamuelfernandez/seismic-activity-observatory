"""El histórico no duplica validación, conversión de tiempos ni país (T017, B16, SC-008, FR-009).

Revisión estática (AST) de `historical/`: sin importaciones de los módulos de procesamiento de
`common/`, sin funciones con esos nombres y con `load_historical` llamando a `process_record`.
"""
import ast
from pathlib import Path

HISTORICAL_DIR = Path(__file__).resolve().parents[2] / "historical"
FORBIDDEN_MODULES = ("common.validation", "common.transform", "common.geo", "common.decode")
FORBIDDEN_DEFINITIONS = ("validate", "ms_to_utc", "assign_country", "build_event_rows", "decode_value")
# Excepción única y acotada: `load_main.py` enlaza el localizador de país en `PipelineDeps`
# (igual que `consumer/loop.py`); la asignación sigue ocurriendo dentro de `process_record`.
ALLOWED_IMPORTS = {("load_main.py", "common.geo")}


def _trees() -> dict[str, ast.Module]:
    return {path.name: ast.parse(path.read_text(encoding="utf-8")) for path in HISTORICAL_DIR.glob("*.py")}


def _imported_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def test_historical_package_exists_and_is_scanned() -> None:
    assert {"loader.py", "load_main.py", "envelope.py"} <= set(_trees())


def test_no_forbidden_processing_imports() -> None:
    found = [(name, module) for name, tree in _trees().items() for module in _imported_modules(tree)
             if module.startswith(FORBIDDEN_MODULES) and (name, module) not in ALLOWED_IMPORTS]
    assert found == []


def test_loader_imports_nothing_from_processing_modules() -> None:
    modules = _imported_modules(_trees()["loader.py"])
    assert not [module for module in modules if module.startswith(FORBIDDEN_MODULES)]


def test_no_function_reimplements_processing() -> None:
    defined = [(name, node.name) for name, tree in _trees().items() for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and any(word in node.name for word in FORBIDDEN_DEFINITIONS)]
    assert defined == []


def test_load_historical_calls_process_record() -> None:
    tree = _trees()["loader.py"]
    function = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.AsyncFunctionDef) and node.name == "load_historical")
    calls = [node.func.id for node in ast.walk(function) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name)]
    assert "process_record" in calls
    assert any(isinstance(node, ast.ImportFrom) and node.module == "consumer.pipeline"
               and any(alias.name == "process_record" for alias in node.names) for node in ast.walk(tree))
