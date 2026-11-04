# Data model: Productor en vivo

Las tablas y el mensaje están en los contratos (`db-schema.md` §3.6 a §3.9, `kafka-message.md` §3); aquí solo se indica **cómo las usa el productor** y qué estructuras en memoria maneja. No se redefine nada (constitución §15).

## 1. Qué escribe y qué lee el productor

| Tabla | Operación del productor | Cuándo | Permiso necesario |
|---|---|---|---|
| `ingest.ingest_run` | `INSERT` una fila por consulta; `SELECT sha256` de la última correcta | Pasos 2 y 3 del ciclo; también en cada fallo | `SELECT, INSERT` (ya concedido) |
| `ingest.raw_response` | `INSERT` si el hash difiere; `DELETE` de las de más de la retención (menos la más reciente) | Paso 3 y fin de ciclo | `INSERT` (ya) + **`SELECT, DELETE` (nuevo, `sql/002_roles.sql`)** |
| `live.exclusion` | `INSERT ... ON CONFLICT DO NOTHING` | Paso 4 | `INSERT` (ya) |
| `ingest.ingest_state` | `SELECT` de los `id` del ciclo; `UPSERT` tras cada ack | Pasos 5 y 6 | `SELECT, INSERT, UPDATE` (ya) |

`replay.exclusion` y el esquema `replay` no los toca esta feature.

## 2. Filas que construye

### `ingest_run`

| Caso | `status` | `latency_ms` | `event_count` | `sha256` | `error` |
|---|---|---|---|---|---|
| Correcta | 200 | ms medidos | `len(features)` (todos, incluidos los excluidos) | hash de `features` | `NULL` |
| HTTP 429 / 5xx | código | ms medidos | `NULL` | `NULL` | `HTTP 429` (texto corto) |
| Timeout o red (sin respuesta) | `NULL` | ms transcurridos | `NULL` | `NULL` | `timeout` / texto del error |
| Cuerpo no válido (JSON roto o sin `features`) | 200 | ms medidos | `NULL` | `NULL` | `invalid_body: <motivo>` |

Una fila es "consulta correcta" cuando `error IS NULL AND status = 200` (`db-schema.md` §3.8); los tres últimos casos nunca lo cumplen, así que no cuentan para `last_ingestion` ni como referencia del hash.

### `raw_response`

`fetched_at` = instante de recepción; `sha256` = el mismo de la fila de `ingest_run`; `body` = respuesta completa. Solo si el hash difiere del de la última consulta correcta.

### `exclusion`

| Columna | Valor |
|---|---|
| `event_id`, `updated_ms` | `id` y `updated` del elemento |
| `kind` | `non_earthquake_type` |
| `reason` | texto fijo: `properties.type distinto de earthquake` |
| `observed_type` | `properties.type` o `NULL` si falta |
| `fetched_at` | instante de recepción del ciclo |
| `is_synthetic` | `false` |

### `ingest_state`

`event_id`, `last_updated_ms` (el `updated` publicado), `published_at` (instante de la marca). El `UPSERT` solo avanza (`WHERE EXCLUDED.last_updated_ms > ingest_state.last_updated_ms`), así una marca tardía nunca retrocede el estado.

## 3. Estructuras en memoria (módulos puros de `common/`)

| Nombre | Módulo | Campos / valores | Para qué |
|---|---|---|---|
| `Decision` (enum) | `ingest_decision.py` | `PUBLISH`, `PUBLISH_UNMARKED`, `SKIP`, `EXCLUDE` | Resultado de `decide_publication` (tabla de research §3) |
| `FeedFormatError` | `usgs_feed.py` | excepción con el motivo | Cuerpo que no es JSON o no tiene `features` |
| `BackoffSettings` | `backoff.py` | `initial_seconds`, `max_seconds` | Parámetros del backoff; producción 2 y 60 |
| `FeedSettings` | `config.py` | `url`, `poll_seconds`, `timeout_seconds`, `raw_retention_days` | Configuración del productor |
| `FeedResponse` | `producer/usgs_client.py` | `status`, `body` (bytes), `latency_ms`, `received_at` | Resultado de una consulta correcta |
| `FeedFetchError` | `producer/usgs_client.py` | `status` o `None`, `message`, `latency_ms` | Fallo de HTTP, timeout o red |
| `CycleResult` | `producer/cycle.py` | `fetched`, `excluded`, `published`, `skipped`, `unmarked` | Línea de log del ciclo y pruebas |

## 4. Mensaje publicado

Construido por `build_live_message(feature, ingested_at)`: `source = "usgs_feed"`, `mode = "live"`, `ingested_at` (ISO 8601 UTC con `Z`, el instante de recepción del ciclo), `replay_at = null`, `is_synthetic = false`, `event` = el elemento de `features` sin modificar. Clave: `event.id` (nula si falta). Tema: `KAFKA_TOPIC` (`earthquakes.live`).

## 5. Variables de entorno nuevas

| Variable | Ejemplo | Validación | Quién la lee |
|---|---|---|---|
| `POLL_SECONDS` | `60` | entero 1 a `HEALTH_MAX_AGE_SECONDS / 2` (60); sustituye a `PRODUCER_INTERVAL_SECONDS` | `producer` |
| `USGS_FEED_URL` | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson` | texto no vacío, empieza por `https://` o `http://` | `producer` |
| `HTTP_TIMEOUT_SECONDS` | `10` | entero 1 a 60 | `producer` |
| `RAW_RETENTION_DAYS` | `7` | entero >= 1 | `producer` |

Van a `.env.example`, a `compose.yaml` (servicio `producer`) y a `specs/002-infra-compose/contracts/config.md` (sección A, D y E; `PRODUCER_INTERVAL_SECONDS` desaparece). `scripts/check_env_example.py` las verifica. No son secretos.

## 6. Línea de log por ciclo

Una línea `INFO` por ciclo (B1): `cycle=<n> status=<ok|fetch_error|kafka_error|db_error> http=<código|-> latency_ms=<n> fetched=<n> excluded=<n> published=<n> skipped=<n> unmarked=<n> next_wait_s=<n>`. Los errores llevan una línea `WARNING`/`ERROR` aparte con el motivo. Sirve de evidencia para "segundo ciclo ≈ 0" y "reinicio sin republicar".
