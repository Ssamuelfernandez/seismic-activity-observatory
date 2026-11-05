# Tasks: Geografía y país

**Input**: `specs/005-geografia-pais/` (spec.md, plan.md, research.md, data-model.md, quickstart.md).

**Rama**: `005-geografia-pais`. **Estado**: ninguna tarea hecha. No se hace commit ni merge: al terminar T025 se detiene el trabajo y se espera la revisión del alumno.

**Cubre**: C9–C12; pruebas de aceptación 5 (magnitud nula) y 7 (evento marítimo), con refuerzo de la 6. Retoma de `003-consumidor-idempotente` las tareas diferidas T062–T067, T069 y T080 (catálogo y comprobación del esquema al arrancar).

**Alcance**: 25 tareas en 5 bloques. Fuera de alcance: histórico, replay, API, frontend, contadores y motivos de cuarentena nuevos, recálculo retroactivo, fuzz y auditorías. `kafka-message.md`, `db-schema.md`, `sql/001_schema.sql` y `docs/enunciado/` no se tocan (se comprueba en T025). Lo raro es un límite conocido en una línea (research.md), no una tarea.

## Formato y criterios comunes

Cada tarea: `- [ ] T### [P?] [US?] Descripción con ruta`, con **Cubre** (IDs) y **Criterio** (comando y resultado). `[P]` = paralelizable con otras `[P]` del bloque. Etiquetas `[US1]…[US5]` = historias de la spec.

Toda tarea de código cumple además (heredado de `003`, no se repite): **CC-DOC** (identificadores en inglés; docstrings y comentarios en español con la plantilla de `03-procedimiento-ejecucion.md` §7.4; type hints; sin `print` en `common/` ni `consumer/`; sin `except Exception: pass`); **CC-14** (una responsabilidad por función, cuerpo ≈ 30 líneas, archivo ≤ 250, ≤ 4 parámetros, sin números ni textos mágicos, lo puro no importa `asyncpg` ni `aiokafka`, el SQL vive en `consumer/queries.py`); **CC-MAP** (la tarea que crea, mueve o elimina archivos de código ajusta en el mismo paso la fila de `CODEMAP.md`).

La prueba va antes que su implementación (TDD): "falla antes" significa que al escribirla falla por falta de implementación o por import.

**Imagen `tests` al día**: tras cualquier cambio en `common/` o `consumer/`, `docker compose --profile test build tests` antes de `pytest -m integration`.

Comandos de referencia: unitarias `uv run pytest -m "not integration" -q`; integración `docker compose up -d postgres`, `docker compose --profile test build tests`, `docker compose --profile test run --rm tests pytest -m integration -q`. Los scripts que usan `down -v` se ejecutan con `--yes`.

## Bloque 1 — Dependencia y asignación de país (funciones puras)

**Objetivo**: `common/geo.py` completo y probado sin base ni red. **Dependencias**: ninguna.

- [x] T001 Añadir `shapely` (2.x, versión exacta) a `dependencies` de `pyproject.toml`, ejecutar `uv lock` y reconstruir la imagen. No se añade GeoPandas.
  - Cubre: C9, constitución §11, D1.
  - Criterio: `git diff --stat -- pyproject.toml uv.lock` muestra solo `shapely` (y sus dependencias transitivas si las hubiera); `uv run python -c "import shapely; print(shapely.__version__)"` imprime la versión fijada; `docker compose build producer` termina bien y `docker compose run --rm --no-deps consumer python -c "import shapely; from shapely.strtree import STRtree"` no falla (imagen `production`). Si las ruedas no instalan en la imagen, se detiene y se escala.

