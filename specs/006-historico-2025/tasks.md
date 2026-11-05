# Tasks: Histórico 2025

**Input**: `specs/006-historico-2025/` (spec.md, plan.md, research.md, data-model.md, quickstart.md).

**Rama**: `006-historico-2025`. **Estado**: 0/25 tareas hechas. No se hace commit ni merge: al terminar T025 se detiene el trabajo y se espera la revisión del alumno.

**Cubre**: B13–B18 y el procedimiento de hueco >24 h (B12).

**Alcance**: 25 tareas en 5 bloques. Fuera de alcance: replay, API, frontend, Kafka para el histórico, reconciliación de revisiones antiguas (B11), fuzz, auditorías y endurecimiento de casos raros. `kafka-message.md`, `db-schema.md`, `sql/001_schema.sql` y `docs/enunciado/` no se tocan (se comprueba en T025). Lo raro es un límite conocido en una línea (research.md), no una tarea.

## Formato y criterios comunes

Cada tarea: `- [ ] T### [P?] [US?] Descripción con ruta`, con **Cubre** (IDs) y **Criterio** (comando y resultado). `[P]` = paralelizable con otras `[P]` del bloque. Etiquetas: US1 descarga, US2 deduplicación, US3 carga, US4 documentación y hueco.

Toda tarea de código cumple además (heredado de `003`, no se repite): **CC-DOC** (identificadores en inglés; docstrings y comentarios en español con la plantilla de `03-procedimiento-ejecucion.md` §7.4; type hints; sin `print` en `common/`, `consumer/` ni `historical/`, salvo el resumen de los `*_main.py` por log; sin `except Exception: pass`); **CC-14** (una responsabilidad por función, ≈ 30 líneas, archivo ≤ 250, ≤ 4 parámetros, sin números ni textos mágicos, lo puro no importa `asyncpg`, el SQL vive en `consumer/queries.py`); **CC-MAP** (la tarea que crea, mueve o elimina archivos de código ajusta en el mismo paso la fila de `CODEMAP.md`).

La prueba va antes que su implementación (TDD): «falla antes» significa que al escribirla falla por falta de implementación o por import. Las pruebas usan USGS simulado y fixtures pequeños con ids `synthetic-…` e `is_synthetic=true`; los datos reales solo aparecen en el bloque 4.

**Imagen `tests` al día**: tras cambiar `common/`, `consumer/` o `historical/`, `docker compose --profile test build tests` antes de `pytest -m integration`.

Comandos de referencia: unitarias `uv run pytest -m "not integration" -q`; integración `docker compose up -d postgres`, `docker compose --profile test build tests`, `docker compose --profile test run --rm tests pytest -m integration -q`.

## Bloque 1 — Piezas puras de la descarga

**Objetivo**: intervalos, dedup, manifiesto y mensaje del contrato, sin red ni base. **Dependencias**: ninguna.

- [x] T001 [P] [US1] `tests/historical/test_intervals.py` y `historical/intervals.py`: `month_intervals(2025)` da 12 intervalos contiguos UTC (el `end` de uno es el `start` del siguiente; el último termina en 2026-01-01); `split_interval` da dos mitades contiguas que cubren el original; `build_query_url` incluye `minmagnitude=4`, `eventtype=earthquake`, `orderby=time-asc`, `format=geojson`, `starttime`, `endtime`.
  - Cubre: B13.
  - Criterio: `uv run pytest tests/historical/test_intervals.py -q` pasa; falla antes de implementar.

- [x] T002 [P] [US2] `tests/historical/test_dedup.py` y `historical/dedup.py`: dos listas con el mismo `id` → una sola feature con `updated` mayor y `discarded == 1`; mismo `updated` → se queda la primera; sin `id` o con `updated` no entero → pasa sin agrupar; entrada vacía → vacía.
  - Cubre: B14, SC-003.
  - Criterio: `uv run pytest tests/historical/test_dedup.py -q` pasa; en el resultado, `len(ids distintos) == len(features con id)`.

