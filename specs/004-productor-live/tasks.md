# Tasks: Productor en vivo

**Input**: `specs/004-productor-live/` (spec.md, plan.md, research.md, data-model.md, quickstart.md).

**Rama**: `004-productor-live`. **Estado**: ninguna tarea hecha. Sin commits ni merges (CLAUDE.md): al terminar T022 se detiene el trabajo y se espera la revisión del alumno. **22 tareas activas en 5 bloques** (tope 25 y 5).

**Cubre**: B1 a B12, A10; pruebas de aceptación 1 (real, hasta PostgreSQL) y 2 (reenvío); FR-001 a FR-014; SC-001 a SC-009.

**Alcance**: spec "Fuera de alcance". Sin fuzz, auditorías ni endurecimiento de casos raros. Los contratos de `specs/001-contratos-y-modelo/contracts/`, `sql/001_schema.sql` y `docs/enunciado/` no se tocan.

## Formato y criterios comunes

Cada tarea: `- [ ] T### [P?] [US?] Descripción con ruta`, con **Cubre** y **Criterio** (comando y resultado). `[P]` = paralelizable dentro del bloque. Historias: US1 evento real a PostgreSQL, US2 no duplicar, US3 fallos de USGS, US4 originales y filtro, US5 arranque y configuración.

Criterios comunes de toda tarea de código:

- **CC-DOC**: identificadores en inglés; docstrings y comentarios en español con la plantilla de `03-procedimiento-ejecucion.md` §7.4; type hints en funciones públicas; logging, no `print`; sin `except Exception: pass`.
- **CC-14** (§14): una función = una responsabilidad, <= ~30 líneas; archivo <= 250 líneas; sin números ni textos mágicos; lo puro no importa `asyncpg`, `aiokafka` ni `urllib`; el SQL vive en `producer/ingest_queries.py`.
- **CC-MAP**: la tarea que crea, mueve o elimina un archivo de código no toca `CODEMAP.md` (se actualiza en T021 en una sola pasada; desviación respecto al CLAUDE.md por proporcionalidad: se confirma con el alumno al revisar).

TDD: la prueba va antes que su implementación y "falla antes, pasa después". Tras cualquier cambio en `common/` o `producer/`, reconstruir la imagen de pruebas antes de ejecutar la integración: `docker compose --profile test build tests`.

Comandos de referencia: unitarias `uv run pytest -m "not integration" -q`; integración `docker compose up -d postgres`, `docker compose --profile test build tests`, `docker compose --profile test run --rm tests pytest -m integration -q`. Los criterios con `grep`/`wc` se ejecutan en Git Bash o con su equivalente en PowerShell.

## Bloque 1 — Configuración y funciones puras (sin red ni servicios)

**Objetivo**: toda la lógica de decisión, mensaje, hash y backoff, probada sin E/S.

- [ ] T001 [US5] Prueba y luego implementación de la configuración: en `tests/common/test_config.py` y `common/config.py` añadir `FeedSettings` y `load_feed_settings` (`POLL_SECONDS` por defecto 60, `USGS_FEED_URL` por defecto el `all_day.geojson`, `HTTP_TIMEOUT_SECONDS` 10, `RAW_RETENTION_DAYS` 7; rangos de `data-model.md` §5) y una función pura `validate_poll_against_health(poll_seconds, max_age_seconds)` que falla nombrando `POLL_SECONDS` si `poll_seconds * 2 > max_age_seconds`. Quitar `MIN/MAX_PRODUCER_INTERVAL_SECONDS`.
  - Cubre: B1, A10, FR-001, FR-010, spec US5.3.
  - Criterio: `uv run pytest tests/common/test_config.py -q` pasa; casos: valores por defecto, `POLL_SECONDS=61` con latido 120 falla con "POLL_SECONDS", URL sin esquema falla, `RAW_RETENTION_DAYS=0` falla; `common/config.py` <= 250 líneas.

