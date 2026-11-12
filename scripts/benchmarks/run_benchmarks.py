"""CLI de las mediciones de complejidad y costes (K1 a K7): solo orquesta, no mide ni formatea.

Uso (servicio `tests`, con el stack en marcha):
    python -m scripts.benchmarks.run_benchmarks --sizes 1000 --repeats 3 --budget 10 --yes

Escribe en `--out` (por defecto el montaje `/app/evidence-mediciones`) y deja la base como estaba:
el esquema `bench` se elimina siempre y el aislamiento se comprueba antes y después.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import asyncpg

from common.geo import assign_country, build_country_index, parse_country_catalog
from scripts.benchmarks import costs, report, transfer
from scripts.benchmarks.bench_load import analyze, load_table, read_index_definitions
from scripts.benchmarks.bench_schema import (BenchSchemaError, bench_session, connect_admin, take_snapshot,
                                             verify_isolation)
from scripts.benchmarks.hardware import read_machine, render_equipo_md
from scripts.benchmarks.op_agg import run_agg
from scripts.benchmarks.op_geo import run_geo
from scripts.benchmarks.op_search import run_search
from scripts.benchmarks.seed import SeedError, load_seed
from scripts.benchmarks.stats import BUDGET_SECONDS, N_MAX
from scripts.benchmarks.storage import (measure_bench_storage, read_real_reference, read_storage,
                                        render_storage_md)
from scripts.benchmarks.synth import build_rows

LOG = logging.getLogger("benchmarks")
DEFAULT_SIZES = (1000, 10000, 100000)
DEFAULT_OUT = "/app/evidence-mediciones"
DATA_DIRS = {"data/historical": Path("/app/data/historical"), "data/catalogo": Path("/app/data/catalogo")}
CATALOG_FILE = "paises.geojson"
API_USER = "observatory_api"
CONNECT_TIMEOUT_SECONDS = 10


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Argumentos: tamaños, repeticiones máximas, presupuesto por serie, limpieza y confirmación."""
    parser = argparse.ArgumentParser(description="Mediciones de complejidad y costes (datos SINTÉTICOS en `bench`).")
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))
    parser.add_argument("--repeats", type=int, default=N_MAX)
    parser.add_argument("--budget", type=float, default=BUDGET_SECONDS)
    parser.add_argument("--clean", action="store_true", help="elimina un `bench` marcado de una ejecución anterior")
    parser.add_argument("--yes", action="store_true", help="no pide confirmación")
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT))
    return parser.parse_args(argv)


def confirm(args: argparse.Namespace) -> bool:
    """Pide confirmación antes de escribir en la base (salvo `--yes`)."""
    if args.yes:
        return True
    answer = input("Se creará el esquema temporal `bench` (datos SINTÉTICOS) y se eliminará al terminar. ¿Seguir? [s/N] ")
    return answer.strip().lower() in ("s", "si", "sí", "y", "yes")


async def connect_api(env: dict) -> asyncpg.Connection:
    """Conexión del rol de solo lectura de la API (referencia real de índices y definiciones)."""
    return await asyncpg.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]), database=env["DB_NAME"],
                                 user=API_USER, password=env["DB_API_PASSWORD"], timeout=CONNECT_TIMEOUT_SECONDS)


def measure_transfer() -> list[transfer.RouteBytes] | None:
    """Bytes de las rutas de la API; `None` si no responde (se informa «no disponible», sin inventar)."""
    try:
        return transfer.measure_routes()
    except transfer.TransferError as error:
        LOG.warning("transferencia no disponible: %s", error)
        return None


