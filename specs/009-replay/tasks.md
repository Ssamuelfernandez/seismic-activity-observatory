# Tareas: replay (009)

**Entrada**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md` (esta carpeta). **IDs**: F9, J1 a J8, G10, F12, G12 (`metadata.mode`), prueba 11.

18 tareas activas en 5 bloques (máximo 25 y 5), numeradas **T041–T058** para continuar la numeración de `008`. Formato: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = en paralelo (archivos distintos). Cada tarea lleva **Prueba** y **Cubre**. Todo código nuevo sigue `03 §7.4` (docstrings en español con la plantilla, identificadores en inglés, funciones de unas 30 líneas, archivos de 250 como máximo, lógica pura separada del I/O). Sin fuzz, pruebas exhaustivas ni auditorías: una prueba por comportamiento que pida un criterio de la spec. Cualquier archivo de código nuevo se anota en `CODEMAP.md` en T058.

Notación: «sin Docker» = `uv run pytest -m "not integration" <ruta>`; «integración» = servicio `tests` (perfil `test`). Cada ejecución se guarda en `docs/evidencias/replay/T0##_*.txt`.

## Bloque 1 — Piezas puras y archivos de origen (J1, J2, J6, J7)

- [x] T041 [US1][US2] **Mensaje y bloque controlado**: `common/replay_message.py` con `SOURCE_REPLAY = "replay_demo"`, `MODE_REPLAY = "replay"`, `ReplayItem`, `build_replay_message(item, replay_at)` (sobre de `kafka-message.md` §3; `event` sin tocar) y `build_controlled_block(started_at)` con los 6 elementos de `data-model.md` (E1 v1, E1 v1, E1 v2, E1 v1, E2, E1 intermedia; ids `synthetic-replay-e1/e2`, `is_synthetic = true`, fechas de enero de 2025, `ingested_at` = `started_at`). Tests en `tests/common/test_replay_message.py`.
  - **Prueba (sin Docker)**: el mensaje de un evento real tiene `mode = replay`, `source = replay_demo`, `replay_at` no nulo con `Z` y el `event` idéntico al de entrada (`time` y `updated` intactos); el bloque tiene 6 elementos en el orden esperado, 2 ids distintos, el `updated` intermedio entre v1 y v2, todos sintéticos y con `time` dentro de 2025.
  - **Cubre**: J2, J6, J7; FR-005, FR-006, FR-010, FR-012, FR-013.

- [x] T042 [P] [US1] **Selección**: `producer/replay_selection.py` con `Zone`, `ZONES` (`chile-norte` por defecto y `japon-honshu`; cajas de `research.md` D4) y `select_events(pairs, zone, count)` sobre pares `(feature, extracted_at)` de T043 (filtra por caja con lon/lat, ordena por `(time, id)`, ids únicos, primeros `count`; con menos devuelve los que hay). Tests en `tests/producer/test_replay_selection.py`.
  - **Prueba (sin Docker)**: con features sintéticas de prueba, el orden es ascendente por `time`, las de fuera de la caja se descartan, los ids son únicos y `count` mayor que los disponibles devuelve los disponibles. Con los **archivos reales** de `data/historical/` y `chile-norte`/20: 20 eventos, primer `time` 2025-01-01 08:08 UTC y último 2025-01-29 03:44 UTC, ids únicos, M ≥ 4.
  - **Cubre**: J1; FR-002, FR-003, FR-010; SC-004 (orden).

- [x] T043 [US1] **Lectura verificada de los archivos**: `producer/replay_source.py` con `load_verified_features(directory)` (lee `manifest.json`, `verify_file` de cada archivo mensual, `read_features`, `dedup_features`, devuelve los eventos con el `extracted_at` de su archivo) y `ReplaySourceError` que nombra el archivo. Tests en `tests/producer/test_replay_source.py`.
  - **Prueba (sin Docker)**: con el directorio real devuelve 18 302 eventos únicos y `extracted_at` en formato `Z`; con una copia temporal a la que se altera un byte, o se quita un archivo, lanza `ReplaySourceError` con el nombre del archivo y no devuelve nada.
  - **Cubre**: J1, J7; FR-001, FR-006, FR-018 (parte de archivos).

## Bloque 2 — Publicación y CLI (J1, J3)

