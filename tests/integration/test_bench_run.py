"""Ensayo y corrida completa del CLI de mediciones contra el stack real (T087, K1 a K4, E6).

El ensayo crea `bench` en la base real del stack (datos SINTÉTICOS), escribe en una carpeta
temporal y comprueba aislamiento y completitud. La corrida completa se ejecuta aparte con el
CLI; si su salida está en `/app/evidence-mediciones`, la segunda prueba la comprueba.
"""
import asyncio
import json
import os
import re
from pathlib import Path

import pytest

from scripts.benchmarks.bench_schema import connect_admin
from scripts.benchmarks.run_benchmarks import main

EMPTY_CELL = re.compile(r"\|[ \t]*\|")
FULL_OUT = Path("/app/evidence-mediciones")
MD_FILES = ("tablas.md", "indices.md", "aislamiento.md", "almacenamiento.md", "equipo.md", "costes.md",
            "transferencia.md")
Q = {"namespace": "SELECT to_regnamespace('bench')::text",
     "outside": "SELECT count(*) FROM live.current_event WHERE event_id LIKE 'synthetic-bench-%'"}


def db_state() -> tuple[str | None, int]:
    """`to_regnamespace('bench')` y filas de bench en `live.current_event`, leídos como administrador."""
    async def main():
        conn = await connect_admin(dict(os.environ))
        try:
            return await conn.fetchval(Q["namespace"]), await conn.fetchval(Q["outside"])
        finally:
            await conn.close()
    return asyncio.run(main())


def assert_outputs_complete(out: Path, sizes: list[int]) -> dict:
    """Comprueba sin celdas vacías, etiqueta SINTÉTICO, N real >= 3 y un plan por consulta de Postgres."""
    data = json.loads((out / "resultados.json").read_text("utf-8"))
    measurements = data["measurements"]
    assert data["etiqueta"] == "SINTETICO" and sorted({m["size"] for m in measurements}) == sorted(sizes)
    assert all(m["n_real"] >= 3 and len(m["samples_ms"]) == m["n_real"] for m in measurements)
    postgres = [m for m in measurements if m["strategy"].startswith("pg_") or m["operation"] == "agg"]
    assert postgres and all(m["plan_ref"] and (out / m["plan_ref"]).is_file() for m in postgres)
    for name in MD_FILES:
        text = (out / name).read_text("utf-8")
        assert text.strip() and not EMPTY_CELL.search(text), f"celdas vacías en {name}"
    tables = (out / "tablas.md").read_text("utf-8")
    assert "SINTÉTICO" in tables and "Violaciones: ninguna" in (out / "aislamiento.md").read_text("utf-8")
    return data


def test_trial_run_exits_zero_leaves_no_bench_and_writes_complete_outputs(tmp_path: Path) -> None:
    before = db_state()
    code = main(["--sizes", "1000", "--repeats", "3", "--budget", "10", "--yes", "--out", str(tmp_path)])
    assert code == 0 and db_state() == (None, 0) == (before[0], before[1])
    data = assert_outputs_complete(tmp_path, [1000])
    ids = {m["id"] for m in data["measurements"]}
    assert "search.dict.1000.absent" in ids and "geo.naive.1000.ocean" in ids and "agg.q4_time_index.1000.day" in ids


def test_full_run_evidence_has_three_sizes_when_present() -> None:
    path = FULL_OUT / "resultados.json"
    if not path.is_file() or json.loads(path.read_text("utf-8"))["params"]["sizes"] != [1000, 10000, 100000]:
        pytest.skip("la corrida completa aún no ha dejado resultados.json con los 3 tamaños")
    assert_outputs_complete(FULL_OUT, [1000, 10000, 100000])
    assert db_state() == (None, 0)