- [ ] T002 [P] [US3] [US4] Prueba y luego implementación de `common/usgs_feed.py` y `tests/common/test_usgs_feed.py`: `parse_feed_body(raw: bytes) -> list[dict]` (lanza `FeedFormatError` con el motivo si no es JSON, no es objeto, falta `features` o no es lista; descarta con aviso elementos que no son objeto) y `hash_features(features) -> str` (JSON canónico `sort_keys`, `separators=(",", ":")`, `ensure_ascii=False`, SHA-256 hex de 64 caracteres).
  - Cubre: B4, B5, B10, FR-003, FR-008, FR-012, SC-007.
  - Criterio: `uv run pytest tests/common/test_usgs_feed.py -q` pasa; casos: JSON roto, `[]`, `{}` sin `features`, `features: []` válido (0 eventos), mismo contenido con distinto orden de claves y distinto `metadata.generated` da el mismo hash, un cambio en un `updated` da otro.

- [ ] T003 [P] [US1] [US2] [US4] Prueba y luego implementación de `common/ingest_decision.py` y `tests/common/test_ingest_decision.py`: `Decision` (`PUBLISH`, `PUBLISH_UNMARKED`, `SKIP`, `EXCLUDE`), `decide_publication(feature, last_updated_ms)` según la tabla de `research.md` §3 y `build_exclusion_row(feature, fetched_at)` según `data-model.md` §2.
  - Cubre: B3, B6, FR-004, FR-005, SC-002.
  - Criterio: `uv run pytest tests/common/test_ingest_decision.py -q` pasa; una prueba por fila de la tabla (nuevo; `updated` mayor; igual; menor; `type` distinto con `observed_type`; `type` ausente con `observed_type` nulo; sin `id` publicable sin marca; `updated` booleano o texto sin marca; invalidez prevalece sobre `type`).

- [ ] T004 [P] [US1] Prueba y luego implementación de `common/live_message.py` y `tests/common/test_live_message.py`: `build_live_message(feature, ingested_at)` y `message_key(feature)` (`id` o `None`). `ingested_at` en ISO 8601 UTC con `Z`.
  - Cubre: B7, B8, FR-006.
  - Criterio: `uv run pytest tests/common/test_live_message.py -q` pasa; el mensaje tiene exactamente `source=usgs_feed`, `mode=live`, `ingested_at`, `replay_at=null`, `is_synthetic=false` y `event` igual al elemento (con `mag` nulo y negativo intactos); clave nula si falta `id`. El mensaje del ejemplo de `kafka-message.md` §4 pasa por `common.decode`/`common.validation` del consumidor sin motivo de cuarentena.

- [ ] T005 [P] [US3] Prueba y luego implementación de `common/backoff.py` y `tests/common/test_backoff.py`: `BackoffSettings(initial_seconds, max_seconds)` y `compute_backoff_seconds(failures, settings, jitter_fraction)`; constantes con nombre `PRODUCTION_BACKOFF` (2 y 60) y `JITTER_MIN_FRACTION = 0.5`.
  - Cubre: B10, FR-008, SC-006.
  - Criterio: `uv run pytest tests/common/test_backoff.py -q` pasa; con `jitter_fraction` fijo en 1 la secuencia es 2, 4, 8, 16, 32, 60, 60; con 0 el factor es 0,5; ningún valor supera 60; fallos 0 devuelve 0.

## Bloque 2 — Entrada/salida: HTTP, PostgreSQL, permisos y variables

**Objetivo**: cliente HTTP, almacén en PostgreSQL con el rol real, permiso de purga y variables en `.env.example`/`compose.yaml`.