- [x] T044 [US1] **Publicador del replay**: `producer/replay_runner.py` con `run_replay(items, interval, settings, retry)`: `ensure_topics`, `start_producer`, publica cada elemento con `publish_message` **solo en `TOPIC_REPLAY`**, clave `event.id`, lee el reloj justo antes de cada envío para `replay_at`, espera `interval` entre mensajes (no tras el último), cierra el productor y devuelve el resumen (reales, bloque, total). Tests en `tests/producer/test_replay_runner.py` con dobles de Kafka y de reloj.
  - **Prueba (sin Docker)**: con 26 elementos el doble recibe 26 envíos, todos en `earthquakes.replay` y ninguno en `earthquakes.live`; `replay_at` estrictamente creciente; no se envía el siguiente antes de terminar el anterior; 25 esperas de `interval`; un fallo de Kafka reintenta como el productor live (A4, usando `common/retry.py`).
  - **Cubre**: J1, J3; FR-004, FR-005, FR-007, FR-018 (reintento).

- [x] T045 [US1] **CLI `producer.replay`**: `producer/replay.py` (`python -m producer.replay`) con `--interval` (2), `--zone` (`chile-norte`), `--count` (20), `--data-dir` (`data/historical`); solo configura y arranca: carga, selecciona, arma los 26 elementos con T041 a T043 y llama a T044; `KAFKA_BOOTSTRAP_SERVERS` del entorno. Código de salida 1 y mensaje claro si `ReplaySourceError`, zona desconocida o selección vacía; si hay menos eventos que `--count`, informa del número real. Tests en `tests/producer/test_replay_cli.py`.
  - **Prueba (sin Docker)**: con dobles, los valores por defecto son los documentados; zona desconocida y archivo alterado salen con código 1 y sin publicar; el resumen final dice «Publicados: 26 (20 reales + 6 del bloque controlado)».
  - **Cubre**: J1, J8 (cómo iniciar, velocidad); FR-002, FR-004, FR-017, FR-018; SC-007.

## Bloque 3 — Consumidor con dos topics, Compose y pruebas de integración (J3, J5, J6, F12)

- [x] T046 [US1] **Consumidor con dos topics**: `common/config.py::load_consumer_topics` (`KAFKA_CONSUMER_TOPICS`, lista por comas validada contra `CONTRACT_TOPICS`, `ConfigError` con el nombre si no), `ConsumerSettings.topics` en `consumer/loop.py` (suscripción y log de arranque), `consumer/main.py`; actualizar los dos `ConsumerSettings(...)` de `tests/consumer/test_consumer_loop.py`. Sin tocar `consumer/pipeline.py`.
  - **Prueba (sin Docker)**: tests de `load_consumer_topics` (por defecto, un solo topic, nombre inválido, vacío) en `tests/common/test_config_topics.py`; `uv run pytest -m "not integration" tests/consumer tests/common` sigue en verde; `git diff --stat` no muestra `consumer/pipeline.py`.
  - **Cubre**: J3, J5; FR-008, FR-009, FR-017.

- [x] T047 [P] [US1] **Compose y entorno**: `compose.yaml` (consumer: `KAFKA_CONSUMER_TOPICS: ${KAFKA_CONSUMER_TOPICS:-earthquakes.live,earthquakes.replay}`; producer: volumen `./data/historical:/app/data/historical:ro`; sin servicios nuevos), `.env.example` (variable nueva con comentario y defecto `earthquakes.live,earthquakes.replay`) y la sección de configuración del `README.md` (la variable se documenta ahí, como `API_MAX_EVENTS` en la feature api; `specs/002-infra-compose/contracts/config.md` no se edita). `Dockerfile` sin cambios.
  - **Prueba**: `docker compose config` sin errores y con 5 servicios más `tests`; `python scripts/check_env_example.py` sale con 0; `git diff --stat` solo muestra esos tres archivos.
  - **Cubre**: J3; FR-017, FR-020.

- [x] T048 [US1][US2] **Integración consumidor y esquema `replay`**: `tests/integration/test_replay_consumer.py` (arnés existente: PostgreSQL real, rol `observatory_consumer`, `process_record` con el tema `earthquakes.replay`) con los 20 eventos reales de `chile-norte` y el bloque controlado de T041.
  - **Prueba (integración)**: los 26 mensajes dan 22 filas en `replay.current_event`, 24 en `replay.event_version`, 0 en `replay.quarantine`, E1 con la versión de `updated` mayor, 2 reenvíos, 1 versión posterior y 1 antigua tardía; `replay_at` no nulo y `source = replay_demo` en todas; `live.*` sin filas nuevas; repetir los 26 deja los mismos recuentos y el mismo `replay_at`; un mensaje con `mode = live` en el topic de replay va a `replay.quarantine` con `mode_topic_mismatch`.
  - **Cubre**: J3, J5, J6; FR-008, FR-009, FR-011, FR-014; SC-001, SC-002, SC-004, SC-006; US1.4.

