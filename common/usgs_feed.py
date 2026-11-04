"""Validación del cuerpo del feed de USGS y hash canónico de sus eventos (B4, B5, B10). Puro, sin E/S."""
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class FeedFormatError(Exception):
    """El cuerpo de la respuesta no es un objeto JSON con una lista `features`."""


def parse_feed_body(raw: bytes) -> list[dict]:
    """Extrae la lista de eventos del cuerpo de la respuesta.

    Qué hace:
        Decodifica el JSON, exige un objeto con `features` como lista y descarta con un
        aviso los elementos que no son objetos.
    Recibe:
        raw: cuerpo tal como llegó.
    Devuelve:
        Lista de elementos de `features` (puede estar vacía: 0 eventos es válido).
    Por qué existe:
        Un cuerpo no válido es un fallo de USGS y no debe tocar el estado (FR-008, B10).
    Lanza:
        FeedFormatError con el motivo.
    """
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise FeedFormatError(f"el cuerpo no es JSON válido ({type(error).__name__})") from error
    if not isinstance(body, dict):
        raise FeedFormatError("el cuerpo no es un objeto JSON")
    if "features" not in body:
        raise FeedFormatError("falta el campo features")
    if not isinstance(body["features"], list):
        raise FeedFormatError("features no es una lista")
    return _keep_objects(body["features"])


def _keep_objects(features: list) -> list[dict]:
    """Conserva solo los elementos que son objetos JSON y avisa de los demás."""
    objects = [item for item in features if isinstance(item, dict)]
    dropped = len(features) - len(objects)
    if dropped:
        logger.warning("Se descartan %d elementos de features que no son objetos.", dropped)
    return objects


def hash_features(features: list[dict]) -> str:
    """Calcula el SHA-256 hexadecimal del contenido canónico de `features`.

    Qué hace:
        Serializa con claves ordenadas, sin espacios y sin escapar no ASCII.
    Recibe:
        features: lista de eventos ya validada.
    Devuelve:
        Cadena hexadecimal de 64 caracteres.
    Por qué existe:
        Detecta si dos respuestas tienen el mismo contenido aunque `metadata.generated`
        cambie cada minuto (db-schema.md §3.9, B5).
    """
    canonical = json.dumps(features, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