- [x] T003 [P] [US1] `tests/historical/test_manifest.py` y `historical/manifest.py`: estructuras de data-model §3, `sha256_of`, escritura atómica y lectura de `manifest.json`, `verify_file` (coincide / no coincide / ausente → error que nombra el archivo).
  - Cubre: B15, FR-003, FR-008.
  - Criterio: `uv run pytest tests/historical/test_manifest.py -q` pasa (ida y vuelta de un manifiesto sintético; sha256 alterado detectado).

- [x] T004 [US3] `tests/historical/test_envelope.py` y `historical/envelope.py::build_message_bytes(feature, extracted_at)`: el mensaje tiene `source=usgs_historical`, `mode=live`, `replay_at=null`, `is_synthetic` indicado, `ingested_at` con `Z`, la feature intacta; dos llamadas dan los mismos bytes; `common.validation.validate_message` con tema `earthquakes.live` lo acepta.
  - Cubre: B16, FR-010.
  - Criterio: `uv run pytest tests/historical/test_envelope.py -q` pasa (usa `validate_message`, no una copia).

## Bloque 2 — Descarga (E/S con USGS simulado)

**Objetivo**: descargador completo y probado sin la red real. **Dependencias**: bloque 1.

- [x] T005 [US1] `tests/historical/test_fetch_interval.py` y `historical/fetch_interval.py`: con un `fetch` inyectado que simula `count` y datos, un intervalo con `count <= 20000` hace una consulta; un mes simulado con `count = 45000` (ids `synthetic-…`) se divide recursivamente, suma 45000 registros, 0 perdidos y un único `FeatureCollection` fusionado; si los registros devueltos ≠ `count` lanza error con ambas cifras; un intervalo de 1 ms con `count > 20000` lanza error explícito.
  - Cubre: B13, SC-002, FR-002.
  - Criterio: `uv run pytest tests/historical/test_fetch_interval.py -q` pasa; el log muestra una línea `query …` por consulta.

- [x] T006 [US1] En `historical/fetch_interval.py` y `tests/historical/test_fetch_interval.py`: reintentos ante `FeedFetchError` (429, 5xx, timeout) con `common/backoff.compute_backoff_seconds`, máximo 5 intentos (constante con nombre); al agotarlos, error que nombra el intervalo. Con espera inyectable (sin dormir en la prueba).
  - Cubre: B13, FR-007.
  - Criterio: la prueba con 2 fallos y un éxito pasa; con 5 fallos lanza el error con el mes.

- [x] T007 [US1] `tests/historical/test_download.py` y `historical/download.py::download_year`: escribe 12 archivos crudos y `manifest.json` (sha256, registros, consultas, fecha); dedup entre archivos con un `id` en la frontera (manifiesto cuenta `duplicates_discarded=1`); total único ≠ `count` anual simulado → error y **código de salida distinto de 0** con ambas cifras; segunda ejecución con archivos y sha256 válidos → 0 peticiones; `force=True` → vuelve a pedir; un mes que falla conserva los anteriores y el manifiesto parcial permite reanudar.
  - Cubre: B13, B14, B15, SC-001, FR-004 a FR-006.
  - Criterio: `uv run pytest tests/historical/test_download.py -q` pasa (contador de peticiones del doble = 0 en la segunda ejecución).

- [x] T008 [US4] `tests/historical/test_download_gap.py` y `historical/download.py::download_gap`: con `--start/--end` guarda `usgs_gap_<start>_<end>.geojson`, lo añade a `gaps` del manifiesto sin alterar `totals` de 2025, contrasta con su propio `count`; un intervalo con `end <= start` es error.
  - Cubre: B12, B15, pregunta 1.
  - Criterio: `uv run pytest tests/historical/test_download_gap.py -q` pasa.