- [x] T049 [US3] **Integración API con replay**: ampliar `tests/integration/test_api_replay_events.py` (o un archivo nuevo si pasa de 250 líneas) con los 26 mensajes procesados como en T048.
  - **Prueba (integración)**: `mode=replay` con el intervalo de 2025 da `metadata.mode = "replay"` y `total = 22`; `time` de los 20 reales igual al del archivo; `is_synthetic` solo en `synthetic-replay-*`; sin `mode` o con `live`, ningún evento de replay; `/api/estadisticas?mode=replay` con `comparison = null`; esquema `replay` vacío devuelve lista vacía y no error.
  - **Cubre**: F12, J7; FR-015; SC-003; US3.1, US3.2, US3.3, US3.5.

## Bloque 4 — Documentación (J8)

- [x] T050 [P] [US4] **README**: sección «Replay» (selección por defecto y por qué, comando, `--interval`, aislamiento por topic + esquema + comprobación `mode` ↔ topic, cómo se ve el modo, recuentos esperados, repetición y límites conocidos de la spec y de `research.md` D11); corregir la frase del consumidor (ahora lee los dos topics) y la del límite de la API («vacío hasta la feature de replay»); fila de `replay` en la tabla de features.
  - **Prueba**: un enlace relativo por cada ruta citada (`ls` de todas ellas) y los comandos copiados de `quickstart.md`; `grep -n "solo el tema live" README.md` sin resultados.
  - **Cubre**: J8, J4; FR-019, FR-020; SC-007.

- [x] T051 [P] [US4] **Apuntes de memoria y defensa**: `docs/borradores/replay.md` (qué hace el replay, selección y su porqué, bloque controlado con la tabla de resultados, aislamiento, decisiones D1 a D9 resumidas, límites y preguntas de defensa). Los resultados observados se rellenan en T057.
  - **Prueba**: el archivo existe y cada ID de la cobertura (J1 a J8, G10, F12, G12) aparece al menos una vez.
  - **Cubre**: J8; FR-019.

## Bloque 5 — Recorrido de extremo a extremo con contenedores y panel, evidencia y cierre (todos los IDs; prueba 11)

- [x] T052 [US1] **Arranque limpio y «antes»**: `docker compose down -v`, `docker compose up --build -d`, esperar a sanos; `docker compose stop producer` (productor live); consultas SQL de `quickstart.md` §2 (recuentos y huella de `live`, recuentos de `replay` = 0). Salida en `docs/evidencias/replay/T052_antes.out`.
  - **Prueba**: `docker compose ps` con kafka, postgres, consumer y api sanos; `replay` con 0, 0, 0.
  - **Cubre**: SC-002 (línea base); prueba 11.

- [x] T053 [US1][US2] **Replay real y «después»** (precondición verificada en el código: el consumidor ya cuenta `redeliveries_ignored`, `newer_versions_applied` y `late_old_versions` en la línea `COUNTERS` de `consumer/reporting.py` y deja una línea `decision=` por mensaje; no hace falta contador nuevo. Si faltara alguna en el log, comprobar ese caso por consulta SQL y anotarlo como límite): `docker compose run --rm producer python -m producer.replay` (intervalo por defecto), medir la duración, esperar al consumidor y repetir las consultas de §2 y §4. Guardar la salida del replay (`T053_replay.log`), los logs del consumidor (`T053_consumer.log`) y el SQL (`T053_despues.out`).
  - **Prueba**: 26 mensajes publicados en menos de 90 s; `replay` con **22 / 24 / 0**; 2 reenvíos, 1 versión posterior y 1 antigua tardía en el log del consumidor; E1 con `updated` 10:09; `live.*` con los mismos recuentos y la misma huella que en T052; `replay_at` no nulo y `source = replay_demo` en todas las filas; `replay_at` crecientes para los 20 reales.
  - **Cubre**: J1, J2, J3, J5, J6; SC-001, SC-002, SC-004, SC-007; prueba 11.

- [x] T054 [US2] **Repetición idempotente y archivo alterado**: repetir `producer.replay` sin vaciar nada y comparar con T053; comprobar el error con un archivo alterado en una copia (`--data-dir` apuntando a una copia temporal con un byte cambiado, sin tocar `data/historical/`).
  - **Prueba**: mismos 22 / 24 / 0 y mismos `replay_at` de las filas existentes; con la copia alterada el proceso sale con código 1, nombra el archivo y no publica nada (recuento de `replay` sin cambios). Salida en `T054_*.out`.
  - **Cubre**: J6; FR-001, FR-018; SC-006.

