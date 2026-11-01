"""Exploración del feed de terremotos de USGS (fase F1).

Descarga una respuesta de `all_day.geojson` (o lee un archivo local con --file)
y muestra un informe: metadatos, tipos de evento, campos y nulos, rangos,
geometría, tiempos y ejemplos raros.

Por qué existe: antes de diseñar el modelo y las reglas de calidad hay que
ver cómo son los datos reales (B2). La salida es la evidencia de F1 y la
base del diccionario de datos.

Uso:
    python scripts/explore_usgs.py                      # descarga el feed
    python scripts/explore_usgs.py --file muestra.json  # analiza un archivo local
"""

import argparse
import hashlib
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
TIMEOUT_SECONDS = 15
RAW_DIR = Path("data/raw/explore")  # carpeta ignorada por Git
HEADERS_OF_INTEREST = ("Content-Type", "Content-Length", "Cache-Control", "Last-Modified", "Expires", "Age")


def emit(text: str = "") -> None:
    """Escribe una línea del informe (única salida del script)."""
    print(text)


def fetch_feed(url: str, timeout: int) -> tuple[bytes, dict]:
    """Descarga el feed y devuelve el cuerpo y los datos de la petición.

    Por qué existe: mide la latencia y guarda las cabeceras de caché,
    necesarias para documentar la frecuencia de actualización (B2).
    """
    request = Request(url, headers={"User-Agent": "observatorio-sismico-explore/0.1"})
    started = time.perf_counter()
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        info = {
            "status": response.status,
            "headers": {name: response.headers.get(name) for name in HEADERS_OF_INTEREST},
        }
    info["latency_ms"] = round((time.perf_counter() - started) * 1000)
    info["size_bytes"] = len(body)
    return body, info


def save_raw(body: bytes) -> Path:
    """Guarda la respuesta original con marca de tiempo y hash en el nombre."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(body).hexdigest()[:12]
    path = RAW_DIR / f"all_day_{stamp}_{digest}.geojson"
    path.write_bytes(body)
    return path


def ms_to_iso(value_ms: int) -> str:
    """Convierte milisegundos Unix a texto ISO 8601 en UTC."""
    return datetime.fromtimestamp(value_ms / 1000, tz=timezone.utc).isoformat()


def is_number(value) -> bool:
    """Indica si el valor es numérico (los booleanos no cuentan)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def report_request(info: dict | None, source: str) -> None:
    """Informe de la petición HTTP (latencia, tamaño, cabeceras)."""
    emit(f"== Origen: {source}")
    if info is None:
        emit("(archivo local: sin datos de petición)")
        return
    emit(f"HTTP {info['status']} | latencia {info['latency_ms']} ms | {info['size_bytes']} bytes")
    for name, value in info["headers"].items():
        emit(f"  {name}: {value}")


def report_metadata(data: dict) -> None:
    """Informe del bloque `metadata` y de claves de primer nivel."""
    emit()
    emit("== Estructura de primer nivel")
    emit(f"Claves: {list(data.keys())}")
    metadata = data.get("metadata", {})
    emit(f"metadata: {metadata}")
    generated = metadata.get("generated")
    if is_number(generated):
        emit(f"metadata.generated = {generated} ms -> {ms_to_iso(generated)}")


def report_types(features: list) -> None:
    """Informe de los valores de `properties.type` (qué no es terremoto)."""
    counts = Counter((f.get("properties") or {}).get("type") for f in features)
    emit()
    emit(f"== Tipos de evento ({len(features)} features)")
    for event_type, count in counts.most_common():
        emit(f"  {event_type!r}: {count}")


def report_fields(features: list) -> None:
    """Informe de cada campo de `properties`: nulos y tipos Python observados."""
    keys = sorted({key for f in features for key in (f.get("properties") or {})})
    emit()
    emit("== Campos de properties (no nulos / total, tipos observados)")
    for key in keys:
        values = [(f.get("properties") or {}).get(key) for f in features]
        non_null = [v for v in values if v is not None]
        types = sorted({type(v).__name__ for v in non_null})
        emit(f"  {key:<10} {len(non_null):>5}/{len(values):<5} {types}")


def describe_numbers(label: str, values: list) -> None:
    """Línea de resumen de una lista numérica (nulos, rango, negativos)."""
    numbers = [v for v in values if is_number(v)]
    nulls = sum(1 for v in values if v is None)
    if not numbers:
        emit(f"  {label}: sin valores numéricos (nulos: {nulls})")
        return
    negatives = sum(1 for v in numbers if v < 0)
    emit(f"  {label}: min {min(numbers)} | max {max(numbers)} | nulos {nulls} | negativos {negatives}")


