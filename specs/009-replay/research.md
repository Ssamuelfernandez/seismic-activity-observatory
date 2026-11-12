# Investigación: replay (009)

Decisiones de diseño con sus alternativas. Cada una cita el requisito que la motiva. Las cinco «Preguntas para el alumno» de `spec.md` se adoptan con su decisión provisional (D1 a D4 y D9).

## D1. El consumidor lee los dos topics (pregunta 1)

- **Decisión**: un único consumidor suscrito a `earthquakes.live` y `earthquakes.replay`. Variable nueva `KAFKA_CONSUMER_TOPICS` (lista separada por comas, por defecto los dos topics del contrato). `ConsumerSettings` gana el campo `topics` y `start_consumer` se suscribe a todos. El esquema de destino ya sale del topic de cada mensaje (`common/kafka_topics.py::topic_mode`, usado por `consumer/pipeline.py`), así que **no cambia la lógica de proceso**.
- **Motivo** (J3, J5, FR-008): reutiliza el procesamiento y la comprobación `mode` ↔ topic; el grupo `consumer-live` conserva sus offsets de live y empieza el de replay desde el principio (`auto_offset_reset=earliest`).
- **Alternativas**: segunda instancia con `KAFKA_TOPIC=earthquakes.replay` y otro grupo (más pasos en la demo y un servicio más que operar, FR-020); suscribirse por constante sin variable (no cumple FR-017).
- **`KAFKA_TOPIC`** sigue existiendo para el productor live y para `KafkaSettings` del consumidor; el consumidor ya no lo usa para suscribirse (límite conocido, una línea en la tarea de config).
- **Validación de la variable**: cada nombre debe estar en `CONTRACT_TOPICS`; si no, `ConfigError` con el nombre.

## D2. Volumen de solo lectura en el servicio `producer` (pregunta 2)

- **Decisión**: `./data/historical:/app/data/historical:ro` en el servicio `producer` de `compose.yaml`. Sin servicio nuevo. El replay se lanza con `docker compose run --rm producer python -m producer.replay`.
- **Motivo** (FR-020): `data/historical/` (14 MB) no está en la imagen y el `Dockerfile` ya copia `common/`, `producer/` y `historical/`; **el `Dockerfile` no cambia**. Los datos no se meten en la imagen para no engordarla ni duplicarlos.
- **Alternativas**: `-v` en cada `run` (peor README); copiar los datos al `Dockerfile` (cambia la imagen compartida).

## D3. Velocidad: `--interval` en segundos (pregunta 3)

- **Decisión**: `--interval` (segundos entre mensajes, por defecto 2). El alumno actualiza el ejemplo `--speed 2` de `03 §8.5`; esta feature no edita `docs/planificacion/`.
- **Motivo** (FR-004): evita que `2` se lea como «el doble de rápido». Sin compresión proporcional del tiempo (límite conocido de la spec).
- **Argumentos y defaults** (todos con valor por defecto en constantes con nombre, sin variables de entorno nuevas salvo D1): `--interval 2`, `--zone chile-norte`, `--count 20`, `--data-dir data/historical`. Solo se usa `KAFKA_BOOTSTRAP_SERVERS` del entorno.

## D4. Zona y número por defecto (pregunta 4)

Se inspeccionó `data/historical/` (18 302 eventos únicos de 2025, M ≥ 4) con las mismas funciones de `common/geo.py` y el catálogo real de países.

| Zona candidata (caja lat/lon) | Eventos en la caja | Primeros 20 por `time`: países |
|---|---|---|
| **Chile norte** (lat −27 a −18, lon −72 a −68,5) | 267 | **CHL 18**, BOL 1, sin país 1 |
| Japón (lat 35 a 41, lon 139 a 142,5) | 194 | JPN 11, sin país 9 |
| México (lat 15 a 20, lon −102 a −96) | 29 | MEX 12, sin país 8 |

- **Decisión**: zona por defecto `chile-norte` y `N = 20`. Los 20 primeros eventos de la caja ordenados por `(time, id)` van del 2025-01-01 08:08 UTC al 2025-01-29 03:44 UTC, con M entre 4,0 y 6,1, ids únicos, sin empates de `time` y todos en `usgs_2025-01.geojson`. País reconocible (Chile) y un evento en Bolivia y otro sin país: enseña a la vez país por geometría y «Sin país asignado».
- **Segunda zona** `japon-honshu` (caja de la tabla) para demostrar que la zona es configurable. Con ella 9 de 20 caen en el mar; no es la de por defecto.
- **Motivo**: cumple «≥ 20 eventos M ≥ 4, país reconocible» (spec, Assumptions). El orden por `(time, id)` es determinista, así que el replay es repetible y `N = 20` se fija en este plan (SC-001: 26 mensajes, 22 filas actuales, 24 versiones).
- **Alternativa**: Turquía (14 TUR de 20) o Perú (11 PER); peor proporción.

## D5. Qué se reutiliza y qué es nuevo (J5, FR-009, FR-010)