async def run_size(admin: asyncpg.Connection, size: int, seed_events: list[dict], catalog, defs: list,
                   plans_dir: Path, args: argparse.Namespace) -> tuple[list, list, dict]:
    """Carga `bench.event_<size>` y ejecuta las operaciones a, b y c; devuelve mediciones, veredictos y tamaños."""
    index = build_country_index(catalog)
    rows = build_rows(seed_events, size, lambda lon, lat: assign_country(index, lon, lat).country_id)
    await load_table(admin, size, rows)
    await analyze(admin, f"event_{size}")
    kwargs = {"n_max": args.repeats, "budget": args.budget}
    started = time.perf_counter()
    found = await run_search(admin, size, rows, defs, plans_dir, **kwargs)
    LOG.info("size=%d search listo en %.1f s", size, time.perf_counter() - started)
    found += run_geo(rows, size, catalog, **kwargs)
    LOG.info("size=%d geo listo (acumulado %.1f s)", size, time.perf_counter() - started)
    agg, verdicts = await run_agg(admin, size, rows, defs, plans_dir, **kwargs)
    LOG.info("size=%d agg listo (total %.1f s)", size, time.perf_counter() - started)
    return found + agg, verdicts, await measure_bench_storage(admin, size, defs)


async def run(args: argparse.Namespace, env: dict) -> int:
    """Orquesta la corrida completa y escribe los informes; devuelve el código de salida (0 = correcto)."""
    admin = await connect_admin(env)
    api = await connect_api(env)
    try:
        defs = await read_index_definitions(api)
        reference = await read_real_reference(api)
        storage = await read_storage(admin, DATA_DIRS)
        seed = load_seed(Path("/app/data/historical"))
        catalog = parse_country_catalog(json.loads((DATA_DIRS["data/catalogo"] / CATALOG_FILE).read_text("utf-8")))
        before = await take_snapshot(admin)
        measurements, verdicts, bench_sizes = [], [], []
        async with bench_session(admin, args.sizes, args.clean):
            for size in args.sizes:
                found, judged, sized = await run_size(admin, size, seed.events, catalog, defs,
                                                      args.out / "planes", args)
                measurements, verdicts, bench_sizes = measurements + found, verdicts + judged, bench_sizes + [sized]
        after = await take_snapshot(admin)
        machine = read_machine(postgres_version=await admin.fetchval("SELECT version()"))
    finally:
        await api.close()
        await admin.close()
    problems = verify_isolation(before, after)
    write_reports(args, measurements, verdicts, bench_sizes, reference, storage, machine, (before, after, problems))
    LOG.info("terminado: %d mediciones, violaciones de aislamiento: %s", len(measurements), problems or "ninguna")
    return 1 if problems else 0


def write_reports(args, measurements, verdicts, bench_sizes, reference, storage, machine, isolation) -> None:
    """Escribe todos los archivos de resultados en `--out`."""
    args.out.mkdir(parents=True, exist_ok=True)
    params = {"sizes": args.sizes, "repeats": args.repeats, "budget_seconds": args.budget}
    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    routes = measure_transfer()
    per_visit = transfer.bytes_per_visit(routes) if routes else None
    files = {
        "resultados.json": json.dumps(report.build_results_json(params, run_at, measurements), indent=1,
                                      ensure_ascii=False),
        "tablas.md": report.render_tablas_md(measurements, params),
        "indices.md": report.render_indices_md(reference, verdicts, bench_sizes),
        "aislamiento.md": report.render_aislamiento_md(*isolation),
        "almacenamiento.md": render_storage_md(storage, bench_sizes),
        "equipo.md": render_equipo_md(machine),
        "transferencia.md": transfer.render_transfer_md(routes),
        "costes.md": costs.render_costs_md(costs.build_rows(storage.database_bytes, per_visit)),
    }
    for name, text in files.items():
        (args.out / name).write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada: configura el registro, valida y ejecuta; 0 correcto, 1 fallo, 2 abortado."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    if not confirm(args):
        LOG.info("cancelado por el usuario")
        return 2
    try:
        return asyncio.run(run(args, dict(os.environ)))
    except (BenchSchemaError, SeedError) as error:
        LOG.error("%s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