- [x] T002 [P] [US4] Pruebas del catálogo en `tests/common/test_geo.py` (parte 1): con `data/catalogo/paises.geojson` real, `parse_country_catalog` devuelve 177 entradas con `ADM0_A3` único y el mapeo `ADM0_A3`→`country_id`, `NAME_ES`→`name_es`, `ADMIN`→`admin`, `CONTINENT`→`continent`, `SUBREGION`→`subregion`; el SHA-256 del archivo no cambia tras parsear; un GeoJSON sintético con un `ADM0_A3` repetido lanza `CatalogError` que nombra el código; con un campo ausente lanza error que cita campo y posición; con una geometría que no es `Polygon`/`MultiPolygon` lanza error que nombra la entidad. Falla antes de T003.
  - Cubre: C10, FR-010, SC-006.
  - Criterio: falla antes de T003 y pasa después (2 pruebas de unicidad: real = 177 distintos; sintético con repetido = rechazo).

- [x] T003 [US4] Crear `common/geo.py` con `CatalogError` y `parse_country_catalog(geojson: dict) -> CountryCatalog`, y añadir `CountryRow` a `common/records.py` (estructuras de data-model.md §1; sin leer archivos ni importar `asyncpg`/`aiokafka`). CC-DOC, CC-14, CC-MAP.
  - Cubre: C10, FR-005, FR-010.
  - Criterio: `uv run pytest tests/common/test_geo.py -q` pasa (parte 1); `grep -n "asyncpg\|aiokafka\|open(" common/geo.py` no devuelve nada.

- [x] T004 [P] [US1] Pruebas de asignación en `tests/common/test_geo.py` (parte 2): con el catálogo real, Madrid (lon -3,70 lat 40,42) → `ESP` y Atlántico (lon -30 lat 35) → `None` con candidatos vacíos; con catálogos sintéticos mínimos de cuadrados: punto en el interior → ese país; **punto sobre la arista compartida de dos cuadrados → no `None`** y el de `ADM0_A3` menor; **punto en dos polígonos solapados → el menor**, con ambos en `candidates`; el mismo resultado en 10 ejecuciones y con el catálogo en orden inverso; un vértice real de un polígono del catálogo (borde) → no `None`; lon ±180 y lat ±90 no lanzan. Falla antes de T005.
  - Cubre: C9, C11, C12, FR-001 a FR-005, SC-008, pruebas 7.
  - Criterio: falla antes de T005 y pasa después.

- [x] T005 [US1] En `common/geo.py`, `build_country_index(catalog) -> CountryIndex` (`STRtree`, construido una vez) y `assign_country(index, lon, lat) -> CountryMatch` según data-model.md §3 (`covered_by`, candidatos ordenados, menor `ADM0_A3`, ninguno → `None`). CC-DOC, CC-14, CC-MAP (fila «Cómo se asigna el país» pasa de prevista a real).
  - Cubre: C9, C11, C12, FR-001 a FR-005, FR-019.
  - Criterio: `uv run pytest tests/common/test_geo.py -q` pasa completo; `common/geo.py` ≤ 250 líneas (si no, se divide el parseo y se anota en `CODEMAP.md`).

## Bloque 2 — Esquema y catálogo en la base al arrancar (retoma T062–T067 de `003`)

**Objetivo**: comprobar el esquema y cargar `public.country` de forma repetible. **Dependencias**: bloque 1 (T003, T005).

- [x] T006 [P] [US4] Pruebas de `ensure_schema_ready` en `tests/consumer/test_schema_check.py` con conexión de mentira: `to_regclass` devuelve `NULL` para una de las 8 tablas (`public.country`, `public.date_dim`, `live.current_event`, `live.event_version`, `live.quarantine` y las tres de `replay`) → `SchemaNotReadyError` cuyo mensaje contiene el nombre; con todas presentes no lanza. Falla antes de T007.
  - Cubre: FR-008, retoma T064.
  - Criterio: falla antes de T007 y pasa después.

- [x] T007 [US4] Crear `consumer/schema_check.py::ensure_schema_ready(pool)` y `SchemaNotReadyError` (consulta con `to_regclass`; la sentencia vive en `queries.py`). CC-DOC, CC-14, CC-MAP.
  - Cubre: FR-008, retoma T065.
  - Criterio: `uv run pytest tests/consumer/test_schema_check.py -q` pasa.