| Pieza | Origen |
|---|---|
| Decodificar, validar, versión, transformar, país, escritor | **Sin cambios** (`common/`, `consumer/`) |
| Verificación sha256 y lectura de archivos | `historical/manifest.py` (`read_manifest`, `verify_file`), `historical/download_files.py::read_features` |
| Deduplicación por `id`/`updated` | `historical/dedup.py` |
| Clave del mensaje y formato de fecha | `common/live_message.py` (`message_key`, `ISO_UTC_FORMAT`) |
| Arranque con reintentos y publicación con ack | `producer/publisher.py` (`start_producer`, `publish_message`), `common/retry.py` |
| Temas | `common/kafka_topics.py` (`TOPIC_REPLAY`, `ensure_topics`) |
| **Nuevo, puro** | `common/replay_message.py`, `producer/replay_selection.py` |
| **Nuevo, con E/S** | `producer/replay_source.py` (archivos), `producer/replay_runner.py` (publicar con intervalo), `producer/replay.py` (CLI) |

El replay **no** llama a `process_record`: publica en Kafka y el consumidor procesa. Esa es la reutilización que pide J5 (el productor de replay entrega al consumidor, que usa `common/`).

## D6. Bloque controlado (J6, FR-012, FR-013)

- Eventos fabricados `synthetic-replay-e1` y `synthetic-replay-e2`, `is_synthetic = true`, dentro de la zona (lon −70,0; lat −22,0; profundidad 10 km), `time` el 2025-01-30 12:00 y 12:30 UTC (posterior a la selección y dentro de 2025), `place` «Sintético: …». Fechas y magnitudes son constantes con nombre en `common/replay_message.py`.
- E1: v1 `updated` = 10:05, v2 = 10:09 (M 4,6), intermedia = 10:07 (M 4,4), todas del 2025-01-30; E2 `updated` 10:12. Misma estructura de tiempos que la FAQ 12 de `tests/support/messages.py` (ahí hay otros ids: no se importa de `tests/`).
- Orden de publicación: E1 v1, E1 v1, E1 v2, E1 v1, E2, E1 intermedia. Resultado esperado: 2 reenvíos, 1 versión posterior, 1 versión antigua tardía (`kafka-message.md` §5).
- `ingested_at` de los sintéticos: instante de arranque del replay (FR-006).

## D7. Sobre del mensaje (FR-005, FR-006)

`source = replay_demo`; `mode = replay`; `replay_at` = instante UTC de publicación de cada mensaje (se lee el reloj justo antes de enviar; pasa como parámetro a la función pura); `ingested_at` = `extracted_at` del archivo en el manifiesto (reales) o arranque (sintéticos); `is_synthetic` según origen; `event` tal cual. `replay_at` crece con cada mensaje, lo que permite comprobar el orden (SC-004).

## D8. Aislamiento y comprobación de que live no cambia (SC-002)

El productor de replay solo conoce el topic `TOPIC_REPLAY` (constante en el runner, no sale de `KAFKA_TOPIC`, que en el servicio `producer` vale `earthquakes.live`). Prueba unitaria: con un publicador doble, todos los envíos van a `earthquakes.replay`. En la demo, `docker compose stop producer` (el productor live), huella de las tres tablas `live` (recuento y `md5` del texto de las filas ordenadas) antes y después. El consumidor sigue activo (necesario).

## D9. Panel (pregunta 5)

No se toca el panel. Ya pide el intervalo de 2025 y muestra el banner (`008`). Se verifica a mano con la API real; si los puntos de 2025 salen ilegibles por `fadeByAge`, se anota como hallazgo y se abre un cambio mínimo (desactivarlo solo en modo replay) como tarea condicional del último bloque.

## D10. Datos de entrada

Se verifican y leen los 12 archivos mensuales del manifiesto (14 MB, menos de 1 s); `usgs_gap_*.geojson` no se usa. Si falta un archivo o el sha256 no coincide, el proceso termina con código 1 antes de publicar y nombra el archivo (FR-001, FR-018). Si la zona no da eventos, error claro y sin publicar; si da menos que `--count`, se reproducen los que hay y se informa (edge cases).

## D11. Límites conocidos (una línea cada uno)

- El grupo del consumidor conserva el nombre `consumer-live` aunque ahora lee los dos topics; renombrarlo reprocesaría `live` entero.
- Una selección y un bloque controlado fijos: no hay modo aleatorio.
- El replay no se puede borrar (rol sin `DELETE`): repetir desde cero exige recrear el volumen de PostgreSQL.
- `KAFKA_TOPIC` queda sin uso para suscribirse en el consumidor.
- El bloque controlado tiene 6 mensajes (E1 v1, E1 v2, E1 intermedia tardía, reenvíos y E2) frente a los 5 de la FAQ 12: es una variante propia, no una copia.
- `specs/002-infra-compose/contracts/config.md` no refleja `KAFKA_CONSUMER_TOPICS`: la fuente es `.env.example` y el `README.md`.
