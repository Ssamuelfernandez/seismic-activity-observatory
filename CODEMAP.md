# Mapa del código

Estado: features `contratos-y-modelo` (2026-11-02) e `infra-compose` (2026-11-04) cerradas; `consumidor-idempotente` y `productor-live` (2026-11-05) implementadas y verificadas, pendientes de la revisión del alumno: existen los contratos, el DDL, el modelo de datos, el stack de Compose con API **mínima**, el consumidor idempotente, el productor que consulta USGS en vivo y sus evidencias. Las filas de estas features son rutas reales; las que citan `api/routers/events.py` y `frontend/` son **previstas** y se confirman al cerrar cada feature.

## Dónde está cada cosa
| Quiero entender… | Mira… | Requisito |
|---|---|---|
| Cómo se explora el feed de USGS | scripts/explore_usgs.py | B2 |
| Qué mensaje viaja por Kafka y qué motivos de cuarentena existen | specs/001-contratos-y-modelo/contracts/kafka-message.md | C4 |
| Qué tablas e índices tiene la base y por qué | specs/001-contratos-y-modelo/contracts/db-schema.md | E2, E3, E7 |
| Qué contrato tiene la API con el panel | specs/001-contratos-y-modelo/contracts/api.md | F1–F3 |
| El DDL del esquema (`public`, `live`, `replay`, `ingest`) | sql/001_schema.sql | E5 |
| Los modelos conceptual, lógico y físico | specs/001-contratos-y-modelo/data-model.md (borrador); docs/memoria.md §5 | E1, E4 |
| Las pruebas del esquema en PostgreSQL 16 y la revisión de la API | docs/evidencias/contratos-y-modelo/ | E5, SC-005 |
| Cómo se levantan, comprueban y reinician los cinco servicios | compose.yaml; README.md (sección «Ejecución con Docker Compose»); specs/002-infra-compose/quickstart.md | A1, A2, A8, A9, A12 |
| Qué imagen Python usan productor, consumidor y API y cómo se fijan las versiones | Dockerfile, pyproject.toml, uv.lock, .python-version, .dockerignore | A3, A11 |
| Qué variables de entorno hay y cuáles lee el código | .env.example; specs/002-infra-compose/contracts/config.md; common/config.py; scripts/check_env_example.py | A10 |
| Cómo se reintenta la conexión a Kafka y PostgreSQL | common/retry.py, common/db.py | A4 |
| Cómo se calcula la salud de productor y consumidor (latido) y los umbrales | common/health.py; consumer/loop.py::broker_reachable; specs/002-infra-compose/contracts/config.md §E | A4 |
| Cómo se crean los temas y su retención de 7 días | common/kafka_topics.py; compose.yaml (broker); README.md (sección «Retención de Kafka») | A6 |
| El evento sintético de prueba (`is_synthetic = true`; el productor ya no lo usa, se conserva para pruebas del consumidor) | common/synthetic_event.py | C13 |
| El productor en vivo: arranque (`main.py`), bucle ciclo → latido → espera con backoff (`loop.py`) y publicación con ack (`publisher.py`) | producer/ (`main.py`, `loop.py`, `publisher.py`) | B1, B10, A4, A10 |
| Un ciclo del productor (consultar, guardar original, filtrar, decidir, publicar, marcar tras el ack) | producer/cycle.py (`run_cycle`) | B1, B3, B6, B7, B8, B9 |
| La consulta HTTP al feed de USGS y sus errores (timeout, 429, 5xx) | producer/usgs_client.py (`fetch_feed`, `FeedFetchError`) | B1, B10 |
| El almacén de ingesta en PostgreSQL (originales, ejecuciones, exclusiones, estado persistente, purga) y su SQL | producer/ingest_store.py, producer/ingest_queries.py | B3, B4, B5, B6, B9 |
| Cómo se interpreta la respuesta y se calcula su hash (`parse_feed_body`, `hash_features`) | common/usgs_feed.py | B4, B5, B10 |
| Qué se publica, se omite o se excluye (`id` + `updated`, motivo de exclusión) | common/ingest_decision.py | B3, B6 |
| Cómo se arma el mensaje live y su clave Kafka | common/live_message.py | B7, B8 |
| El backoff progresivo con jitter tras fallos de USGS | common/backoff.py | B10 |
| La política de `raw_response` (hash, retención, purga) y las variables nuevas del productor | README.md (sección del productor); common/config.py (`FeedSettings`, `load_feed_settings`, `validate_poll_against_health`); specs/002-infra-compose/contracts/config.md | B5, A10 |
| Las pruebas unitarias del productor (funciones puras, cliente contra el mock, ciclo con dobles, bucle) | tests/common/ (`test_usgs_feed.py`, `test_ingest_decision.py`, `test_live_message.py`, `test_backoff.py`); tests/producer/ (`test_usgs_client.py`, `test_cycle.py`, `test_loop.py`) | B1–B10 |
| El servidor USGS simulado (SINTÉTICO: ids `synthetic-…`) y el arnés del productor para integración | tests/support/mock_usgs.py, tests/support/producer_harness.py | B10 |
| Las pruebas de integración del productor (almacén y permisos, ciclos/reinicio/reenvío, fallos 500/429/timeout/JSON) | tests/integration/ (`test_producer_store.py`, `test_producer_cycles.py`, `test_producer_failures.py`) | B3–B6, B9, B10, prueba 2 |
| Los apuntes de memoria del productor (B2, B11, B12) | docs/borradores/productor-live.md | B2, B11, B12 |
| La spec, el plan, la investigación y las tareas del productor en vivo | specs/004-productor-live/ | B1–B12 |
| Las evidencias del productor (pytest, ejecución real contra USGS, reinicio, evento nuevo, reenvío, regresión) | docs/evidencias/productor-live/ | B1–B12, pruebas 1 y 2 |
| Los informes del verificador de los bloques 1 a 3 del productor | docs/evidencias/subagentes/verificador-productor-live-bloque{1,2,3}.md; plan-reviewer-productor-live.md | — |
| El consumidor idempotente: arranque, señales de parada y gancho de prueba | consumer/main.py | C2, FR-023, FR-027 |
| El bucle (un mensaje por vuelta: escritura, línea de decisión, commit del offset, contadores; latido y sondeo del broker) | consumer/loop.py (`consume_until_stopped`, `process_and_commit`, `broker_reachable`) | C2, FR-001, FR-029 |
| Procesar un mensaje (decodificar, validar, transformar, escribir, cuarentena; `db_constraint_violation`) | consumer/pipeline.py (`process_record`, `bind_pool_writers`) | C1, C2, C5 |
| Reintentos sin límite de la base y del commit del offset, y la parada limpia | consumer/resilience.py (`retry_db_operation`, `commit_offset_with_retry`) | C2, FR-014, FR-029 |
| La línea de decisión por mensaje y el volcado de contadores (`COUNTERS`) | consumer/reporting.py | C1, C8, FR-003 |
| Los contadores de transformaciones y sus identidades | consumer/counters.py | C8, FR-023, FR-036 |
| El gancho que corta el proceso entre ambos commits (prueba 8) | consumer/fault_hook.py | C2, SC-005 |
| La API mínima (`GET /api/salud`) | api/ (`main.py`, `queries.py`, `routers/health.py`) | A1, A9 |
| Los roles de base de datos y sus permisos | sql/002_roles.sql; specs/002-infra-compose/data-model.md | E5 (db-schema.md §1.1) |
| Cómo se inicializa PostgreSQL (esquema y roles) la primera vez | scripts/postgres_init.sh | A5 |
| Cómo se ejecutan las pruebas de integración (servicio `tests`, perfil `test`, etapa `test` del `Dockerfile`) y la evidencia del bloque 1 | compose.yaml (servicio `tests`; monta `tests/`, `sql/` y `scripts/` en solo lectura, este último para que `tests/scripts/` importe `scripts`); Dockerfile (etapa `test`); pyproject.toml (marcador `integration`); docs/evidencias/consumidor-idempotente/ | FR-033 |
| Las pruebas unitarias | tests/ (`common/`, `producer/`, `consumer/`); `uv run pytest -m "not integration"` | A4, A10 |
| Las pruebas unitarias del procesamiento (puro, sin E/S): decodificar, validar, transformar, versión, cuarentena, temas | tests/common/ (`test_decode.py`, `test_storable.py`, `test_validation.py`, `test_transform.py`, `test_processing.py`, `test_records.py`, `test_quarantine_row.py`, `test_kafka_topics.py`) | C1–C8 |
| Las pruebas unitarias del consumidor (bucle, canalización, reintentos, contadores, línea de decisión, gancho, SQL, errores de base, estado inconsistente) | tests/consumer/ (`test_consumer_loop.py`, `test_pipeline.py`, `test_resilience.py`, `test_counters.py`, `test_reporting.py`, `test_fault_hook.py`, `test_queries.py`, `test_db_errors.py`, `test_writer_inconsistent.py`); tests/support/`__init__.py` y scripts/consumer_scenarios/`__init__.py` son marcadores de paquete | C1–C8 |
| Las pruebas de integración del bucle (corte tras el commit de PostgreSQL y reinicio; contadores contra SQL) y su arnés de Kafka simulado | tests/integration/test_restart_crash.py, tests/integration/test_counters_reconcile.py; tests/support/loop_harness.py | C2, C8, SC-005, SC-009 |
| La evidencia del bloque 4 (pytest unitario e integración, TDD, corte simulado, contadores) | docs/evidencias/consumidor-idempotente/ (`pytest_*_bloque4.txt`, `bloque4_*`) | FR-034 |
| La verificación de punta a punta del stack (A1 reconoce la línea `decision=… event_id=synthetic-…`) | scripts/verify_stack.py; nota de regresión en docs/evidencias/consumidor-idempotente/regresion_002.txt | A1–A12 |
| La verificación del consumidor con Kafka y PostgreSQL reales (`faq12`, `quarantine`, `restart`; `down -v` solo con `--yes`) | scripts/verify_consumer.py (CLI); scripts/consumer_scenarios/ (`helpers.py` auxiliares puros, `stack.py` Docker/SQL/Kafka, `report.py` comprobaciones y evidencias, `faq12.py`, `quarantine.py`, `restart.py`, `geo.py` (escenario `geo`: catálogo de 177 países y país por geometría con Kafka real; evidencia en docs/evidencias/geografia-pais/; ver fila de geografía); repartido en módulos por el límite de 250 líneas) | C2, C3, C4, C5, FR-034, SC-012 |
| Los mensajes de cada escenario publicados en Kafka (casos con nombre, bytes exactos, todo sintético) | tests/support/publish_messages.py (se ejecuta en el servicio `tests`: `python -m tests.support.publish_messages <caso>`) | FR-031, SC-012 |
| Las pruebas de los auxiliares del script de verificación y de los casos del publicador (sin Docker) | tests/scripts/test_verify_consumer_helpers.py, tests/scripts/test_publish_messages.py, tests/scripts/test_verify_stack_a1.py (reconocimiento de la línea de decisión del check A1) | SC-009, FR-034 |
| La evidencia del bloque 6 (FAQ 12, reenvío, versiones, cuarentena y reinicio con Kafka real; consola de cada escenario) | docs/evidencias/consumidor-idempotente/ (`faq12_antes_despues.sql/.out`, `prueba2_reenvio.out`, `prueba3_4_versiones.out`, `prueba6_cuarentena.out`, `prueba8_reinicio.log/.out`, `bloque6_*`) | FR-034 |
| Las evidencias de infra-compose (arranque, clon limpio, reintentos, latido, 503, M7–M9, secretos…) | docs/evidencias/infra-compose/ | A1–A12, M7–M9 |
| La spec, el plan y las tareas de infra-compose | specs/002-infra-compose/ | A1–A12 |
| La spec, el plan, la investigación, las tareas (activas y diferidas), la bitácora y el contrato de ejecución del consumidor idempotente | specs/003-consumidor-idempotente/ (`contracts/consumer-runtime.md`) | C1–C8, C13 |
| Los apuntes para la memoria y la defensa del consumidor idempotente | docs/borradores/consumidor-idempotente.md | C1–C8, C13 |
| El informe del revisor del cierre del consumidor idempotente | docs/evidencias/subagentes/plan-reviewer-consumidor-idempotente-cierre.md | — |
| Cómo se decide qué se publica | common/ingest_decision.py, producer/cycle.py, producer/ingest_store.py (`load_state`, `mark_published`) | B6 |
| Qué versión gana | common/processing.py (`is_newer_version`, `decide_version_outcome`, `is_inconsistent_state`) | C4 |
| Cómo se asigna el país (catálogo de `data/catalogo/paises.geojson` parseado con `ADM0_A3` único, índice `STRtree`, borde incluido, empate por `ADM0_A3` menor; puro) | common/geo.py (`parse_country_catalog`, `build_country_index`, `assign_country`); `CountryRow` en common/records.py; dependencia `shapely` en pyproject.toml/uv.lock | C9–C12 |
| Las pruebas del catálogo y la asignación de país (catálogo real y cuadrados sintéticos) y su evidencia | tests/common/test_geo.py; docs/evidencias/geografia-pais/ | C9–C12 |
| Que la base tiene el esquema y el catálogo de países cargado al arrancar (`to_regclass` de 8 tablas; upsert repetible de `public.country` en una transacción, devuelve el índice) | consumer/schema_check.py (`ensure_schema_ready`, `SchemaNotReadyError`); consumer/catalog_loader.py (`load_country_catalog`, `CatalogLoadResult`); sentencias en consumer/queries.py (`COUNTRY_COUNT`, `REGCLASS_CHECK`) | C10, FR-008 a FR-012 |
| Las pruebas de esos dos pasos (esquema con pool de mentira; catálogo contra PostgreSQL real: 177, repetible, corrección de fila, duplicado) y su evidencia | tests/consumer/test_schema_check.py; tests/integration/test_catalog_load.py; docs/evidencias/geografia-pais/ (`T001_docker.txt`, `T006_*`, `T007_*`, `T008_*`, `T009_*`, `geografia_catalogo_carga.*`) | C10 |
| El país en la fila y el arranque conectado (`country_id` en `current` de `build_event_rows`; `PipelineDeps.locate` y línea `country_tie`; `prepare_database`: esquema, catálogo y localizador antes de crear el consumidor; ruta de `COUNTRY_CATALOG_PATH`) | common/transform.py, consumer/queries.py (`CURRENT_COLUMNS`), consumer/pipeline.py, consumer/loop.py (`prepare_database`), consumer/main.py; localizador «sin país» de pruebas en tests/support/db_helpers.py (`no_country_locator`) y tests/support/loop_harness.py; pruebas en tests/common/test_transform.py, tests/consumer/test_queries.py, tests/consumer/test_pipeline.py, tests/consumer/test_consumer_loop.py (orden de arranque) | C9, C11, FR-006, FR-008 a FR-011 |
| Los casos geográficos sintéticos (`synthetic-geo-…`: madrid, atlantico, mag-nula, negativos, lat-145, lon-nan, no-point, sin-time, sin-updated; `geo_cases()`) y su publicación en Kafka (`geo-madrid`, `geo-atlantico`, `geo-mag-nula`, `geo-lat-145`) | tests/support/messages.py (`geo_cases`, `build_geo_message`); tests/support/publish_messages.py; prueba de los casos en tests/scripts/test_publish_messages.py | C13, FR-016 |
| Las pruebas de aceptación de geografía contra PostgreSQL real (país por geometría y reproceso x100, Atlántico sin país, versiones; mag nula, negativos y cuarentena; tipo no earthquake excluido por el productor) y su arnés (pipeline y localizador reales, catálogo cargado) | tests/integration/ (`test_geography.py`, `test_geography_validity.py`, `test_geography_exclusion.py`); tests/support/geo_harness.py; evidencia en docs/evidencias/geografia-pais/ (`geografia_prueba5.*`, `geografia_prueba6_cuarentena.*`, `geografia_prueba7.*`, `geografia_no_earthquake.*`) | C9, C11, C12, C13, pruebas 5, 6 y 7 |
| La muestra real de un día (asigna país a cada evento de un feed `all_day` guardado; sin red ni base) y su prueba | scripts/geo_real_day.py (`summarize_day`); tests/scripts/test_geo_real_day.py; docs/evidencias/geografia-pais/ (`feed_all_day.geojson` real, `geo_real_day.out`) | C9, C12, SC-007 |
| La verificación del catálogo y de las pruebas 5 y 7 con Kafka y PostgreSQL reales (`python scripts/verify_consumer.py geo --yes`) y su prueba sin Docker | scripts/consumer_scenarios/geo.py; tests/scripts/test_geo_scenario.py; docs/evidencias/geografia-pais/ (`geografia_catalogo.out`, `geografia_pruebas5_7_kafka.out`, `T021_*`) | C9–C12, pruebas 5 y 7 |
| Qué va a cuarentena y por qué | common/validation.py (+ `validation_envelope.py`: pasos 1-3, dividido por el límite de 250 líneas), common/quarantine_row.py, consumer/writer.py (`write_quarantine`) | C5 |
| Cómo se escribe un evento en una transacción (estado actual, historial, `date_dim`) | consumer/writer.py (`write_event`) | C2, C3, C4 |
| Todo el SQL del consumidor (el esquema sale de una lista cerrada) | consumer/queries.py | C2, C5 |
| Qué error de base es de contenido (cuarentena) y cuál se reintenta | consumer/db_errors.py (`is_content_error`) | C5 |
| Las pruebas de integración con PostgreSQL real (base temporal, rol `observatory_consumer`, FAQ 12, reenvío, nulos y tiempos, `date_dim`, cuarentena, permisos) | tests/integration/ (`conftest.py`, `test_faq12.py`, `test_idempotence.py`, `test_nulls_times.py`, `test_date_dim.py`, `test_quarantine.py` (más de 250 líneas: son 14 motivos y casos hostiles en una tabla, se mantiene unido por T042), `test_roles.py`) | C1–C8, C13 |
| Ayudas de esas pruebas: base temporal, procesar un mensaje de punta a punta sin Kafka y escribir evidencias | tests/support/temp_database.py, tests/support/db_helpers.py, tests/support/evidence.py | FR-031, FR-033 |
| La evidencia del bloque 3 (FAQ 12, reenvío, versiones, cuarentena, roles) | docs/evidencias/consumidor-idempotente/ (`bloque3_*.out/.sql`, `roles_consumidor.out`, `pytest_integracion_bloque3.txt`) | FR-034 |
| Las estructuras del procesamiento (mensaje, resultado de versión, filas) | common/records.py | C1–C8 |
| Cómo se decodifica el valor Kafka y qué contenido no se puede guardar | common/decode.py, common/storable.py | C1, C5 |
| Cómo se convierten ms a UTC y se arman las filas de un evento | common/transform.py | C6, C7 |
| Cómo se decide el modo (`live`/`replay`) de un tema | common/kafka_topics.py::topic_mode | C1 |
| Los mensajes de prueba compartidos (secuencia FAQ 12) | tests/support/messages.py | C3, C4 |
| Qué devuelve la API de eventos | api/routers/events.py, api/queries.py | F1–F3 |
| Cómo el panel consume la API | frontend/src/app/core/api.service.ts | G1, G9 |