- [x] T055 [US3] **API real**: las tres llamadas de `quickstart.md` §6 con `curl` contra el stack. Guardar las respuestas en `T055_*.json`.
  - **Prueba**: `metadata.mode = "replay"` y `total = 22`; `time` de los 20 reales igual al de los archivos (comparación con un script de una línea sobre `data/historical/`); sin `mode`, ningún evento de replay y `metadata.mode = "live"`; `comparison = null`.
  - **Cubre**: F12, J4, J7; SC-003.

- [x] T056 [US3] **Panel con banner**: con `frontend/public/config.json` en `mode: "api"` y el frontend en el 4200, elegir «Reproducción» y volver a «En vivo». Capturas `T056_reproduccion.png` y `T056_en_vivo.png`. Si los puntos de 2025 salen ilegibles por `fadeByAge`, aplicar el cambio mínimo (desactivarlo solo en modo replay) con su prueba de Vitest y anotarlo; si no, no se toca el panel.
  - **Prueba**: en «Reproducción» aparece el banner «REPRODUCCIÓN» y 22 eventos con sus fechas de 2025 (visible y legible); en «En vivo» no hay banner ni eventos de replay; el panel no calcula nada nuevo (`grep` de la diferencia, si la hay). Si el panel cambió: `npm test` y `npm run build` en 0.
  - **Cubre**: G10, G12 (`metadata.mode`), J4; FR-016; SC-005; US3.4.

- [x] T057 [US4] **Regresión y apuntes**: `docker compose start producer`; `uv run pytest -m "not integration"` completo, integración completa con el servicio `tests` (las pruebas existentes no se rompen), `python scripts/check_env_example.py` y `python scripts/verify_stack.py`. Rellenar los resultados observados en `docs/borradores/replay.md` y en la sección «Replay» del README (tiempos y recuentos reales).
  - **Prueba**: todo en verde y salidas guardadas en `T057_*.txt`; los recuentos del README coinciden con T053.
  - **Cubre**: J8; FR-019; SC-007; prueba 11.

- [x] T058 [US4] **Evidencia y `CODEMAP.md`**: `docs/evidencias/replay/README.md` con el índice de archivos y el veredicto de SC-001 a SC-007 (cada uno con su archivo); actualizar `CODEMAP.md` (filas nuevas: mensaje y bloque, selección, lectura verificada, publicador, CLI, consumidor con dos topics, pruebas y evidencias; línea de estado y fila en el historial de features cerradas) y marcar las tareas hechas aquí. Anotar en `bitacora.md` las preguntas del alumno aún abiertas. La feature se detiene aquí a la espera de revisión (constitución §19, sin commits).
  - **Prueba**: `ls` de todas las rutas citadas en `CODEMAP.md` y en el README de evidencias; los 5 archivos de código nuevos de `producer/` y `common/` aparecen en `CODEMAP.md`.
  - **Cubre**: constitución §16; FR-019, FR-020; SC-001 a SC-007.

## Dependencias

- Bloque 1: T041, T042 en paralelo; T043 independiente de ambas. Los tres antes del bloque 2.
- Bloque 2: T044 necesita T041; T045 necesita T041 a T044.
- Bloque 3: T046 y T047 independientes entre sí y del bloque 2; T048 necesita T041 y T046; T049 necesita T048.
- Bloque 4: T050 y T051 pueden hacerse tras el bloque 3 (T051 se completa en T057).
- Bloque 5: T052 necesita los bloques 1 a 3; T053 → T054 → T055 → T056 en orden (misma base de datos); T057 y T058 al final.

## Estrategia

MVP = bloques 1 a 3 (replay por Kafka, aislado y con recuentos exactos, comprobado con PostgreSQL real); el bloque 5 lo repite con contenedores y añade API y panel. Primero la prueba, después el código, y una tarea cada vez.

## Cobertura de IDs

| ID | Tareas |
|---|---|
| J1 | T041 a T045, T053 |
| J2 | T041, T053 |
| J3 | T044, T046 a T048, T053 |
| J4 | T050, T055, T056 |
| J5 | T046, T048, T053 |
| J6 | T041, T048, T053, T054 |
| J7 | T041, T043, T049, T055 |
| J8 | T045, T050, T051, T057 |
| G10 | T056 |
| F12 | T049, T055 |
| G12 (`metadata.mode`) | T056 |
| Prueba 11 | T052 a T054, T057 |
