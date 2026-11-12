# Modelo de datos: replay (009)

Sin tablas ni columnas nuevas: el esquema `replay` ya existe con las mismas tablas que `live` (`sql/001_schema.sql`, `db-schema.md`). Aquí solo se fijan las estructuras en memoria del replay y el contenido esperado.

## Estructuras en memoria (puras)

| Estructura | Campos | Dónde | Reglas |
|---|---|---|---|
| `Zone` | `name`, `lat_min`, `lat_max`, `lon_min`, `lon_max` | `producer/replay_selection.py` | Cajas de la tabla D4 de `research.md`; `ZONES` = `chile-norte` (por defecto) y `japon-honshu`. Una zona desconocida es un error de uso que lista las válidas |
| Selección | lista de `(feature, extracted_at)` ordenada | `producer/replay_selection.py` | Filtra por caja con `geometry.coordinates` (lon, lat); ordena por `(properties.time, id)`; ids únicos; primeros `count` |
| `ReplayItem` | `feature`, `is_synthetic`, `ingested_at` | `common/replay_message.py` | Un elemento a publicar; reales primero, luego el bloque controlado |
| Mensaje | el sobre de `kafka-message.md` §3 | `common/replay_message.py::build_replay_message(item, replay_at)` | `source = replay_demo`, `mode = replay`, `replay_at` no nulo |

## Contenido esperado en PostgreSQL (esquema vacío, un replay, N = 20)

| Tabla | Filas | Detalle |
|---|---|---|
| `replay.current_event` | 22 | 20 reales (`is_synthetic = false`) + `synthetic-replay-e1` (versión con `updated` 10:09) y `synthetic-replay-e2` (`is_synthetic = true`); `replay_at` no nulo y `source = replay_demo` en todas |
| `replay.event_version` | 24 | 20 + 3 de E1 + 1 de E2 |
| `replay.quarantine` | 0 | |
| `live.*` | sin cambios | Con el productor live parado |

Mensajes publicados: 26 (20 + 6). Decisiones del consumidor: 22 `new`, 1 versión posterior, 1 versión antigua tardía, 2 reenvíos ignorados.

## Bloque controlado (fabricado, `is_synthetic = true`)

| # | Evento | `updated` (UTC, 2025-01-30) | Magnitud | Resultado esperado |
|---|---|---|---|---|
| 1 | `synthetic-replay-e1` v1 | 10:05 | 4,2 | evento nuevo |
| 2 | `synthetic-replay-e1` v1 repetido | 10:05 | 4,2 | reenvío ignorado |
| 3 | `synthetic-replay-e1` v2 | 10:09 | 4,6 | versión posterior: sustituye la actual |
| 4 | `synthetic-replay-e1` v1 repetido tarde | 10:05 | 4,2 | reenvío ignorado |
| 5 | `synthetic-replay-e2` | 10:12 | 3,1 | evento nuevo |
| 6 | `synthetic-replay-e1` intermedia | 10:07 | 4,4 | versión antigua tardía: solo al historial |

`time` de E1 = 2025-01-30 12:00 UTC y de E2 = 12:30 UTC; coordenadas dentro de la caja `chile-norte`.

## Repetición del replay

Los 26 mensajes son reenvíos (mismo `id` y `updated`, contenido igual): los recuentos y el `replay_at` de las filas existentes no cambian (SC-006).

## Configuración

| Nombre | Dónde | Valor por defecto | Quién |
|---|---|---|---|
| `KAFKA_CONSUMER_TOPICS` | `.env.example`, `compose.yaml` (consumer) | `earthquakes.live,earthquakes.replay` | `common/config.py::load_consumer_topics` |
| `--interval`, `--zone`, `--count`, `--data-dir` | argumentos de `producer.replay` | `2`, `chile-norte`, `20`, `data/historical` | `producer/replay.py` |

Sin secretos. La variable se documenta en `.env.example` y en la sección de configuración del `README.md` (T047); `specs/002-infra-compose/contracts/config.md` no se edita. Se mantiene la validación contra `CONTRACT_TOPICS`.