- [x] T009 [US1] `historical/download_main.py` (solo configura y arranca: `--force`, `--start`, `--end`, directorio de salida) y `tests/historical/test_download_main.py`: argumentos inválidos (`--start` sin `--end`) terminan con código ≠ 0; con el servidor simulado `tests/support/mock_usgs.py` extendido para `count` (o un doble equivalente) la CLI deja los archivos en un directorio temporal.
  - Cubre: B13, B15, B17.
  - Criterio: `uv run pytest tests/historical -q` pasa completo; `uv run python -m historical.download_main --help` lista las tres opciones.

## Bloque 3 — Carga con el procesamiento común

**Objetivo**: cargador sobre `process_record` y su prueba de aceptación con PostgreSQL real. **Dependencias**: bloques 1 y 2 (T003, T004).

- [x] T010 [US3] Referencia Kafka nula (research D1): `MessageRef.partition/offset` admiten `None`; `kafka_columns(ref)` en `common/records.py`; usarla en `common/transform.py` y `common/quarantine_row.py`; `QuarantineRow.kafka_topic` opcional; formatos de log `%d` → `%s` en `consumer/pipeline.py` y `consumer/resilience.py`. Pruebas en `tests/common/test_transform.py` y `tests/common/test_quarantine_row.py`: con ref `partition=None` las columnas `kafka_*` salen `None`; con ref real, iguales que antes. Se ejecuta la suite completa antes y después.
  - Cubre: B16, FR-009, FR-010.
  - Criterio: `uv run pytest -m "not integration" -q` pasa con el mismo nº de pruebas previas + las nuevas (0 rotas de 003–005); `docker compose --profile test run --rm tests pytest -m integration -q` pasa.

- [x] T011 [US3] `tests/historical/test_loader.py` y `historical/loader.py::load_historical`: lee el manifiesto, `verify_file` de cada archivo (falta o sha256 distinto → se detiene nombrando el archivo, 0 eventos escritos), `dedup_features` sobre todos los archivos, y por evento `build_message_bytes` + `process_record` con `RawRecord(topic=TOPIC_LIVE, partition=None, offset=None)` y un `PipelineDeps` doble; devuelve `LoadSummary` (únicos, nuevos, versiones nuevas, sin cambios, cuarentena). Una cuarentena no detiene la carga.
  - Cubre: B16, FR-008, FR-009, FR-011, FR-013.
  - Criterio: `uv run pytest tests/historical/test_loader.py -q` pasa con escritores de mentira; el loader no importa nada de `common.validation`, `common.transform` ni `common.geo` (revisión en T017).

- [x] T012 [P] [US3] `consumer/queries.py` (consultas de data-model §6) y `historical/verify.py::verify_load(pool, unique_ids, quarantined_ids)` + `snapshot_fingerprint(pool)`; pruebas en `tests/consumer/test_queries.py` (texto de las sentencias, esquema solo `live`) y `tests/historical/test_verify.py` (fórmula `|U| − |Q|` con conexión de mentira, discrepancia → resultado falso con ambas cifras).
  - Cubre: B14, B17, FR-013, SC-004.
  - Criterio: `uv run pytest tests/consumer/test_queries.py tests/historical/test_verify.py -q` pasa.

- [x] T013 [US3] `historical/load_main.py` (configura y arranca: `load_database_settings`, `create_pool_with_retry`, `ensure_schema_ready`, `load_country_catalog`, `load_historical`, `verify_load`, código de salida ≠ 0 si la verificación falla) y `COPY historical ./historical` en el `Dockerfile`; fila de `CODEMAP.md`.
  - Cubre: B16, B17, FR-014, FR-015.
  - Criterio: `docker compose build producer` termina bien (imagen compartida); `docker compose run --rm --no-deps consumer python -c "import historical.load_main"` no falla; `grep -n "localhost" historical/` no devuelve nada.