- [ ] T006 [US4] Permiso de purga: añadir en `sql/002_roles.sql` `GRANT SELECT, DELETE ON ingest.raw_response TO observatory_producer;` (actualizar el comentario del bloque del productor) y ampliar `tests/integration/test_roles.py` con una prueba del rol del productor (puede `DELETE` y `SELECT` en `raw_response`; no puede `UPDATE` ni tocar `current_event`). Añadir `producer()` a `tests/support/temp_database.py` y `DB_PRODUCER_PASSWORD` al servicio `tests` de `compose.yaml` (y al `conftest.py` de integración si lee el entorno).
  - Cubre: B5, FR-003, Preguntas 2 de la spec.
  - Criterio: `docker compose --profile test build tests` y `docker compose --profile test run --rm tests pytest tests/integration/test_roles.py -q` pasan. `git diff --stat -- specs/001-contratos-y-modelo sql/001_schema.sql` vacío.

- [ ] T007 [P] [US3] Cliente HTTP y servidor simulado: `producer/usgs_client.py` (`fetch_feed(url, timeout_seconds) -> FeedResponse`, lanza `FeedFetchError` con `status` o `None` y `latency_ms`; `urllib` en `asyncio.to_thread`) y `tests/support/mock_usgs.py` (`http.server` en un hilo, puerto 0; modos: cuerpo correcto, 500, 429, lento, no JSON; sus eventos llevan `id` `synthetic-…` y la cabecera de módulo lo declara). Pruebas en `tests/producer/test_usgs_client.py`.
  - Cubre: B1, B10, FR-001, FR-008, FR-014.
  - Criterio: `uv run pytest tests/producer/test_usgs_client.py -q` pasa: 200 devuelve cuerpo y latencia > 0; 500 y 429 lanzan `FeedFetchError` con ese `status`; respuesta lenta con timeout de 1 s lanza `FeedFetchError` con `status=None`; servidor apagado lanza `FeedFetchError`.

- [ ] T008 [US2] [US3] [US4] Almacén de ingesta: `producer/ingest_queries.py` (SQL) y `producer/ingest_store.py` con `last_ok_hash`, `record_success` (transacción: `raw_response` si el hash difiere + `ingest_run`), `record_failure`, `insert_exclusions` (`ON CONFLICT DO NOTHING` sin `RETURNING`), `load_state`, `mark_published` (`UPSERT` que solo avanza) y `purge_raw_responses` (conserva la más reciente). Pruebas de integración en `tests/integration/test_producer_store.py` con la base temporal y el rol `observatory_producer`.
  - Cubre: B3, B4, B5, B6, B9, FR-002, FR-003, FR-004, FR-007, SC-007.
  - Criterio: la integración pasa: dos `record_success` con el mismo hash dejan 2 filas en `ingest_run` y 1 en `raw_response`; una exclusión repetida deja 1 fila; `mark_published` con `updated` menor no retrocede; `purge_raw_responses` borra las de más de 7 días (fechas insertadas a mano con el administrador) y deja siempre la más reciente; `record_failure` con timeout deja `status` y `sha256` nulos.

- [ ] T009 [US5] Variables y comprobador: en `.env.example`, `compose.yaml` (servicio `producer`: sustituir `PRODUCER_INTERVAL_SECONDS` por las cuatro variables, con `${…:?mensaje}`) y `specs/002-infra-compose/contracts/config.md` (secciones A, D y E) reflejar `POLL_SECONDS`, `USGS_FEED_URL`, `HTTP_TIMEOUT_SECONDS` y `RAW_RETENTION_DAYS`. `scripts/check_env_example.py` solo cambia si no reconoce las nuevas.
  - Cubre: A10, FR-010, spec US5.2, SC-009.
  - Criterio: `python scripts/check_env_example.py` sale con 0; `docker compose config -q` sin errores; `grep -rn PRODUCER_INTERVAL_SECONDS .env.example compose.yaml common producer scripts` vacío (las referencias en `specs/` de `002`/`003` son históricas y se conservan salvo `config.md`).

## Bloque 3 — Ciclo, bucle, fallos y retirada de los sintéticos

**Objetivo**: el ciclo completo, el bucle con backoff y latido, y las pruebas de aceptación sin USGS real.

