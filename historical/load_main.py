"""Arranque de la carga del histórico: configura, abre la base y llama a `loader.py` (B16, B17).

Uso: `python -m historical.load_main [--input-dir data/historical]`. Código de salida distinto
de 0 si falta un archivo, cambia un sha256 o la verificación `|U| - |Q|` no cuadra.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from common.config import DatabaseSettings, RetrySettings, load_database_settings, load_log_level
from common.config import load_retry_settings, read_str
from common.db import create_pool_with_retry
from common.geo import assign_country
from common.logging_setup import configure_logging
from consumer.catalog_loader import load_country_catalog
from consumer.pipeline import PipelineDeps, bind_pool_writers
from consumer.resilience import RetryControl
from consumer.schema_check import ensure_schema_ready
from historical.loader import LoadSummary, load_historical
from historical.manifest import ManifestFileError
from historical.verify import snapshot_fingerprint, verify_load

logger = logging.getLogger("historical.load")

DEFAULT_INPUT_DIR = "data/historical"
EXIT_OK = 0
EXIT_ERROR = 1


def build_parser() -> argparse.ArgumentParser:
    """Define las opciones de la línea de comandos."""
    parser = argparse.ArgumentParser(prog="historical.load_main", description="Carga el histórico en PostgreSQL.")
    parser.add_argument("--input-dir", type=Path, default=Path(DEFAULT_INPUT_DIR), help="carpeta con manifest.json")
    return parser


def _log_summary(summary: LoadSummary, ok: bool) -> None:
    """Resumen final por log (data-model §7)."""
    logger.info("historical_summary unique=%d new=%d newer=%d unchanged=%d late_old=%d quarantined=%d ok=%s",
                summary.unique, summary.new_event, summary.newer_version, summary.unchanged, summary.late_old,
                summary.quarantined, str(ok).lower())


async def _log_fingerprint(pool: Any) -> None:
    """Deja en el log la huella de las tres tablas, para comparar entre cargas."""
    for table, (count, digest) in (await snapshot_fingerprint(pool)).items():
        logger.info("fingerprint table=%s count=%d md5=%s", table, count, digest)


async def run_load(directory: Path, database: DatabaseSettings, retry: RetrySettings, catalog_path: str) -> bool:
    """Prepara la base, carga el histórico y verifica; devuelve si la verificación cuadra."""
    pool = await create_pool_with_retry(database, retry)
    try:
        await ensure_schema_ready(pool)
        index, _ = await load_country_catalog(pool, catalog_path)
        write_event, write_quarantine = bind_pool_writers(pool)
        deps = PipelineDeps(write_event, write_quarantine, RetryControl(retry, asyncio.Event()),
                            lambda lon, lat: assign_country(index, lon, lat))
        summary = await load_historical(directory, deps)
        result = await verify_load(pool, summary.event_ids, summary.quarantined_ids)
        logger.info("verify %s", result.message)
        _log_summary(summary, result.ok)
        await _log_fingerprint(pool)
        return result.ok
    finally:
        await pool.close()


def main(argv: list[str] | None = None) -> int:
    """Ejecuta la carga y devuelve el código de salida."""
    args = build_parser().parse_args(argv)
    configure_logging(load_log_level())
    try:
        ok = asyncio.run(run_load(args.input_dir, load_database_settings(), load_retry_settings(),
                                  read_str("COUNTRY_CATALOG_PATH")))
    except ManifestFileError as error:
        logger.error("historical_load_failed %s", error)
        return EXIT_ERROR
    return EXIT_OK if ok else EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
