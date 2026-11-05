"""Doble de USGS para el descargador del histórico: responde `count` y `query` sin red.

DATOS SINTÉTICOS: todos los eventos llevan `id` `synthetic-<n>` y no son sismos reales.
"""
import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from tests.support.mock_usgs import SYNTHETIC_PREFIX

MAX_ALLOWED = 20_000
BASE_URL = "https://example.invalid/fdsnws/event/1"
YEAR_START = "2025-01-01T00:00:00"
YEAR_END = "2026-01-01T00:00:00"


def make_event(number: int, moment: datetime, updated: int = 1_000) -> dict:
    """Feature sintética con `id` `synthetic-<n>` situada en `moment`."""
    return {
        "type": "Feature",
        "id": f"{SYNTHETIC_PREFIX}{number}",
        "properties": {"mag": 4.5, "time": int(moment.timestamp() * 1000), "updated": updated,
                       "type": "earthquake"},
        "geometry": {"type": "Point", "coordinates": [-100.0, 40.0, 10.0]},
    }


def spread_events(start: datetime, end: datetime, total: int, first_number: int = 0) -> list[dict]:
    """`total` eventos repartidos de forma uniforme en [start, end)."""
    step = (end - start) / total
    return [make_event(first_number + index, start + step * index) for index in range(total)]


class FakeUsgs:
    """Sirve `count` y `query` sobre una lista fija de features ordenadas por tiempo."""

    def __init__(self, features: list[dict], count_override: int | None = None,
                 year_count: int | None = None) -> None:
        self.features = features
        self.count_override = count_override
        self.year_count = year_count
        self.urls: list[str] = []

    def _select(self, url: str) -> list[dict]:
        params = parse_qs(urlparse(url).query)
        start = datetime.fromisoformat(params["starttime"][0]).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(params["endtime"][0]).replace(tzinfo=timezone.utc)
        low, high = start.timestamp() * 1000, end.timestamp() * 1000
        return [item for item in self.features if low <= item["properties"]["time"] < high]

    async def fetch(self, url: str) -> bytes:
        """Equivale a `fetch_feed(url).body`: devuelve los bytes de la respuesta."""
        self.urls.append(url)
        selected = self._select(url)
        if urlparse(url).path.endswith("/count"):
            count = len(selected) if self.count_override is None else self.count_override
            params = parse_qs(urlparse(url).query)
            if self.year_count is not None and (params["starttime"][0], params["endtime"][0]) == (YEAR_START, YEAR_END):
                count = self.year_count
            return json.dumps({"count": count, "maxAllowed": MAX_ALLOWED}).encode()
        if len(selected) > MAX_ALLOWED:
            raise AssertionError("USGS rechazaría una consulta de más de 20000 resultados")
        body = {"type": "FeatureCollection", "metadata": {"count": len(selected)}, "features": selected}
        return json.dumps(body).encode()

    @property
    def request_count(self) -> int:
        """Número de peticiones recibidas."""
        return len(self.urls)