- [ ] T010 [US1] [US2] Prueba y luego implementación de `producer/cycle.py` (`run_cycle(deps, settings) -> CycleResult` según `plan.md` §1: orden fijo ack → marca) y `tests/producer/test_cycle.py` con dobles (cliente, almacén y publicador falsos, reloj fijo).
  - Cubre: B1, B3, B6, B7, B8, B9, FR-001, FR-005, FR-006, FR-007.
  - Criterio: `uv run pytest tests/producer/test_cycle.py -q` pasa: el publicador falso registra el orden de llamadas y `mark_published` nunca precede al ack; si el publicador falla en el 2.º evento, el 1.º queda marcado, el 2.º no, y el ciclo devuelve error de Kafka; clave del mensaje = `id`; todos los mensajes comparten `ingested_at`; los `type != earthquake` van a exclusiones y no al publicador.

- [ ] T011 [US3] [US5] Prueba y luego implementación de `producer/loop.py` y `producer/main.py`: bucle `ciclo → latido → espera` con backoff por fallos consecutivos, latido solo en ciclo correcto o fallo controlado de USGS, arranque con `check_database` y `start_producer` reintentando (A4), `ensure_topics`. Quitar de `loop.py` todo lo sintético. Pruebas en `tests/producer/test_loop.py` (reescribir las del productor mínimo).
  - Cubre: B1, B10, A10, FR-001, FR-008, FR-009, FR-011, SC-006, spec US5.1 y US5.3.
  - Criterio: `uv run pytest tests/producer/test_loop.py -q` pasa: 3 fallos de USGS seguidos piden esperas crecientes (con `jitter_fraction` fijo), un ciclo correcto reinicia el contador y espera `POLL_SECONDS`; el latido se renueva tras un fallo de USGS y no tras un fallo de Kafka; `main.py` con `POLL_SECONDS=61` falla nombrando la variable. `grep -rn synthetic producer/` vacío.

- [ ] T012 [US3] Prueba de integración de fallos con el mock: `tests/integration/test_producer_failures.py` (PostgreSQL real, mock de USGS, publicador falso, esperas de milisegundos). Para 500, 429, espera mayor que el timeout y JSON inválido (y cuerpo sin `features`): una fila de error en `ingest_run`, 0 mensajes y `ingest_state`, `raw_response` y `exclusion` idénticos antes y después; al volver el mock a responder bien, el siguiente ciclo publica.
  - Cubre: B10, FR-008, FR-014, SC-005, spec US3.1 a US3.4.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_producer_failures.py -q` pasa; la prueba compara las tres tablas antes y después mediante SQL.

- [ ] T013 [US1] [US2] Prueba de integración de ciclos, reinicio y reenvío: `tests/integration/test_producer_cycles.py`. (a) Primer ciclo publica N y segundo ciclo con la misma respuesta publica 0. (b) Reinicio = ciclo nuevo sobre la misma base: 0 mensajes. (c) Una revisión con `updated` mayor se publica; con menor o igual, no. (d) Corte entre ack y marca (el marcado falla una vez): el ciclo siguiente reenvía ese único mensaje; los dos mensajes pasan por la canalización del consumidor (`tests/support/db_helpers.py`, sin modificarla) y los recuentos de `current_event` y `event_version` no cambian.
  - Cubre: B6, B9, FR-005, FR-007, SC-002, SC-003, SC-004, pruebas 1 (parte productor) y 2.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_producer_cycles.py -q` pasa; la salida de pytest se guarda en T017.

- [ ] T014 [US1] Retirar los sintéticos del productor y adaptar A1: `scripts/verify_stack.py` (A1 comprueba una fila con `is_synthetic = false` y `source = 'usgs_feed'` en `live.current_event` tras el primer ciclo, en lugar de buscar `synthetic-…` en el log del consumidor) y `tests/scripts/test_verify_stack_a1.py`. `common/synthetic_event.py` se conserva.
  - Cubre: A1 (regresión), Preguntas 1 de la spec, constitución §7, FR-011.
  - Criterio: `uv run pytest tests/scripts/test_verify_stack_a1.py -q` pasa; `uv run pytest -m "not integration" -q` pasa completo; `grep -rn "synthetic_event" producer/` vacío.