## Flujo actual (productor en vivo y consumidor idempotente)
USGS -> producer/usgs_client.py -> common/usgs_feed.py -> producer/ingest_store.py (original y estado) -> common/ingest_decision.py -> common/live_message.py
     -> producer/cycle.py -> producer/publisher.py -> Kafka (`earthquakes.live`) -> (ack) producer/ingest_store.py (`mark_published`)
     -> consumer/loop.py -> consumer/pipeline.py -> common/{decode,validation,transform,quarantine_row}.py -> consumer/writer.py -> PostgreSQL ; API: api/routers/health.py -> api/queries.py -> PostgreSQL (rol de solo lectura)

## Flujo previsto de un evento (de USGS al mapa)
Kafka -> consumer/pipeline.py -> common/validation.py -> common/geo.py
     -> consumer/writer.py -> PostgreSQL -> api/queries.py -> frontend/features/map

## Convenciones
Reglas completas en `docs/planificacion/03-procedimiento-ejecucion.md` §7.3. Resumen:
- Una función, una responsabilidad; unas 30 líneas como máximo por función y 250 por archivo.
- La lógica pura (validar, transformar) va separada del I/O (BD, Kafka, HTTP).
- `main.py` solo configura y arranca; no contiene lógica.
- Sin números ni textos mágicos: van a `config.py` o a constantes con nombre.
- Logging en vez de `print`, y errores con nombre en vez de `except Exception: pass`.

