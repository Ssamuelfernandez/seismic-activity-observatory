"""Arranque de la descarga del histórico: lee argumentos, configura y llama a `download.py` (B13, B15).

Uso: `python -m historical.download_main [--force] [--start AAAA-MM-DDThh:mm:ss --end ...]`.
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from historical.download import CountMismatchError, download_gap, download_year
from historical.fetch_interval import FetchTools, IntervalFetchError
from historical.intervals import Interval
from historical.manifest import Manifest
from producer.usgs_client import fetch_feed

logger = logging.getLogger("historical.download")

USGS_QUERY_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1"
DEFAULT_OUTPUT_DIR = "data/historical"
HTTP_TIMEOUT_SECONDS = 60
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
EXIT_OK = 0
EXIT_ERROR = 1


def _parse_utc(text: str) -> datetime:
    """Convierte `AAAA-MM-DDThh:mm:ss` en un instante UTC."""
    try:
        return datetime.strptime(text, DATE_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"fecha inválida '{text}', se espera AAAA-MM-DDThh:mm:ss") from error


def build_parser() -> argparse.ArgumentParser:
    """Define las opciones de la línea de comandos."""
    parser = argparse.ArgumentParser(prog="historical.download_main", description="Descarga el histórico 2025 de USGS.")
    parser.add_argument("--force", action="store_true", help="vuelve a pedir todo aunque los archivos sean válidos")
    parser.add_argument("--start", type=_parse_utc, help="inicio UTC de un hueco a recuperar (requiere --end)")
    parser.add_argument("--end", type=_parse_utc, help="fin UTC de un hueco a recuperar (requiere --start)")
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR), help="carpeta de salida")
    return parser


async def _real_fetch(url: str) -> bytes:
    """Petición real a USGS; devuelve el cuerpo."""
    return (await fetch_feed(url, HTTP_TIMEOUT_SECONDS)).body


def production_tools() -> FetchTools:
    """Herramientas con la red real y espera real."""
    return FetchTools(fetch=_real_fetch, base_url=USGS_QUERY_BASE_URL, sleep=asyncio.sleep)


def _log_summary(manifest: Manifest) -> None:
    """Resumen final por log."""
    totals = manifest.totals
    logger.info("download_summary files=%d gaps=%d unique=%d duplicates=%d usgs_count_year=%d",
                len(manifest.files), len(manifest.gaps), totals.unique, totals.duplicates_discarded,
                totals.usgs_count_year)


def main(argv: list[str] | None = None, tools: FetchTools | None = None) -> int:
    """Ejecuta la descarga y devuelve el código de salida (0 correcto, distinto de 0 si falla)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.start is None) != (args.end is None):
        parser.error("--start y --end deben indicarse juntos")
    tools = tools or production_tools()
    try:
        if args.start is not None:
            manifest = asyncio.run(download_gap(args.output_dir, Interval(args.start, args.end), tools))
        else:
            manifest = asyncio.run(download_year(args.output_dir, tools, force=args.force))
    except (IntervalFetchError, CountMismatchError, ValueError) as error:
        logger.error("download_failed %s: %s", type(error).__name__, error)
        return EXIT_ERROR
    _log_summary(manifest)
    return EXIT_OK


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    sys.exit(main())