## Bloque 4 — Documentación de la feature (B2, B5, B11, B12)

**Objetivo**: el texto que exigen los requisitos de documentación.

- [ ] T015 [P] [US4] Borrador de memoria `docs/borradores/productor-live.md`: B2 (estructura de la respuesta, tipos, unidades, opcionales, frecuencia de actualización, errores y latencia, apoyado en `scripts/explore_usgs.py` y `docs/evidencias/f1/explore_usgs_salida.txt`), B11 (un evento que sale de la ventana no está eliminado; la reconciliación exhaustiva es una ampliación) y B12 (hueco tras una parada de más de 24 h: recuperar con el catálogo histórico de USGS por intervalo de fechas y pasar los eventos por las mismas reglas; no automatizado). Citar fuentes, sin inventar cifras.
  - Cubre: B2, B11, B12, FR-013.
  - Criterio: el archivo existe con tres secciones tituladas B2, B11 y B12; cada cifra citada aparece en `explore_usgs_salida.txt`; no usa lenguaje de predicción ni de riesgo (§21).

- [ ] T016 [P] [US4] [US5] `README.md`: sección del productor (qué consulta, variables nuevas, cómo ver el log de ciclos, política de `raw_response`: hash sobre `features`, retención de 7 días configurable, purga al terminar cada ciclo correcto, estimación de ~150 KB por respuesta distinta, `ingest_run` no se purga; nota del `GRANT` para volúmenes existentes).
  - Cubre: B5, A10, FR-003, FR-010.
  - Criterio: `grep -n "RAW_RETENTION_DAYS\|POLL_SECONDS" README.md` encuentra ambas; la sección menciona los límites conocidos de `research.md` §10.

## Bloque 5 — Ejecución real, evidencias y cierre

**Objetivo**: demostrar las pruebas 1 y 2 con USGS real y el consumidor existente; cerrar la feature.

- [ ] T017 Ejecutar y guardar las pruebas: `uv run pytest -m "not integration" -q`, la integración (T006, T008, T012, T013) y `python scripts/check_env_example.py`; guardar las salidas en `docs/evidencias/productor-live/` (`pytest_unitarias.txt`, `pytest_integracion.txt`, `check_env.txt`).
  - Cubre: FR-014, SC-005, SC-006, SC-007, SC-009, constitución §16.
  - Criterio: los tres archivos existen y muestran 0 fallos.

- [ ] T018 [US1] Primera ejecución real: `docker compose build producer`, `docker compose up -d` (con `.env` válido y el `GRANT` aplicado según `quickstart.md` §0), esperar dos ciclos, guardar `docker compose logs producer` y las consultas de `quickstart.md` §2 puntos 2 y 6 con su resultado.
  - Cubre: B1, B3, B4, B5, B7, B8, FR-001, FR-002, SC-001, prueba 1 (primera parte).
  - Criterio: `docs/evidencias/productor-live/ciclo1.log` muestra `published=N`, `live.current_event` tiene N filas con `is_synthetic = false` (o la diferencia explicada), `ingest_run` tiene filas `status=200`, y `raw_response` tiene menos filas que consultas si hubo contenido repetido.

- [ ] T019 [US2] Segundo ciclo, parada y reinicio reales: guardar el log del segundo ciclo (`published` ≈ 0 y `skipped` ≈ N), ejecutar `docker compose kill producer` y `docker compose up -d producer`, y guardar el primer ciclo posterior.
  - Cubre: B6, B9, SC-002, SC-003, FR-005.
  - Criterio: `docs/evidencias/productor-live/reinicio.log` muestra `published` igual a 0 (o solo eventos con `updated` realmente mayor, comprobados por SQL) en el ciclo posterior al reinicio.