- [x] T014 [US3] `tests/integration/test_historical_load.py` (base temporal, rol `observatory_consumer`, catálogo real): fixture de ~30 eventos `synthetic-…` en 3 archivos con un `id` repetido entre dos de ellos y 3 inválidos; tras cargar, `current_event` = únicos − cuarentena, todos con `source=usgs_historical`, `mode`/esquema `live`, `is_synthetic` según el fixture, `ingested_at` = fecha del manifiesto, `kafka_*` nulos en `event_version`; `event_version` una fila por `(id, updated)` único; `verify_load` verdadero.
  - Cubre: B14, B16, SC-004, FR-010.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_historical_load.py -q` pasa.

- [x] T015 [US3] `tests/integration/test_historical_reload.py`: cargar el fixture de T014 tres veces; tras la 2.ª y 3.ª, 0 filas nuevas y 0 modificadas en `current_event`, `event_version` y `quarantine` (misma huella, resumen `new=0 newer=0`); reiniciar la conexión/pool entre cargas.
  - Cubre: B17, SC-005, FR-012.
  - Criterio: la prueba pasa y guarda en `docs/evidencias/historico-2025/` la huella antes y después.

- [x] T016 [US3] `tests/integration/test_historical_rules.py` con fixtures sintéticos: `mag` nula → `mag` nulo (no 0); `mag` y profundidad negativas válidas; latitud 145 → 1 fila de cuarentena `coordinates_out_of_range`; evento en Madrid → `country_id=ESP` y en el Atlántico → nulo; dos versiones del mismo `id` en archivos distintos → solo la de `updated` mayor pasa a `current_event`; un `id` ya presente en la base con `updated` mayor (cargado por la vía en vivo) no retrocede.
  - Cubre: B16, SC-006, constitución §2, §4, §5, §6.
  - Criterio: la prueba pasa; el mensaje del caso «no retrocede» muestra `source` y `updated_ms` sin cambios.

- [x] T017 [US3] `tests/historical/test_no_duplicated_logic.py`: el código de `historical/` no define ni importa validación, conversión de tiempos ni asignación de país (revisión estática de importaciones: ninguna de `common.validation*`, `common.transform`, `common.geo`, `common.decode` salvo lo que pase por `consumer.pipeline`) y `load_historical` llama a `process_record`.
  - Cubre: B16, SC-008, FR-009.
  - Criterio: `uv run pytest tests/historical/test_no_duplicated_logic.py -q` pasa.

- [x] T018 [US4] `tests/integration/test_historical_gap.py`: base con 10 eventos sintéticos cargados por el camino normal; archivo de hueco que repite 4 de ellos (mismo `updated`), 1 con `updated` menor y 3 nuevos → los 4 iguales no cambian nada, el de `updated` menor no retrocede, los 3 nuevos aparecen una vez; repetir no cambia nada.
  - Cubre: B12, constitución §1 y §2.
  - Criterio: la prueba pasa (conteos antes/después en la salida).

## Bloque 4 — Datos reales de 2025

**Objetivo**: descargar y cargar el año real y verificarlo. **Dependencias**: bloques 1 a 3. Necesita red y Docker; se hace una sola vez.

- [x] T019 [US1] Descarga real: `uv run python -m historical.download_main` (con log a `docs/evidencias/historico-2025/descarga_2025.log`). Comprobar 12 archivos + `manifest.json`, sha256 correctos, total único == `count` de USGS. Medir el tamaño y aplicar FR-019 (versionar o `.gitignore` + `checksums.sha256`). Segunda ejecución sin peticiones.
  - Cubre: B13, B14, B15, SC-001, FR-019, pregunta 3.
  - Criterio: log con registros por consulta, duplicados descartados, único == `count`; `sha256sum -c` (o equivalente) sin fallos; segunda ejecución imprime «0 peticiones».

- [x] T020 [US3] Carga real: `docker compose up -d postgres` y el comando del quickstart §4; verificar `|U| − |Q|` con la consulta SQL guardada en `docs/evidencias/historico-2025/verificacion.sql/.out`; repetir la carga (huella idéntica); `docker compose restart postgres` y recontar.
  - Cubre: B16, B17, SC-004, SC-005, SC-007.
  - Criterio: `historical_summary … ok=true`; recuento tras la 2.ª carga y tras el reinicio igual al de la 1.ª; evidencias guardadas.

- [x] T021 [US4] Ensayo del procedimiento de hueco con datos reales: descargar un intervalo corto de 2025 (p. ej. 2025-12-30 a 2025-12-31) con `--start/--end`, cargarlo y comprobar que no duplica ni cambia lo cargado en T020.
  - Cubre: B12, SC-005.
  - Criterio: huella de `current_event` idéntica antes y después; el archivo del hueco aparece en `gaps` del manifiesto; salida guardada en `docs/evidencias/historico-2025/hueco_ensayo.out`.

## Bloque 5 — Documentación y cierre

**Objetivo**: README, borrador de memoria, evidencias y cierre (constitución §16). **Dependencias**: bloques 1 a 4.

- [x] T022 [US4] Sección «Histórico 2025» en `README.md`: comandos de descarga y de carga repetibles (quickstart §3 y §4), dónde quedan los archivos, qué esperar, si el clon necesita descargar (según T019) y el comando del hueco.
  - Cubre: B17, B12, FR-016.
  - Criterio: seguir la sección en un clon limpio de los archivos de `data/historical/` reproduce el recuento de T020.

- [x] T023 [US4] `docs/borradores/historico-2025.md`: párrafo «por qué lote y no Kafka» (research D10, apoyado en `kafka-message.md` §1 y `db-schema.md` §1), párrafo «instantánea a la fecha de extracción» (B18), procedimiento de recuperación de un hueco >24 h (B12) y límites conocidos de research.
  - Cubre: B12, B16, B18, FR-017, FR-018.
  - Criterio: el borrador existe, cita los contratos y no usa lenguaje de predicción ni riesgo (constitución §21).

- [x] T024 [US4] Evidencias y mapa: guardar en `docs/evidencias/historico-2025/` la salida de `pytest` (unitarias e integración), el log de descarga, la consulta SQL de verificación y la recarga sin diferencias (FR-021); actualizar `CODEMAP.md` (filas de `historical/`, cambio de `MessageRef`, historial de features, flujo del histórico).
  - Cubre: FR-021, constitución §16.
  - Criterio: cada archivo citado en `CODEMAP.md` existe (`ls`); las filas nuevas siguen el formato de las anteriores.

- [x] T025 [US4] Cierre: `uv run pytest -m "not integration" -q`, integración completa, `git diff --stat -- specs/001-contratos-y-modelo/contracts sql/001_schema.sql docs/enunciado` vacío, `grep -rn "password\|secret" historical/` sin secretos, marcar T001–T025 y actualizar `bitacora.md` y las casillas de B12–B18 de `docs/planificacion/01-checklist-requisitos.md` solo con evidencia. Detenerse: sin commit ni merge.
  - Cubre: B12–B18, SC-008, SC-009.
  - Criterio: todo verde; diff de contratos vacío; evidencia enlazada en la bitácora.

## Dependencias entre bloques

`1 → 2 → 3 → 4 → 5`. Dentro del bloque 1, T001–T003 son paralelas; T004 puede ir en paralelo con ellas. En el bloque 3, T010 debe terminar antes de T014–T016; T012 es paralela a T011.
T010 va antes de T011 (no solo antes de T014–T016).

## Trazabilidad B → tareas

| ID | Tareas |
|---|---|
| B13 | T001, T005, T006, T007, T009, T019 |
| B14 | T002, T007, T012, T014, T019 |
| B15 | T003, T007, T008, T009, T019 |
| B16 | T004, T010, T011, T013, T014, T016, T017, T020, T023 |
| B17 | T009, T012, T013, T015, T020, T022 |
| B18 | T023 |
| B12 | T008, T018, T021, T022, T023 |
