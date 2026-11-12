# Guía de validación: replay (009)

Cómo comprobar la feature una vez implementada. Los contratos y el modelo no se repiten aquí: ver `kafka-message.md`, `db-schema.md`, `api.md` y `data-model.md`. Con `N = 20`.

## Requisitos previos

- `.env` copiado de `.env.example` y el stack levantado: `docker compose up --build -d` (reconstruye la imagen con el consumidor de dos topics).
- `data/historical/` íntegro (12 archivos mensuales y `manifest.json`).
- Esquema `replay` vacío (stack nuevo o volumen recreado: `docker compose down -v`; no hay borrado de tablas de replay).

## 1. Pruebas sin Docker y de integración

```
uv run pytest -m "not integration" tests/common/test_replay_message.py tests/producer
docker compose --profile test run --rm tests pytest -m integration tests/integration/test_replay_consumer.py
```

Esperado: todo en verde; la integración da 22 filas actuales, 24 versiones y 0 cuarentena.

## 2. Recuentos de `live` antes (productor live parado)

```
docker compose stop producer
```

Con el administrador (`docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>`), guardar la salida de:

```sql
SELECT 'current' AS t, count(*), md5(string_agg(c::text, '|' ORDER BY event_id)) FROM live.current_event c
UNION ALL SELECT 'version', count(*), md5(string_agg(v::text, '|' ORDER BY event_id, updated_ms)) FROM live.event_version v
UNION ALL SELECT 'quarantine', count(*), md5(string_agg(q::text, '|' ORDER BY id)) FROM live.quarantine q;
SELECT 'current' AS t, count(*) FROM replay.current_event
UNION ALL SELECT 'version', count(*) FROM replay.event_version
UNION ALL SELECT 'quarantine', count(*) FROM replay.quarantine;
```

Esperado: `replay` con 0, 0, 0.

## 3. Lanzar el replay

```
docker compose run --rm producer python -m producer.replay --interval 2 --zone chile-norte --count 20
```

Esperado: unos 52 s; la salida lista cada mensaje (clave y `replay_at`) y termina con «Publicados: 26 (20 reales + 6 del bloque controlado)». Un archivo alterado o ausente: salida con código 1 que nombra el archivo y nada publicado.

Esperar a que el consumidor termine (`docker compose logs consumer --tail 40`: 26 líneas `decision=…` con `topic=earthquakes.replay`).

## 4. Recuentos esperados

Repetir las consultas del paso 2.

| Comprobación | Esperado |
|---|---|
| `live.*` (recuentos y huella) | idéntico al paso 2 |
| `replay.current_event` | 22 |
| `replay.event_version` | 24 |
| `replay.quarantine` | 0 |
| Decisiones del consumidor (`COUNTERS` o líneas `decision=`) | 22 nuevos, 1 versión posterior, 1 antigua tardía, 2 reenvíos |
| E1 | `updated` 10:09 (la mayor), 3 versiones |
| `replay_at` | no nulo y `source = replay_demo` en las 22 filas; crece en el orden de publicación de los 20 reales |

## 5. Idempotencia (SC-006)

Repetir el paso 3 sin vaciar nada y las consultas de `replay`: mismos 22, 24 y 0, y los `replay_at` de las filas existentes no cambian.

## 6. API

```
curl -s "http://127.0.0.1:8000/api/eventos?mode=replay&start=2025-01-01&end=2026-01-01"
curl -s "http://127.0.0.1:8000/api/eventos"
curl -s "http://127.0.0.1:8000/api/estadisticas?mode=replay&start=2025-01-01&end=2026-01-01"
```

Esperado: `metadata.mode = "replay"` y `total = 22`; `time` de los 20 reales igual al del archivo de origen; `is_synthetic = true` solo en `synthetic-replay-*`; sin `mode`, `metadata.mode = "live"` y ningún evento de replay; en estadísticas `comparison` es `null`.

## 7. Panel (SC-005)

Con el panel en `config.mode = "api"` (frontend en el 4200): elegir «Reproducción»: banner «REPRODUCCIÓN» y 22 eventos; volver a «En vivo»: sin banner ni eventos de replay. Captura de ambos estados. Si los puntos se ven ilegibles por el atenuado por antigüedad, anotarlo (decisión provisional 5).

## 8. Restaurar

`docker compose start producer` (el productor live).

## Evidencias

Todo se guarda en `docs/evidencias/replay/` (salida del replay, SQL antes y después, respuestas de la API, captura del panel, notas de la comprobación).