- [ ] T020 [US1] Evento nuevo real y reenvío (pruebas 1 y 2): esperar a un ciclo con `published` > 0, guardar el recuento de `live.current_event` y `event_version` antes y después, la fila nueva con su `event_id`, y el resultado de la prueba de reenvío de T013 como contraste.
  - Cubre: B6, B7, B8, SC-008, pruebas 1 (hasta PostgreSQL) y 2.
  - Criterio: `docs/evidencias/productor-live/prueba1_evento_nuevo.out` muestra una fila nueva con `is_synthetic = false` y `source = usgs_feed` dentro de 2 ciclos desde su aparición en el feed; `prueba2_reenvio.out` muestra recuentos idénticos antes y después. Si USGS no publica un evento nuevo en un tiempo razonable, anotar el intento y lo esperado en la evidencia y avisar al alumno (no inventar el resultado).

- [ ] T021 Cierre documental: `CODEMAP.md` (filas del productor real: `common/usgs_feed.py`, `ingest_decision.py`, `live_message.py`, `backoff.py`, `producer/{usgs_client,ingest_queries,ingest_store,cycle,loop,main}.py`, mock y pruebas, evidencias; reemplazar «productor mínimo» y los flujos «previstos» del productor; historial de features), marcar B1 a B12 y la prueba 1 (parte productor) en `docs/planificacion/01-checklist-requisitos.md` solo si la evidencia lo respalda, y actualizar el quickstart si algún comando cambió.
  - Cubre: constitución §16, CLAUDE.md.
  - Criterio: todo archivo de código nuevo de `common/`, `producer/` y `tests/` aparece en `CODEMAP.md` (`grep` de cada nombre); ninguna fila apunta a un archivo inexistente.

- [ ] T022 Revisión final y parada: ejecutar `uv run pytest -m "not integration" -q` y `python scripts/verify_stack.py`; guardar la salida en `docs/evidencias/productor-live/regresion_stack.txt`; comprobar que `git status` no muestra cambios en los contratos, `sql/001_schema.sql` ni `docs/enunciado/`; escribir en el chat el resumen y las preguntas abiertas y **detenerse** a esperar la revisión del alumno (sin commits ni merges).
  - Cubre: FR-014, constitución §16, §19.
  - Criterio: `git diff --stat -- specs/001-contratos-y-modelo sql/001_schema.sql docs/enunciado` vacío; regresión sin fallos.

## Dependencias

- Bloque 1 → Bloque 2 → Bloque 3 → Bloque 4 y 5. T002 a T005 son paralelas entre sí; T001 va antes de T011.
- T006 antes de T008 (permisos); T007 y T009 independientes de T008.
- T010 depende de T002 a T004 y T008; T011 de T005, T007 y T010; T012 y T013 de T010 y T011; T014 de T011.
- T015 y T016 son paralelas y pueden hacerse tras T011.
- Bloque 5: T017 → T018 → T019 → T020 → T021 → T022.

## Trazabilidad

| ID | Tareas |
|---|---|
| B1 | T001, T007, T010, T011, T018 |
| B2 | T015 |
| B3 | T003, T008, T010, T018 |
| B4 | T002, T008, T018 |
| B5 | T002, T006, T008, T016, T018 |
| B6 | T003, T008, T010, T013, T019, T020 |
| B7, B8 | T004, T010, T018, T020 |
| B9 | T008, T010, T013, T019 |
| B10 | T002, T005, T007, T011, T012 |
| B11, B12 | T015 |
| A10 | T001, T009, T011, T016 |
| Prueba 1 | T013, T018, T020 |
| Prueba 2 | T013, T020 |

## Estrategia

MVP = bloques 1 a 3 (productor probado con mock y PostgreSQL real). Los bloques 4 y 5 cierran requisitos de documentación y la ejecución real. Nada se implementa hasta que el alumno revise spec, plan y tareas.
