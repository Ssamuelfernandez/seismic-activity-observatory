"""Servidor simulado del feed de USGS para las pruebas (FR-014).

DATOS SINTÉTICOS: todos los eventos que sirve llevan `id` `synthetic-...` y no representan
sismos reales. Nunca deben llegar a una base de datos real. Escucha en el puerto 0 (libre) del
propio proceso de pruebas, en un hilo; no es un servicio de Compose ni publica puertos.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE_OK = "ok"
MODE_500 = "500"
MODE_429 = "429"
MODE_SLOW = "slow"
MODE_NOT_JSON = "not_json"
MODE_NO_FEATURES = "no_features"
SLOW_SECONDS = 3.0
LOCALHOST = "127.0.0.1"
SYNTHETIC_PREFIX = "synthetic-"


def synthetic_feature(number: int, updated: int = 1_000, event_type: str = "earthquake",
                      mag: float | None = 2.5) -> dict:
    """Elemento sintético del feed, con `id` `synthetic-<n>`."""
    return {
        "type": "Feature",
        "id": f"{SYNTHETIC_PREFIX}{number}",
        "properties": {"mag": mag, "place": "Lugar sintético", "time": 1_700_000_000_000 + number,
                       "updated": updated, "type": event_type},
        "geometry": {"type": "Point", "coordinates": [-100.0, 40.0, 10.0]},
    }


class MockUsgs:
    """Servidor HTTP en un hilo cuyo modo y eventos se cambian entre ciclos."""

    def __init__(self) -> None:
        self.mode = MODE_OK
        self.features: list[dict] = []
        self.requests = 0
        self._generated = 0
        self._server = ThreadingHTTPServer((LOCALHOST, 0), self._handler_class())
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        """Dirección del feed simulado."""
        return f"http://{LOCALHOST}:{self._server.server_address[1]}/feed.geojson"

    def start(self) -> "MockUsgs":
        """Arranca el servidor en su hilo."""
        self._thread.start()
        return self

    def stop(self) -> None:
        """Apaga el servidor y libera el puerto."""
        self._server.shutdown()
        self._server.server_close()

    def _body(self) -> bytes:
        """Cuerpo correcto; `metadata.generated` cambia en cada consulta como en USGS."""
        self._generated += 1
        return json.dumps({"type": "FeatureCollection", "metadata": {"generated": self._generated},
                           "features": self.features}).encode("utf-8")

    def _respond(self, handler: BaseHTTPRequestHandler) -> None:
        """Responde según el modo vigente."""
        self.requests += 1
        if self.mode in (MODE_500, MODE_429):
            handler.send_error(int(self.mode))
            return
        if self.mode == MODE_SLOW:
            time.sleep(SLOW_SECONDS)
        payloads = {MODE_NOT_JSON: b"<html>no es json</html>",
                    MODE_NO_FEATURES: b'{"type": "FeatureCollection"}'}
        body = payloads.get(self.mode) or self._body()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        try:
            handler.wfile.write(body)
        except OSError:
            pass  # el cliente ya cerró (timeout del lado del productor)

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        mock = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 (nombre fijado por http.server)
                mock._respond(self)

            def log_message(self, format: str, *args) -> None:  # silencia el log de http.server
                return

        return Handler