## Historial de features cerradas
| Feature | Qué añadió | Fecha |
|---|---|---|
| contratos-y-modelo | Contratos del mensaje Kafka, de la base de datos y de la API; `sql/001_schema.sql`; modelo de datos conceptual, lógico y físico; evidencias de las pruebas del esquema (E1–E5, E7, C4) | 2026-11-02 |
| infra-compose | `compose.yaml` con Kafka (KRaft), PostgreSQL 16, productor, consumidor y API; imagen Python compartida con `uv.lock`; `.env.example`; reintentos, latido y healthchecks; temas con retención de 7 días; roles de base de datos (`sql/002_roles.sql`); productor, consumidor y API mínimos con eventos sintéticos; `verify_stack.py` y `check_env_example.py`; pruebas unitarias; evidencias en `docs/evidencias/infra-compose/` (A1–A12; M7–M9 verificados) | 2026-11-04 |
| consumidor-idempotente | Consumidor que valida (`common/validation.py`), decide la versión (`common/processing.py`), escribe en una transacción por mensaje (`consumer/writer.py`), envía a cuarentena con motivo, reintenta sin límite la base y el commit del offset, deja una línea `decision=…` por mensaje y contadores `COUNTERS`; gancho de corte para la prueba 8; servicio `tests` (perfil `test`) y pruebas de integración con PostgreSQL real; `scripts/verify_consumer.py` (`faq12`, `quarantine`, `restart`); check A1 de `verify_stack.py` actualizado; evidencias en `docs/evidencias/consumidor-idempotente/` (C1–C8, C13; pruebas 2, 3, 4, 6 y 8; el consumidor lee solo el tema live; diferidos: catálogo de países, comprobación de esquema al arrancar y caídas de PostgreSQL/Kafka con Docker) | 2026-11-04 |
| productor-live | Productor que consulta el feed de USGS cada `POLL_SECONDS`, guarda el GeoJSON original con hash y retención (`ingest.raw_response`, `ingest.ingest_run`), excluye lo que no es `earthquake` con motivo (`live.exclusion`), decide con estado persistente (`ingest.ingest_state`) por `id` + `updated`, publica con clave `id` y marca solo tras el ack; backoff ante fallos de USGS; variables nuevas; permiso `SELECT, DELETE` sobre `raw_response`; sintéticos retirados del productor; evidencias en `docs/evidencias/productor-live/` (B1–B12; pruebas 1 hasta PostgreSQL y 2) | 2026-11-05 |
