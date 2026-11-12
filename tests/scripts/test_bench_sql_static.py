"""Análisis estático de las sentencias de escritura del paquete de mediciones (T078, FR-016).

Recorre el código fuente de `scripts/benchmarks/` con `ast`, reúne las cadenas que empiezan por
una palabra de escritura SQL en mayúsculas y comprueba que solo tocan `bench`.
"""
import ast
import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "scripts" / "benchmarks"
WRITE_START = re.compile(r"^\s*(CREATE|DROP|INSERT|UPDATE|DELETE|TRUNCATE|ALTER|COMMENT|COPY|ANALYZE|GRANT|REVOKE)\b")
BENCH_TARGET = re.compile(r"\bbench\.|\bSCHEMA (IF EXISTS )?bench\b")
FORBIDDEN = re.compile(r"\b(live|replay|public|ingest)\.")
# La única lectura permitida dentro de una escritura: la estructura sale de la tabla real (D5).
ALLOWED_READ = "LIKE live.current_event INCLUDING DEFAULTS"


def string_literals(source: str) -> list[str]:
    """Cadenas del código; en las f-strings, cada valor interpolado se sustituye por `{}`."""
    texts = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.JoinedStr):
            texts.append("".join(p.value if isinstance(p, ast.Constant) else "{}" for p in node.values))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            texts.append(node.value)
    return texts


def violations(texts: list[str]) -> list[str]:
    """Sentencias de escritura que no califican con `bench.` o nombran otro esquema."""
    problems = []
    for text in texts:
        if not WRITE_START.match(text):
            continue
        if not BENCH_TARGET.search(text):
            problems.append(f"sin bench.: {text}")
        if FORBIDDEN.search(text.replace(ALLOWED_READ, "")):
            problems.append(f"esquema ajeno: {text}")
    return problems


def package_literals() -> list[str]:
    """Cadenas de todos los módulos del paquete."""
    return [text for path in sorted(PACKAGE.glob("*.py")) for text in string_literals(path.read_text("utf-8"))]


def test_every_write_statement_qualifies_with_bench() -> None:
    assert violations(package_literals()) == []


def test_the_closed_list_is_really_found() -> None:
    writes = [t for t in package_literals() if WRITE_START.match(t)]
    assert len(writes) >= 4
    assert any(t.startswith("CREATE SCHEMA bench") for t in writes)
    assert any("DROP SCHEMA IF EXISTS bench CASCADE" in t for t in writes)


def test_the_scanner_detects_bad_statements() -> None:
    bad = ["INSERT INTO live.current_event VALUES (1)", "DELETE FROM replay.current_event",
           "TRUNCATE public.country", "UPDATE ingest.ingest_state SET x = 1",
           "CREATE TABLE bench.event_1 AS SELECT * FROM live.current_event"]
    assert all(violations([statement]) for statement in bad)
    assert violations(["CREATE TABLE bench.event_{} (LIKE live.current_event INCLUDING DEFAULTS)"]) == []
