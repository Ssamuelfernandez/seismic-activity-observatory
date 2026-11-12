"""Generador de filas SINTÉTICAS de `bench` a partir de la semilla real. Puro, determinista (K4, D9).

Sin E/S: recibe los eventos de la semilla y el localizador de país; devuelve filas listas para
`COPY`. Todas las filas llevan `is_synthetic = true`, id `synthetic-bench-<n>` y un `source` que
no es ninguno de los reales (constitución §7); ninguna cifra de `bench` es un dato sísmico.
"""
import math
import random
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from decimal import Decimal

RNG_SEED = 20251113
ID_PREFIX = "synthetic-bench-"
SOURCE = "synthetic_bench"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
YEAR_START_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
YEAR_END_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000) - 1
MAG_RANGE = (-10.0, 15.0)
DEPTH_RANGE = (-100.0, 1000.0)
LON_RANGE = (-180.0, 180.0)
LAT_RANGE = (-90.0, 90.0)
TIME_JITTER_MS = 30 * 24 * 3600 * 1000
COORD_JITTER_DEG = 0.5
MAG_JITTER = 0.3
DEPTH_JITTER_KM = 5.0
COLUMNS = ("event_id", "event_time", "event_time_ms", "updated_at", "updated_ms", "mag", "mag_type",
           "depth_km", "lon", "lat", "place", "status", "url", "sig", "country_id", "date_id",
           "source", "is_synthetic", "ingested_at", "replay_at")

Locator = Callable[[float, float], str | None]


def _number(value: object) -> float | None:
    """Devuelve el valor como real finito, o None si es nulo o no numérico."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def _in_range(value: float | None, bounds: tuple[float, float]) -> bool:
    """True si el valor es nulo (se conserva) o cae dentro de los límites."""
    return value is None or bounds[0] <= value <= bounds[1]


def _fields(feature: dict) -> dict | None:
    """Extrae y comprueba los campos de una feature de USGS; None si no es utilizable."""
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    event_id, time_ms, updated_ms = feature.get("id"), props.get("time"), props.get("updated")
    if not isinstance(event_id, str) or not isinstance(time_ms, int) or not isinstance(updated_ms, int):
        return None
    lon, lat = (_number(coords[i]) if len(coords) > i else None for i in (0, 1))
    depth = _number(coords[2]) if len(coords) > 2 else None
    mag = _number(props.get("mag"))
    if lon is None or lat is None or not (_in_range(lon, LON_RANGE) and _in_range(lat, LAT_RANGE)):
        return None
    if not (_in_range(mag, MAG_RANGE) and _in_range(depth, DEPTH_RANGE)):
        return None
    return {"id": event_id, "time_ms": time_ms, "updated_ms": updated_ms, "lon": lon, "lat": lat,
            "mag": mag, "depth": depth, "mag_type": props.get("magType"), "place": props.get("place"),
            "status": props.get("status"), "sig": props.get("sig")}


def _clamp(value: float, bounds: tuple[float, float]) -> float:
    """Acota un valor a los límites válidos."""
    return min(max(value, bounds[0]), bounds[1])


def _perturb(fields: dict, rng: random.Random) -> dict:
    """Copia los campos con tiempo, coordenadas, magnitud y profundidad perturbados en rango.

    Los nulos se conservan como nulos (constitución §5) y `updated >= time` se mantiene.
    """
    delay = max(0, fields["updated_ms"] - fields["time_ms"])
    time_ms = int(_clamp(fields["time_ms"] + rng.randint(-TIME_JITTER_MS, TIME_JITTER_MS),
                         (YEAR_START_MS, YEAR_END_MS)))
    mag, depth = fields["mag"], fields["depth"]
    return {**fields, "time_ms": time_ms, "updated_ms": time_ms + delay,
            "lon": _clamp(fields["lon"] + rng.uniform(-COORD_JITTER_DEG, COORD_JITTER_DEG), LON_RANGE),
            "lat": _clamp(fields["lat"] + rng.uniform(-COORD_JITTER_DEG, COORD_JITTER_DEG), LAT_RANGE),
            "mag": None if mag is None else round(_clamp(mag + rng.uniform(-MAG_JITTER, MAG_JITTER), MAG_RANGE), 2),
            "depth": None if depth is None else round(
                _clamp(depth + rng.uniform(-DEPTH_JITTER_KM, DEPTH_JITTER_KM), DEPTH_RANGE), 1)}


def _decimal(value: float | None) -> Decimal | None:
    """Convierte a `Decimal` por su texto (sin ruido binario); None se conserva."""
    return None if value is None else Decimal(str(value))


def _to_row(number: int, fields: dict, locate: Locator) -> dict:
    """Arma la fila completa de `bench.event_<N>` con tiempos y `date_id` derivados."""
    event_time = EPOCH + timedelta(milliseconds=fields["time_ms"])
    updated_at = EPOCH + timedelta(milliseconds=fields["updated_ms"])
    return {"event_id": f"{ID_PREFIX}{number}", "event_time": event_time, "event_time_ms": fields["time_ms"],
            "updated_at": updated_at, "updated_ms": fields["updated_ms"], "mag": _decimal(fields["mag"]),
            "mag_type": fields["mag_type"], "depth_km": _decimal(fields["depth"]), "lon": fields["lon"],
            "lat": fields["lat"], "place": fields["place"], "status": fields["status"], "url": None,
            "sig": fields["sig"], "country_id": locate(fields["lon"], fields["lat"]),
            "date_id": event_time.date(), "source": SOURCE, "is_synthetic": True,
            "ingested_at": updated_at, "replay_at": None}


def _pick(seed: list[dict], size: int, rng: random.Random) -> list[tuple[dict, bool]]:
    """Elige las filas de partida: submuestra ordenada o semilla completa más réplicas perturbadas."""
    if size <= len(seed):
        return [(seed[i], False) for i in sorted(rng.sample(range(len(seed)), size))]
    extra = [(seed[rng.randrange(len(seed))], True) for _ in range(size - len(seed))]
    return [(fields, False) for fields in seed] + extra


def build_rows(seed_events: list[dict], size: int, locate: Locator, rng_seed: int = RNG_SEED) -> list[dict]:
    """Construye `size` filas sintéticas deterministas a partir de la semilla real.

    Qué hace:
        Con `size` menor o igual que los eventos utilizables, submuestrea; con más, usa todos y
        añade réplicas perturbadas dentro de rangos válidos. Asigna el país con `locate`.
    Recibe:
        seed_events: features únicas de `load_seed`; size: filas pedidas; locate: función
        `(lon, lat) -> country_id | None`; rng_seed: semilla pseudoaleatoria (fija y registrada).
    Devuelve:
        Lista de `size` filas (diccionarios con las claves de `COLUMNS`), siempre las mismas
        para la misma semilla.
    Por qué existe:
        Permite medir con 1.000, 10.000 y 100.000 filas sin mezclar datos inventados con reales
        (K4, FR-013, FR-015, SC-004).
    """
    seed = sorted((f for f in map(_fields, seed_events) if f is not None), key=lambda f: f["id"])
    if size > 0 and not seed:
        raise ValueError("la semilla no tiene eventos utilizables")
    rng = random.Random(rng_seed)
    rows = []
    for number, (fields, replicate) in enumerate(_pick(seed, size, rng), start=1):
        rows.append(_to_row(number, _perturb(fields, rng) if replicate else fields, locate))
    return rows


def row_values(row: dict) -> tuple:
    """Valores de una fila en el orden de `COLUMNS` (el de `bench.event_<N>`), para `COPY`."""
    return tuple(row[column] for column in COLUMNS)
