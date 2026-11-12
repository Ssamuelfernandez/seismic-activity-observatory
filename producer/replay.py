"""CLI del replay (`python -m producer.replay`): solo configura y arranca (J1, J8)."""
import argparse
import asyncio
import logging
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from common.config import KafkaSettings, load_log_level, load_retry_settings, read_str
from common.kafka_topics import TOPIC_REPLAY
from common.live_message import ISO_UTC_FORMAT
from common.logging_setup import configure_logging
from common.replay_message import ReplayItem, build_controlled_block
from producer.replay_runner import ReplaySummary, run_replay
from producer.replay_selection import DEFAULT_ZONE, ZONES, select_events
from producer.replay_source import ReplaySourceError, load_verified_features

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 2.0
DEFAULT_COUNT = 20
DEFAULT_DATA_DIR = "data/historical"
EXIT_OK = 0
EXIT_ERROR = 1


def build_parser() -> argparse.ArgumentParser:
    """Define los argumentos del CLI con los valores por defecto documentados."""
    parser = argparse.ArgumentParser(prog="python -m producer.replay", description="Replay de eventos reales de 2025.")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS,
                        help="segundos entre mensajes (por defecto 2)")
    parser.add_argument("--zone", default=DEFAULT_ZONE, help="zona: " + ", ".join(ZONES))
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="eventos reales a reproducir (por defecto 20)")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="carpeta con manifest.json y los archivos mensuales")
    return parser


def _parse_utc(text: str) -> datetime:
    """Convierte un texto UTC con `Z` en `datetime` con zona."""
    return datetime.strptime(text, ISO_UTC_FORMAT).replace(tzinfo=timezone.utc)


def build_items(selected: list[tuple[dict, str]], started_at: datetime) -> list[ReplayItem]:
    """Arma los elementos: los eventos reales seguidos del bloque controlado de 6 mensajes."""
    real = [ReplayItem(feature, False, _parse_utc(extracted_at)) for feature, extracted_at in selected]
    return real + build_controlled_block(started_at)


def format_summary(summary: ReplaySummary) -> str:
    """Texto final del replay con los recuentos."""
    return f"Publicados: {summary.total} ({summary.real} reales + {summary.block} del bloque controlado)"


def main(argv: list[str] | None = None, *, loader: Callable = load_verified_features,
         runner: Callable = run_replay) -> int:
    """Carga, selecciona, arma los elementos y los publica; devuelve el código de salida.

    Qué hace:
        Código 1 y mensaje claro si la zona es desconocida, un archivo falla o no hay eventos;
        si hay menos eventos que `--count`, informa del número real.
    Recibe:
        argv: argumentos (por defecto los de la línea de órdenes); loader y runner: inyectables.
    Devuelve:
        0 si se publicó todo, 1 si hubo un error de entrada.
    Por qué existe:
        Punto de entrada del replay (FR-002, FR-004, FR-017, FR-018).
    """
    args = build_parser().parse_args(argv)
    zone = ZONES.get(args.zone)
    if zone is None:
        logger.error("Zona desconocida: %s. Zonas disponibles: %s", args.zone, ", ".join(ZONES))
        return EXIT_ERROR
    try:
        pairs = loader(Path(args.data_dir))
    except ReplaySourceError as error:
        logger.error("No se puede leer el origen del replay: %s", error)
        return EXIT_ERROR
    selected = select_events(pairs, zone, args.count)
    if not selected:
        logger.error("No hay eventos en la zona %s; no se publica nada.", zone.name)
        return EXIT_ERROR
    if len(selected) < args.count:
        logger.warning("Solo hay %d eventos en %s (se pidieron %d).", len(selected), zone.name, args.count)
    items = build_items(selected, datetime.now(timezone.utc))
    settings = KafkaSettings(bootstrap_servers=read_str("KAFKA_BOOTSTRAP_SERVERS"), topic=TOPIC_REPLAY)
    summary = asyncio.run(runner(items, args.interval, settings, load_retry_settings()))
    logger.info(format_summary(summary))
    return EXIT_OK


if __name__ == "__main__":
    configure_logging(load_log_level())
    sys.exit(main())