- [x] T008 [P] [US4] `tests/integration/test_catalog_load.py` (base temporal): `load_country_catalog` carga 177 filas (`inserted=177 updated=0`); segunda carga `inserted=0 updated=0` y mismas filas; una fila alterada a mano se corrige (`updated=1`); catálogo sintético con `ADM0_A3` repetido lanza `CatalogError` y deja `public.country` sin cambios; la línea `catalog loaded total=… inserted=… updated=…` se emite una vez por carga (`caplog`); el archivo no cambia (hash). Falla antes de T009.
  - Cubre: C10, FR-009 a FR-012, SC-005, SC-006, retoma T066.
  - Criterio: falla antes de T009 y pasa después.

- [x] T009 [US4] Crear `consumer/catalog_loader.py::load_country_catalog(pool, path) -> tuple[CountryIndex, CatalogLoadResult]` (abre el archivo en lectura, `parse_country_catalog`, `build_country_index`, y en **una transacción** `COUNTRY_UPSERT` por fila con `inserted = count después − antes` y `updated = cambiadas − inserted`; añade a `queries.py` el recuento de `public.country` y la consulta `to_regclass`). CC-DOC, CC-14, CC-MAP.
  - Cubre: C10, FR-009 a FR-012, retoma T067.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_catalog_load.py -m integration -q` pasa; `grep -rn "INSERT INTO\|SELECT " consumer/*.py | grep -v queries.py` no devuelve SQL fuera de `queries.py`.

## Bloque 3 — País en la fila y arranque conectado

**Objetivo**: `country_id` escrito en `current_event` y orden de arranque correcto. **Dependencias**: bloques 1 y 2. T013 y T014 se hacen seguidas (no se levanta Compose entre ellas).

- [x] T010 [P] [US1] Reescribir las dos pruebas que afirman lo contrario: `tests/common/test_transform.py::test_country_id_is_absent` pasa a comprobar que `build_event_rows(valid, ref, now, country_id)` pone `country_id` en `current` (`None` si no se pasa, nunca en `version`) y `tests/consumer/test_queries.py::test_current_event_upsert_is_conditional_and_ignores_country` pasa a comprobar que `country_id` está en `CURRENT_COLUMNS` y en el `DO UPDATE SET`, con el `WHERE EXCLUDED.updated_ms >` intacto y los `$n` coherentes con el número de columnas. Falla antes de T011.
  - Cubre: C9, FR-006, D5.
  - Criterio: falla antes de T011 y pasa después.

- [x] T011 [US1] `common/transform.py::build_event_rows` recibe `country_id: str | None = None` (4 parámetros) y lo incluye en `current`; `consumer/queries.py::CURRENT_COLUMNS` añade `country_id` y se corrige el comentario de `UPSERT_FIXED_COLUMNS`; se actualizan los docstrings de `EventRows` y del módulo `transform.py` (ya no dicen "sin país"). CC-DOC, CC-14, CC-MAP.
  - Cubre: C9, FR-006.
  - Criterio: `uv run pytest tests/common/test_transform.py tests/consumer/test_queries.py -q` pasa.

- [x] T012 [P] [US1] Pruebas en `tests/consumer/test_pipeline.py`: con un localizador doble, `process_record` lo llama una vez con `(lon, lat)` del mensaje válido y pasa su `country_id` al escritor; **no lo llama** si el mensaje va a cuarentena (lat 145); con candidatos múltiples escribe la línea INFO `country_tie event_id=… candidates=… chosen=…` (`caplog`) y con un solo candidato o ninguno no escribe nada. Falla antes de T013.
  - Cubre: C9, C11, FR-003, FR-006, FR-014.
  - Criterio: falla antes de T013 y pasa después.

- [x] T013 [US1] `consumer/pipeline.py`: `PipelineDeps.locate: Callable[[float, float], CountryMatch]` (obligatorio, sin valor por defecto), llamada en `_write_valid` antes de `build_event_rows`, línea `country_tie`. Actualizar `tests/support/db_helpers.py` (parámetro `locate` con un localizador de pruebas «sin país» por defecto, para que las pruebas de integración existentes sigan igual) y los constructores de `PipelineDeps` de las pruebas existentes. CC-DOC, CC-14, CC-MAP.
  - Cubre: C9, C11, FR-001, FR-003, FR-006.
  - Criterio: `uv run pytest -m "not integration" -q` pasa; `grep -n "place" consumer/pipeline.py common/geo.py` no muestra uso del texto `place` para el país.

- [x] T014 [US4] Cablear el arranque en `consumer/loop.py::run_consumer` y `consumer/main.py` (según plan §5): `check_database` → pool → `ensure_schema_ready` → `load_country_catalog(pool, settings.country_catalog_path)` → `start_consumer`, con `locate` ligado al índice devuelto y la ruta leída de `COUNTRY_CATALOG_PATH` (`read_str`). Añadir a `tests/consumer/test_consumer_loop.py` una prueba del **orden de arranque** con dobles (el catálogo se carga antes de crear el consumidor; si `ensure_schema_ready` o la carga lanzan, no se consume). CC-DOC, CC-14, CC-MAP.
  - Cubre: FR-008 a FR-011, retoma T069.
  - Criterio: `uv run pytest tests/consumer/test_consumer_loop.py -q` pasa; `uv run python scripts/check_env_example.py` termina con código 0 (no hay variable nueva).

## Bloque 4 — Casos sintéticos, pruebas de aceptación y verificación real

**Objetivo**: demostrar C9–C12 y las pruebas 5 y 7. **Dependencias**: bloques 1 a 3. Todos los casos son sintéticos (`is_synthetic = true`, ids `synthetic-geo-…`).

- [x] T015 Añadir a `tests/support/messages.py` los constructores de los casos de F5: `madrid` (lon -3,70 lat 40,42, con un `place` que dice otro país), `atlantico` (lon -30 lat 35), `mag-nula` (en Madrid), `negativos` (`mag -0.06`, profundidad `-0.18`, en Madrid), `lat-145`, `lon-nan` (longitud no finita), `no-point` (geometría que no es `Point`), `sin-time` y `sin-updated`. Ids `synthetic-geo-<caso>`. CC-DOC, CC-MAP.
  - Cubre: C13, FR-016, US5.
  - Criterio: `uv run python -c "from tests.support.messages import geo_cases; print(sorted(geo_cases()))"` lista los 9 casos y todos llevan `is_synthetic == True`.

- [x] T016 [P] [US1] [US2] `tests/integration/test_geography.py` (base temporal con catálogo cargado por `load_country_catalog` y `PipelineDeps.locate` real; la tabla `public.country` se vacía entre pruebas, así que cada prueba la recarga): Madrid → `country_id = 'ESP'` aunque `place` diga otro país; reprocesarlo 100 veces no cambia ninguna tabla; Atlántico → fila en `current_event` con `country_id` nulo y 0 filas en `quarantine`; con eventos con y sin país presentes, «con país» + «sin país» = total de `current_event` y ambos son mayores que 0; versión posterior de Madrid con coordenadas en el mar → `country_id` pasa a `NULL`; versión antigua tardía con otro país → `country_id` no cambia; el FK se cumple (todo `country_id` está en `public.country`). Guarda con `evidence.record_query` los recuentos con/sin país y las filas de los casos en `docs/evidencias/geografia-pais/`. Falla antes de T013/T014.
  - Cubre: C9, C11, C12, FR-001 a FR-007, SC-001, SC-002, prueba 7.
  - Criterio: pasa tras T014; `geografia_prueba7.out` muestra Atlántico con `country_id` vacío y la suma con/sin = total.

- [x] T017 [P] [US3] `tests/integration/test_geography_validity.py` (mismo montaje): `mag-nula` en Madrid → `mag` `NULL` (0 filas con `mag = 0`) en `current_event` y `event_version`, `country_id = 'ESP'`; `negativos` se guarda tal cual con país; `lat-145` → 1 fila de cuarentena `coordinates_out_of_range` con referencia Kafka y hash, 0 en `current_event`/`event_version`; `lon-nan`, `no-point`, `sin-time`, `sin-updated` → cuarentena con su motivo (`coordinates_out_of_range`/`invalid_geometry`, `missing_time`, `missing_updated`) y ninguno llama al localizador; solo el caso válido sintético tiene `is_synthetic = true` y la base de pruebas no tiene ningún evento real marcado. Guarda `geografia_prueba5.out` y `geografia_prueba6_cuarentena.out`. Si un caso revela un hueco de `common/validation.py`, se corrige dentro de los motivos existentes (FR-013); un motivo nuevo se escala al alumno.
  - Cubre: C9, C12, C13, FR-013 a FR-016, SC-003, SC-004, pruebas 5 y 6.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_geography_validity.py -m integration -q` pasa.

- [x] T018 [P] [US5] Prueba del tipo no-earthquake en `tests/integration/test_geography_exclusion.py` reutilizando `MockUsgs` y `producer_harness` de `productor-live`: un feature `synthetic-…` con `event_type` distinto de `earthquake` (p. ej. `quarry blast`) no se publica y deja una fila en `live.exclusion` con `observed_type`; el consumidor no cambia (decisión D8). Guarda `geografia_no_earthquake.out`.
  - Cubre: C13, FR-016, US5.2.
  - Criterio: pasa en el servicio `tests`; la fila de `exclusion` aparece en la evidencia.

- [x] T019 [US1] Crear `scripts/geo_real_day.py` (CLI, `print` permitido) y descargar una vez el feed real `all_day` a `docs/evidencias/geografia-pais/feed_all_day.geojson`: lee el GeoJSON, asigna país a cada evento con `common/geo.py` y escribe cuántos tienen país, cuántos no, los códigos distintos, y confirma que todo código asignado está en el catálogo. Prueba unitaria sin red en `tests/scripts/test_geo_real_day.py` con un feed mínimo inventado y etiquetado. CC-DOC, CC-MAP.
  - Cubre: C9, C12, SC-007.
  - Criterio: `uv run python scripts/geo_real_day.py docs/evidencias/geografia-pais/feed_all_day.geojson | tee docs/evidencias/geografia-pais/geo_real_day.out` termina con código 0 y muestra «sin error»; `uv run pytest tests/scripts/test_geo_real_day.py -q` pasa.

- [x] T020 Añadir los casos `geo-*` al publicador `tests/support/publish_messages.py` (madrid, atlantico, mag-nula, lat-145, usando los constructores de T015) y su prueba en `tests/scripts/test_publish_messages.py` (sin Docker). CC-DOC, CC-MAP.
  - Cubre: FR-016, retoma la mecánica de T080.
  - Criterio: `uv run pytest tests/scripts/test_publish_messages.py -q` pasa.

- [x] T021 [US4] Escenario `geo` en `scripts/verify_consumer.py` (módulo `scripts/consumer_scenarios/geo.py`): `docker compose build producer`, `down -v` (el script exige `--yes`), `up -d kafka postgres consumer`; espera `healthy`; comprueba la línea `catalog loaded total=177 inserted=177 updated=0` y `SELECT count(*) FROM public.country` = 177; publica los casos `geo-*`; consulta `current_event` y `quarantine` (Madrid `ESP`, Atlántico nulo, mag nula `NULL` con `ESP`, lat 145 en cuarentena); `docker compose restart consumer` → `inserted=0 updated=0` y 177. Guarda `geografia_catalogo.out` y `geografia_pruebas5_7_kafka.out`. CC-DOC, CC-14, CC-MAP.
  - Cubre: C9–C12, FR-009, SC-001 a SC-005, pruebas 5 y 7, retoma T080.
  - Criterio: `python scripts/verify_consumer.py geo --yes` termina con código 0 y los dos archivos de evidencia existen y no están vacíos.

## Bloque 5 — Cierre

**Objetivo**: evidencias, documentación y comprobaciones finales. **Dependencias**: bloque 4.

- [x] T022 Ejecutar `uv run pytest -m "not integration" -q` y `docker compose --profile test run --rm tests pytest -m integration -q -s` (tras `build tests`) y guardar las salidas en `docs/evidencias/geografia-pais/pytest_unitarias.txt` y `pytest_integracion.txt`; verificar que existen y no están vacíos todos los archivos de evidencia citados (`geografia_prueba5.out`, `geografia_prueba6_cuarentena.out`, `geografia_prueba7.out`, `geografia_no_earthquake.out`, `geo_real_day.out`, `geografia_catalogo.out`, `geografia_pruebas5_7_kafka.out`). Si falta alguno, se corrige el test o el script que debía producirlo.
  - Cubre: FR-020, constitución §16.
  - Criterio: 0 fallos en ambas ejecuciones; los 9 archivos de `docs/evidencias/geografia-pais/` existen y no están vacíos.

- [ ] T023 Actualizar `CODEMAP.md` (filas de `common/geo.py`, `schema_check.py`, `catalog_loader.py`, tests nuevos, `scripts/geo_real_day.py`, escenario `geo`, `docs/evidencias/geografia-pais/`, `specs/005-geografia-pais/`; la fila de `geo.py` pasa de prevista a real; entrada en «Historial de features cerradas» y quitar el «diferido» de `consumidor-idempotente` que esta feature resuelve) y la sección de README del consumidor (país por geometría, catálogo al arrancar, `shapely` como dependencia nueva, límite: sin recálculo retroactivo). Solo documentación. CC-MAP.
  - Cubre: FR-020, constitución §16.
  - Criterio: `grep -n "geo.py\|catalog_loader\|schema_check" CODEMAP.md` muestra las filas reales; cada archivo de código nuevo aparece en `CODEMAP.md` (`git status --short` contra el mapa).

- [ ] T024 Crear `docs/borradores/geografia-pais.md` (apuntes para la memoria, C9–C12): un párrafo con la regla de frontera (borde incluido) y de empates (`ADM0_A3` menor) con su motivo, `NULL` = «Sin país asignado», unicidad de `ADM0_A3` (177), resultado de la muestra real de un día con las cifras de `geo_real_day.out`, la limitación de precisión del catálogo 110m (FAQ 19, `FUENTES-Y-LICENCIAS.md`) y los límites conocidos de research.md. Solo documentación.
  - Cubre: C11, FR-018.
  - Criterio: el archivo existe y las cifras citadas coinciden con las evidencias (revisión manual).

- [ ] T025 Comprobaciones finales y parada: `git diff --stat -- specs/001-contratos-y-modelo/contracts sql/001_schema.sql docs/enunciado` vacío (SC-009); `uv run python scripts/check_env_example.py` con código 0; `grep -rn "Co-Authored-By\|Generated with" specs/005-geografia-pais docs/borradores/geografia-pais.md` sin resultados; actualizar el estado de `spec.md` y `bitacora.md`. Después, **detenerse y esperar la revisión del alumno** (sin commit ni merge).
  - Cubre: FR-017, SC-009, constitución §16, §19.
  - Criterio: los tres comandos dan el resultado indicado y el trabajo queda sin commit.

## Dependencias entre bloques

`B1 → B2 → B3 → B4 → B5`. Dentro del bloque 4, T015 precede a T016, T017, T018 y T020; T020 precede a T021; T016 y T017 necesitan T014. T019 solo necesita T005.

## Trazabilidad

| ID | Tareas |
|---|---|
| C9 | T001, T003–T005, T010–T013, T016, T017, T019, T021 |
| C10 | T002, T003, T008, T009, T021 |
| C11 | T004, T005, T012, T013, T016, T024 |
| C12 | T004, T005, T016, T017, T019, T021 |
| Prueba 5 | T017, T021 |
| Prueba 7 | T004, T016, T021 |
| Retoma de `003` (T062–T067, T069, T080) | T006–T009, T014, T021 |
| C13 (sintéticos) | T015, T017, T018, T020 |