def report_numeric(features: list) -> None:
    """Informe de rangos de magnitud, profundidad y otros numéricos."""
    emit()
    emit("== Rangos numéricos")
    props = [f.get("properties") or {} for f in features]
    for key in ("mag", "nst", "gap", "dmin", "rms", "sig"):
        describe_numbers(key, [p.get(key) for p in props])
    depths = [((f.get("geometry") or {}).get("coordinates") or [None] * 3)[2:3] for f in features]
    describe_numbers("depth (coordinates[2])", [d[0] if d else None for d in depths])
    emit(f"  magType: {dict(Counter(p.get('magType') for p in props))}")


def report_geometry(features: list) -> None:
    """Informe de la geometría: tipo, longitud de coordenadas y rangos."""
    emit()
    emit("== Geometría")
    geometries = [f.get("geometry") for f in features]
    emit(f"  geometry nula: {sum(1 for g in geometries if g is None)}")
    emit(f"  tipos: {dict(Counter((g or {}).get('type') for g in geometries))}")
    coords = [(g or {}).get("coordinates") for g in geometries]
    emit(f"  longitudes de coordinates: {dict(Counter(len(c) if c else 0 for c in coords))}")
    out_of_range = sum(1 for c in coords if c and len(c) >= 2 and not (-180 <= c[0] <= 180 and -90 <= c[1] <= 90))
    emit(f"  lon/lat fuera de rango: {out_of_range}")


def report_times(features: list) -> None:
    """Informe de `time` y `updated` (ms Unix) y del desfase entre ambos."""
    props = [f.get("properties") or {} for f in features]
    times = [p["time"] for p in props if is_number(p.get("time"))]
    lags = [(p["updated"] - p["time"]) / 60000 for p in props if is_number(p.get("time")) and is_number(p.get("updated"))]
    emit()
    emit("== Tiempos (ms Unix UTC)")
    if times:
        emit(f"  time: {ms_to_iso(min(times))} -> {ms_to_iso(max(times))}")
    if lags:
        emit(f"  updated - time (min): min {min(lags):.1f} | mediana {statistics.median(lags):.1f} | max {max(lags):.1f}")
        emit(f"  updated < time: {sum(1 for lag in lags if lag < 0)}")


def report_ids(features: list) -> None:
    """Informe de unicidad de `id` dentro de la respuesta."""
    ids = [f.get("id") for f in features]
    duplicated = [i for i, n in Counter(ids).items() if n > 1]
    emit()
    emit("== Identificadores")
    emit(f"  ids nulos: {sum(1 for i in ids if i is None)} | ids duplicados: {len(duplicated)}")
    emit(f"  ejemplos: {ids[:3]}")


def report_examples(features: list) -> None:
    """Muestra un feature de cada caso raro encontrado (para el diccionario)."""
    def first(predicate):
        return next((f for f in features if predicate(f.get("properties") or {}, f)), None)

    cases = {
        "mag nula": first(lambda p, f: p.get("mag") is None),
        "mag negativa": first(lambda p, f: is_number(p.get("mag")) and p["mag"] < 0),
        "profundidad negativa": first(lambda p, f: is_number(((f.get("geometry") or {}).get("coordinates") or [0, 0, 0])[2]) and f["geometry"]["coordinates"][2] < 0),
        "no es earthquake": first(lambda p, f: p.get("type") != "earthquake"),
    }
    emit()
    emit("== Ejemplos de casos raros")
    for label, feature in cases.items():
        emit(f"-- {label}: {'no aparece en esta respuesta' if feature is None else ''}")
        if feature is not None:
            emit(json.dumps(feature, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    """Lee los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(description="Explora una respuesta del feed de USGS.")
    parser.add_argument("--file", help="analiza un archivo local en vez de descargar")
    parser.add_argument("--url", default=FEED_URL, help="URL del feed (por defecto all_day)")
    return parser.parse_args()


def load_data(args: argparse.Namespace) -> tuple[dict, dict | None, str]:
    """Obtiene los datos (descarga o archivo local) y devuelve también su origen."""
    if args.file:
        return json.loads(Path(args.file).read_text(encoding="utf-8")), None, args.file
    body, info = fetch_feed(args.url, TIMEOUT_SECONDS)
    emit(f"Respuesta original guardada en: {save_raw(body)}")
    return json.loads(body), info, args.url


def main() -> int:
    """Punto de entrada: carga los datos y emite todos los informes."""
    args = parse_args()
    try:
        data, info, source = load_data(args)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        emit(f"ERROR al obtener o leer los datos: {error!r}")
        return 1
    features = data.get("features", [])
    report_request(info, source)
    report_metadata(data)
    report_types(features)
    report_fields(features)
    report_numeric(features)
    report_geometry(features)
    report_times(features)
    report_ids(features)
    report_examples(features)
    return 0


if __name__ == "__main__":
    sys.exit(main())
