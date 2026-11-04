"""Espera creciente entre fallos consecutivos de USGS, con jitter (B10, SC-006). Puro, sin E/S."""
from dataclasses import dataclass

JITTER_MIN_FRACTION = 0.5
MAX_DOUBLINGS = 32


@dataclass(frozen=True)
class BackoffSettings:
    """Espera inicial y máxima del backoff, en segundos."""

    initial_seconds: float
    max_seconds: float


PRODUCTION_BACKOFF = BackoffSettings(initial_seconds=2, max_seconds=60)


def compute_backoff_seconds(failures: int, settings: BackoffSettings, jitter_fraction: float) -> float:
    """Calcula la espera tras el fallo número `failures`.

    Qué hace:
        Duplica la espera inicial en cada fallo hasta el máximo y la multiplica por un factor
        entre `JITTER_MIN_FRACTION` (jitter 0) y 1 (jitter 1).
    Recibe:
        failures: fallos consecutivos (0 = ninguno); settings: espera inicial y máxima;
        jitter_fraction: número en [0, 1] que se inyecta para que la prueba sea determinista.
    Devuelve:
        Segundos de espera; 0 si no hay fallos; nunca más de `settings.max_seconds`.
    Por qué existe:
        Evita golpear a USGS durante una caída y sincronizar reintentos (B10, FR-008).
    """
    if failures < 0:
        raise ValueError("failures no puede ser negativo.")
    if failures == 0:
        return 0
    doublings = min(failures - 1, MAX_DOUBLINGS)
    base = min(settings.max_seconds, settings.initial_seconds * 2 ** doublings)
    return base * (JITTER_MIN_FRACTION + (1 - JITTER_MIN_FRACTION) * jitter_fraction)
