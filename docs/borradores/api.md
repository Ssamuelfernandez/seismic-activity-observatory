# Borrador: API de consulta (F1–F8, F10, F11)

Material para la memoria y la defensa. Cifras tomadas de `docs/evidencias/api/`; los datos de las pruebas son sintéticos (`synthetic-…`, `is_synthetic=true`), el recorrido con `curl` usa los datos reales cargados.

## Qué hace

API FastAPI de solo lectura (rol `observatory_api`) con tres rutas: `GET /api/eventos` (GeoJSON con `metadata`, filtros `start`/`end`/`min_mag`/`country_id`/`mode` y paginación por cursor), `GET /api/estadisticas` (por hora, por país, histogramas de magnitud y profundidad, comparación con 2025) y `GET /api/salud`. Lee `live.current_event` o `replay.current_event` según `mode`. El contrato es `specs/001-contratos-y-modelo/contracts/api.md`; no se ha modificado.

## Decisiones clave

- **Una transacción `REPEATABLE READ` de solo lectura por petición** (`api/db_access.py`): eventos, recuentos y los cinco bloques de estadísticas ven el mismo estado aunque el consumidor escriba entre medias, así `total` coincide con las sumas (F7).
- **Validación propia, sin 422**: los parámetros se validan a mano (`api/params.py`, puro) y todo error usa un único cuerpo `{"error": {"code", "message"}}` (`api/errors.py`), incluidos 404 y 405 del framework. Motivo: FastAPI devolvería `{"detail": …}` con 422 y el panel tendría dos formas de error. Sin `/docs` ni `/openapi.json` (F10).
- **Paginación por `(event_time, event_id)`** con cursor opaco (`api/cursor.py`): orden estable y desempate por id; una revisión de un evento no cambia su posición porque conserva `time` e `id`. `total` es siempre el real y `truncated` avisa de que hay más (F5).
- **`mode=replay` lee `replay.current_event`**, no un vacío fijo: hoy la tabla está vacía y el resultado es el intervalo vacío, y cuando exista la feature de replay no hay que reescribir la API. El esquema sale de una lista cerrada, nunca del cliente; los valores van como `$n`.
- **Estadísticas en SQL** (`api/stats_queries.py`, `width_bucket`, `generate_series` para las horas vacías); `api/stats_builder.py` solo arma la respuesta. El frontend no calcula nada (constitución §17).
- **Fallo de la base = 503 acotado**, nunca «0 eventos» (F8): el 503 tarda unos 4 s con la base parada (`fallo_bd_503.txt`) y la API se recupera sola.
- **Variables nuevas** `API_MAX_EVENTS` (5000) y `API_DB_TIMEOUT_SECONDS` (5, entre 1 y 9 para garantizar < 10 s), en `.env.example` y en el README; no se editó `config.md` de 002.

## Evidencias clave

- Pruebas finales (T025): 731 unitarias y 202 de integración sin fallos (`T025_unitarias.txt`, `T025_integracion.txt`).
- Coherencia contra SQL independiente con los datos reales: `n_2025=18302` igual a la cuenta directa (`coherencia_real.txt`).
- Recorrido real con `curl`: `recorrido_*.txt`. 503 real: `fallo_bd_503.txt`. Errores 404/405/400: `errores_404_405_400.txt`. Solo lectura y rutas: `bloque4_readonly.out`, `T025_rutas_protegidas_y_env.txt`.

## Cómo demostrarlo

```bash
docker compose up -d
curl http://127.0.0.1:8000/api/salud
curl "http://127.0.0.1:8000/api/eventos?min_mag=4&country_id=jpn&limit=20"
curl "http://127.0.0.1:8000/api/eventos?limit=10"            # usar next_cursor en &cursor=…
curl "http://127.0.0.1:8000/api/estadisticas?start=2025-01-01&end=2026-01-01"   # total == metadata.total de eventos
curl "http://127.0.0.1:8000/api/eventos?mode=replay"         # vacío hasta la feature de replay
curl -i "http://127.0.0.1:8000/api/eventos?min_mag=abc"      # 400 invalid_parameter, no 422
curl -i -X POST http://127.0.0.1:8000/api/eventos            # 405 con el cuerpo común
docker compose stop postgres && curl -i http://127.0.0.1:8000/api/eventos   # 503 database_unavailable
```

## Límites conocidos

- Sin CORS: `OPTIONS` responde 405 y el panel en otro origen no podrá consultar hasta la feature `despliegue` (F9).
- Un cursor reutilizado con otros filtros no se detecta; un cursor falsificado con `t` fuera de rango da 500 y con NUL en el id da 503.
- Los parámetros desconocidos se ignoran; un error SQL imprevisto sale como 503, no como 500.
- `by_hour` no tiene tope: un año completo son unas 8 760 entradas.
- Si PostgreSQL está parado al arrancar, la API reintenta y no atiende hasta que vuelva.
- F12 solo parcial (la API acepta `replay`); se completa con la feature de replay.
