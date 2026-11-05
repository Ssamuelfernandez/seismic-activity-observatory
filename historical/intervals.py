"""Intervalos de consulta a USGS y construcción de la URL. Puro, sin E/S (B13)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

MONTHS_PER_YEAR = 12
QUERY_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
MICROSECONDS_PER_MS = 1000
MIN_MAGNITUDE = 4
EVENT_TYPE = "earthquake"
ORDER_BY = "time-asc"
OUTPUT_FORMAT = "geojson"
KIND_QUERY = "query"
KIND_COUNT = "count"
QUERY_KINDS = (KIND_QUERY, KIND_COUNT)


@dataclass(frozen=True)
class Interval:
    """Intervalo semiabierto [start, end) en UTC."""

    start: datetime
    end: datetime


def month_intervals(year: int) -> list[Interval]:
    """Devuelve los 12 meses naturales UTC del año, contiguos.

    Qué hace:
        Cada intervalo empieza en el primer instante del mes y termina en el del siguiente.
    Recibe:
        year: año a descargar.
    Devuelve:
        Lista de 12 `Interval`; el último termina el 1 de enero del año siguiente.
    Por qué existe:
        Define las unidades de descarga y de archivo del histórico (B13, research D5).
    """
    starts = [datetime(year, month, 1, tzinfo=timezone.utc) for month in range(1, MONTHS_PER_YEAR + 1)]
    ends = starts[1:] + [datetime(year + 1, 1, 1, tzinfo=timezone.utc)]
    return [Interval(start, end) for start, end in zip(starts, ends)]


def split_interval(interval: Interval) -> tuple[Interval, Interval]:
    """Parte el intervalo por el punto medio (redondeado a ms) en dos mitades contiguas que lo cubren."""
    span_ms = (interval.end - interval.start) // timedelta(milliseconds=1)
    middle = interval.start + timedelta(milliseconds=span_ms // 2)
    return Interval(interval.start, middle), Interval(middle, interval.end)


def format_query_time(moment: datetime) -> str:
    """Formatea un instante para USGS; añade milisegundos solo si el instante los tiene."""
    text = moment.strftime(QUERY_TIME_FORMAT)
    if moment.microsecond:
        return f"{text}.{moment.microsecond // MICROSECONDS_PER_MS:03d}"
    return text


def build_query_url(interval: Interval, base: str, kind: str) -> str:
    """Construye la URL de USGS (`query` o `count`) con los parámetros del contrato.

    Qué hace:
        Añade magnitud mínima, tipo de evento, orden por tiempo y formato GeoJSON.
    Recibe:
        interval: tramo a consultar; base: URL base del servicio; kind: `query` o `count`.
    Devuelve:
        URL completa lista para pedir.
    Por qué existe:
        Una sola definición de los parámetros, que también se guardan en el manifiesto (B15).
    Lanza:
        ValueError si `kind` no es `query` ni `count`.
    """
    if kind not in QUERY_KINDS:
        raise ValueError(f"tipo de consulta desconocido: {kind}")
    params = {
        "format": OUTPUT_FORMAT,
        "starttime": format_query_time(interval.start),
        "endtime": format_query_time(interval.end),
        "minmagnitude": MIN_MAGNITUDE,
        "eventtype": EVENT_TYPE,
        "orderby": ORDER_BY,
    }
    return f"{base.rstrip('/')}/{kind}?{urlencode(params)}"
