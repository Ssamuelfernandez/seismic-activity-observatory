"""Verificación de punta a punta del consumidor idempotente con Kafka y PostgreSQL reales (T073).

Uso:
    python scripts/verify_consumer.py faq12 --yes        # FAQ 12, reenvíos y versión antigua (pruebas 2, 3, 4)
    python scripts/verify_consumer.py quarantine --yes   # cuarentena (prueba 6)
    python scripts/verify_consumer.py restart --yes      # corte entre commits y reinicio (prueba 8)

ATENCIÓN: cada escenario ejecuta `docker compose down -v`, que BORRA los volúmenes locales de Kafka y
de PostgreSQL de este proyecto (incluidos los datos que `002` haya dejado). Sin `--yes` (o sin
`VERIFY_CONSUMER_CONFIRM=yes`) el script avisa y termina con código 2 sin ejecutar nada destructivo.
Cada escenario guarda su salida en `docs/evidencias/consumidor-idempotente/`; el código de salida es 0
solo si todo coincide. Los datos son sintéticos (`is_synthetic = true`). `print` está permitido (CLI).
"""
import argparse
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# El script se ejecuta como `python scripts/verify_consumer.py`: se añade la raíz para importar `scripts.*`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.consumer_scenarios import faq12, quarantine, restart  # noqa: E402
from scripts.consumer_scenarios.helpers import CountersNotFound, confirm_destructive  # noqa: E402
from scripts.consumer_scenarios.report import Checks, say  # noqa: E402

EXIT_NOT_CONFIRMED = 2
SCENARIOS: dict[str, Callable[[Checks], None]] = {
    "faq12": faq12.run,
    "quarantine": quarantine.run,
    "restart": restart.run,
}
WARNING = (
    "AVISO: este escenario ejecuta `docker compose down -v` y BORRA los volúmenes locales de Kafka y de\n"
    "PostgreSQL de este proyecto, incluidos los datos que `002` haya dejado. No se ha ejecutado nada.\n"
    "Para continuar, repite el comando con --yes (o define VERIFY_CONSUMER_CONFIRM=yes)."
)


def build_parser() -> argparse.ArgumentParser:
    """Parser de línea de comandos con un subcomando por escenario."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subcommands = parser.add_subparsers(dest="scenario", required=True)
    for name, scenario in SCENARIOS.items():
        sub = subcommands.add_parser(name, help=(sys.modules[scenario.__module__].__doc__ or "").splitlines()[0])
        sub.add_argument("--yes", action="store_true", help="confirma el `down -v` (borra los volúmenes locales)")
    return parser


def describe_error(error: Exception) -> str:
    """Resumen corto de un fallo: comando (sin entorno) y final de su error estándar."""
    if isinstance(error, subprocess.CalledProcessError):
        return f"{' '.join(map(str, error.cmd[:6]))} -> código {error.returncode}: {(error.stderr or '')[-300:].strip()}"
    return str(error)


def main(argv: list[str] | None = None) -> int:
    """Pide confirmación, ejecuta el escenario elegido y devuelve el código de salida."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # consola cp1252 de Windows: nunca romper por un carácter
    args = build_parser().parse_args(argv)
    if not confirm_destructive(args, os.environ):
        say(WARNING)
        return EXIT_NOT_CONFIRMED
    checks = Checks()
    try:
        SCENARIOS[args.scenario](checks)
    except (subprocess.CalledProcessError, CountersNotFound) as error:
        checks.record(False, "El escenario se interrumpió", describe_error(error))
    failed = [name for passed, name in checks.results if not passed]
    say(f"\n{len(checks.results) - len(failed)}/{len(checks.results)} comprobaciones superadas.")
    return checks.exit_code()


if __name__ == "__main__":
    sys.exit(main())
