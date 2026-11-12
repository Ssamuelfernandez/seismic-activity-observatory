# Tareas: mediciones-costes (011)

**Entrada**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md` (esta carpeta). **IDs**: K1 a K7 y E6 (K8 fuera de alcance).

21 tareas activas en 5 bloques (máximo 25 y 5), numeradas **T073–T093** para continuar la numeración de `010` (T059–T072). Formato: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = en paralelo (archivos distintos). Cada tarea lleva **Prueba** y **Cubre**. Todo código nuevo sigue `03 §7.4` (docstrings en español con la plantilla, identificadores en inglés, funciones de unas 30 líneas, archivos de 250 como máximo, lógica pura separada del I/O). Un test por comportamiento que pida un criterio de la spec; sin pruebas exhaustivas ni fuzz.

Notación: «sin Docker» = `.venv/Scripts/python.exe -m pytest -m "not integration" <ruta>`; «servicio `tests`» = `docker compose --profile test run --rm tests …`. Cada ejecución se guarda en `docs/evidencias/mediciones/T0##_*.txt`. Los archivos de código nuevos se anotan en `CODEMAP.md` en T093. Las decisiones «prov. n» son las 6 provisionales de la spec. Toda cifra, tabla o gráfico derivado de `bench` lleva la etiqueta SINTÉTICO.

## Bloque 1 — Utilidades, equipo, semilla y esquema `bench` (K2, K4)

- [x] T073 [P] [US1] **Estadísticos y presupuesto (puro)**: `scripts/benchmarks/stats.py` con `summarize(samples)` (mediana, cuartiles, rango intercuartílico, mínimo, máximo) y `plan_repetitions(t_warmup, budget, n_max=15, n_min=3)` (`research.md` D6; si el calentamiento supera el presupuesto, cuenta como una repetición y N = 3). Constantes con nombre: `N_MAX`, `N_MIN`, `BUDGET_SECONDS = 90`.
  - **Prueba (sin Docker)** `tests/scripts/test_bench_stats.py`: serie conocida da mediana e IQR esperados; `plan_repetitions(1, 90)` = 15, `(10, 90)` = 9, `(40, 90)` = 3, `(400, 90)` = 3 con calentamiento contado.
  - **Cubre**: K2; FR-008, FR-009; SC-002.

- [x] T074 [P] [US1] **Arnés de medición**: `scripts/benchmarks/measure.py` con `measure_time(fn, n_max, budget)` (calentamiento descartado, `time.perf_counter`, aplica `plan_repetitions`, devuelve las muestras y la N real) y `measure_peak_kib(fn)` (una pasada aparte con `tracemalloc`, pico en KiB base 1024; D2). Sin `psutil` (prov. 2).
  - **Prueba (sin Docker)** `tests/scripts/test_bench_measure.py`: función de `sleep` corto devuelve N muestras positivas y N real ≤ 15; función cara (reloj simulado) reduce N hasta 3 sin omitir; `measure_peak_kib` de una lista de 100.000 enteros da un valor mayor que el de una de 1.000.
  - **Cubre**: K2; FR-007, FR-008, FR-009; SC-002. Depende de T073.

- [x] T075 [P] [US1] **Equipo leído de la máquina**: `scripts/benchmarks/hardware.py` con funciones puras `parse_cpuinfo(text)`, `parse_meminfo(text)` y `read_machine()` (modelo de CPU, núcleos físicos y lógicos, RAM total, SO, versiones de Python, PostgreSQL y `shapely`, límites de cgroup si existen) y el render de `equipo.md`, con «PENDIENTE (alumno)» para el modelo de equipo anfitrión y la potencia (prov. 1). Sin `psutil`.
  - **Prueba (sin Docker)** `tests/scripts/test_bench_hardware.py`: textos de ejemplo de `/proc` dan los campos esperados; `equipo.md` contiene CPU, núcleos, RAM y SO y los campos del anfitrión «PENDIENTE (alumno)»; si falta `/proc`, el campo dice «no disponible», sin inventar.
  - **Cubre**: K2; FR-010; SC-002.

- [x] T076 [P] [US4] **Semilla real**: `scripts/benchmarks/seed.py` con `load_seed(directory)`: lee `manifest.json`, verifica los 13 sha256 con `historical/manifest.py`, deduplica con `historical/dedup.py` y devuelve los 18.302 eventos únicos; se detiene con error si falta un archivo o un sha256 no coincide (borde de la spec).
  - **Prueba (sin Docker)** `tests/scripts/test_bench_seed.py`: sobre `data/historical/` real da 18.302 eventos únicos y 13 sha256 verificados; con una copia temporal alterada de un archivo lanza error y no devuelve datos.
  - **Cubre**: K4; FR-014; SC-004.

- [x] T077 [US4] **Generador sintético (puro)**: `scripts/benchmarks/synth.py` con `build_rows(seed_events, size, rng_seed=20251113, locate)`: submuestra si `size` ≤ 18.302 y replicación determinista si es mayor (`research.md` D9); `event_id = synthetic-bench-<n>`, `source = synthetic_bench`, `is_synthetic = true`, tiempos/`updated`/`date_id` coherentes, rangos válidos, `country_id` con `common/geo.py::assign_country`, nulos conservados.
  - **Prueba (sin Docker)** `tests/scripts/test_bench_synth.py`: dos ejecuciones con la misma semilla dan filas idénticas; 100 % con prefijo e `is_synthetic`; ningún `source` real; las reglas de coherencia y rangos de `data-model.md` §1 se cumplen en las 100.000 filas; `size` pedido = filas devueltas. Depende de T076.
  - **Cubre**: K4; FR-013, FR-015; SC-004.

- [x] T078 [US4] **Ciclo de vida de `bench`**: `scripts/benchmarks/bench_schema.py` con `create_bench`, `drop_bench`, `clean_if_marked`, `verify_isolation(before, after)` y la lista cerrada de sentencias de escritura (todas con `bench.`); `try/finally` y manejador de `SIGTERM`; aborta si `bench` existe sin `--clean` o sin la marca `SINTETICO-BENCH-TEMPORAL`; sin base o sin administrador falla antes de crear nada (prov. 1 y 3). Tablas con `LIKE live.current_event INCLUDING DEFAULTS` (D5).
  - **Prueba**: (sin Docker) `tests/scripts/test_bench_sql_static.py` comprueba que toda sentencia de escritura del paquete califica con `bench.` y que no hay `live.`, `replay.`, `public.` ni `ingest.` en sentencias de escritura. (servicio `tests`) `tests/integration/test_bench_schema.py`: crea y elimina `bench`; aborta con un `bench` ajeno sin tocarlo; `--clean` solo elimina el marcado; una excepción a mitad deja `to_regnamespace('bench')` NULL; recuentos de `replay.*` y `usgs_historical` iguales antes y después.
  - **Cubre**: K4; FR-012, FR-013, FR-016, FR-017; SC-003.

## Bloque 2 — Operaciones a, b y c (K1, K2, K3, E6)

- [x] T079 [US1] **Carga e índices de `bench`**: `scripts/benchmarks/bench_load.py` con `load_table(conn, size, rows)` (`COPY`), `analyze(conn, table)`, `read_index_definitions(api_conn)` (de `pg_indexes` de `live.current_event` con el rol de solo lectura), `rewrite_index(defn, table, suffix)`, `create_index`/`drop_index` y `explain(conn, sql, params)` que guarda `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` en `planes/`. `ANALYZE` tras cargar y tras cada cambio de índice.
  - **Prueba**: (sin Docker) `rewrite_index` sustituye esquema, tabla y nombre y no deja `live.`; (servicio `tests`) carga 1.000 filas, el recuento es 1.000, los 4 índices se crean y se borran uno a uno y el plan guardado es JSON válido; los nombres de los índices se leen del esquema real, no se tecleen.
  - **Cubre**: E6, K3; FR-005, FR-007; SC-001. Depende de T078.

- [x] T080 [US1] **Operación a: búsqueda por id**: `scripts/benchmarks/op_search.py`; ids primero, medio, último y ausente; estrategias lista, `dict` (con su construcción medida aparte), Postgres sin índice y con el índice de `event_id`; cada medición con id `search.<estrategia>.<N>.<caso>` y teoría O(n)/O(1)/O(log n).
  - **Prueba**: (sin Docker) en `tests/scripts/test_bench_ops_pure.py`, lista y `dict` encuentran el mismo evento en los tres casos y devuelven «ausente» para el id ausente; (servicio `tests`) con N = 1.000 hay 16 mediciones (4 estrategias × 4 ids), los planes de Postgres muestran el nodo usado (`Seq Scan`/`Index Scan`) y se informa si no coincide con la teoría.
  - **Cubre**: K1, K2, K3; FR-001, FR-006; SC-001. Depende de T074, T077, T079.

- [x] T081 [P] [US2] **Operación b: integración geográfica**: `scripts/benchmarks/op_geo.py` con el bucle ingenuo (polígonos ordenados por `ADM0_A3`, `covers`, primer acierto; D4) y el método con `STRtree` de `common/geo.py`; conjuntos «mixto» y «océano» (puntos sin país); construcción del índice medida aparte; recuento de puntos con resultado distinto.
  - **Prueba (sin Docker)** en `tests/scripts/test_bench_ops_pure.py`: con el catálogo real y 1.000 puntos (mixtos y océano) ambos métodos dan el mismo `ADM0_A3` en el 100 % (0 diferencias) y el conjunto «océano» no asigna país; polígonos sintéticos con un punto en el borde y otro en dos polígonos dan el mismo resultado en ambos.
  - **Cubre**: K1, K2; FR-002, FR-003, FR-006; SC-001. Depende de T074, T077.

- [x] T082 [US3] **Operación c y E6**: `scripts/benchmarks/op_agg.py` y `verdicts.py`: Q4 (ventana de un día y toda la tabla) sin y con `ix_current_event_time`; Q3 con `mag >= 4` y con el umbral selectivo p99; Q2 con el país más frecuente en un mes y en todo el rango; un índice cada vez (D8); planes guardados; veredicto puro por índice («justificado», «no justificado con estos datos», «no concluyente») con los ids de medición citados.
  - **Prueba**: (sin Docker) `tests/scripts/test_bench_verdicts.py`: casos construidos (mejora clara con índice usado, índice no usado, rangos solapados, N = 3) dan el veredicto esperado y citan ids; (servicio `tests`) con N = 1.000 se obtienen sin y con índice para Q2, Q3 y Q4, con plan guardado y el `Execution Time` del plan junto al tiempo de cliente.
  - **Cubre**: K1, K2, E6; FR-004, FR-005; SC-001. Depende de T074, T079.

- [x] T083 [P] [US3] **Referencia real de índices (solo lectura)**: función en `scripts/benchmarks/storage.py` que, con el rol `observatory_api` en transacción de solo lectura, lee de `live.current_event` los índices (`pg_indexes`), su tamaño y `idx_scan` de `pg_stat_user_indexes`, y los recuentos de `replay.*` y `usgs_historical`; salida al `indices.md` junto a la medición sintética.
  - **Prueba (servicio `tests`)**: devuelve los 4 índices con tamaño y `idx_scan`; la transacción es de solo lectura (un `INSERT` intentado falla); el recuento `usgs_historical` es 18.302.
  - **Cubre**: E6; FR-005, FR-016, FR-019; SC-001.

## Bloque 3 — Almacenamiento, transferencia, costes y ejecución completa (K6)

- [x] T084 [P] [US5] **Almacenamiento medido**: completar `scripts/benchmarks/storage.py` con `pg_total_relation_size` y `pg_indexes_size` de las tablas reales por esquema, total por esquema, tamaño de `data/historical/` y `data/catalogo/` y bytes por fila derivados; el volumen de Docker solo si puede leerse (si no, «no disponible»).
  - **Prueba (servicio `tests`)**: bytes por fila = tamaño / filas con recuento real; cifras > 0; salida `almacenamiento.md`. Una función pura de bytes por fila se prueba sin Docker.
  - **Cubre**: K6; FR-019; SC-005.

- [x] T085 [P] [US5] **Transferencia medida**: `scripts/benchmarks/transfer.py` pide a `http://api:8000` (nombre de servicio) `/api/eventos` (con el límite por defecto y con el máximo), `/api/estadisticas` y `/api/salud` y guarda los bytes; el volumen mensual es SUPUESTO con las visitas «PENDIENTE (alumno)».
  - **Prueba (servicio `tests`)**: 3 rutas medidas con bytes > 0; sin visitas la fila mensual es «no calculable»; se usa `api:8000`, nunca `localhost`.
  - **Cubre**: K6; FR-020; SC-005.

- [x] T086 [US5] **Costes (puro)**: `scripts/benchmarks/costs.py` con las 6 filas de K6 (hardware con amortización, electricidad, almacenamiento, transferencia, mantenimiento, horas de desarrollo; MEDIDO/SUPUESTO, fórmula, entradas con origen y unidad), valor `PENDING` explícito sin valores por defecto y fila de cuotas gratuitas (límite, fecha de consulta y consecuencia como «PENDIENTE (alumno)»); render de `costes.md`.
  - **Prueba (sin Docker)** `tests/scripts/test_bench_costs.py`: 6 categorías exactas, todas con etiqueta y fórmula; sin entradas rellenadas el resultado es «no calculable» (nunca 0); con entradas de ejemplo en la prueba el resultado coincide con la fórmula; la fila de cuotas incluye «cuota gratuita ≠ coste cero». Depende de T084, T085.
  - **Cubre**: K6; FR-018, FR-021, FR-022; SC-005.

- [x] T087 [US1] **CLI y ejecución completa**: `scripts/benchmarks/run_benchmarks.py` (solo orquesta: `--sizes`, `--repeats`, `--budget`, `--clean`, `--yes`) y `report.py` (JSON, tablas, `tablas.md`, `indices.md`, `aislamiento.md`); añadir a `compose.yaml` el montaje de escritura `./docs/evidencias/mediciones:/app/evidence-mediciones` en `tests` (sin servicio nuevo). Ensayo con `--sizes 1000 --repeats 3 --budget 10`, luego la corrida completa con el stack en marcha (prov. 5), anotando N real y ruido.
  - **Prueba**: (sin Docker) `tests/scripts/test_bench_report.py`: tablas con unidades, N real y etiqueta «SINTÉTICO»; (servicio `tests`) el ensayo y la corrida completa terminan con código 0, `docker compose config --services` sigue con los 5 servicios (`tests` es del perfil `test`), `to_regnamespace('bench')` es NULL, 0 filas de bench en `live`, `replay`, `quarantine`, `exclusion`, `replay.*` y `usgs_historical` iguales, 0 celdas vacías y un plan por consulta de Postgres. Salida en `T087_corrida.txt`. Paso adicional: ejecutar una vez `docker compose config --services` y anotar el resultado en `T087_corrida.txt` (depende de cómo trate Compose los servicios con perfil: puede listar 5 o solo los sin perfil).
  - **Cubre**: K1, K2, K3, K4, E6; FR-007 a FR-009, FR-011, FR-017, FR-025, FR-026; SC-001 a SC-004. Depende de T073–T086.

## Bloque 4 — Razonamiento a 100 M y propuestas (K1, K5, K7; tras medir)

- [x] T088 [US5] **Teoría frente a observado (K1)**: redactar `docs/evidencias/mediciones/teoria_vs_observado.md` con coste medio, peor caso teórico y observado por operación, copiando cifras de `resultados.json` con su id de medición, y explicando cada discrepancia (p. ej. `Seq Scan` no peor a 1.000 filas) sin ocultarla.
  - **Prueba**: cada operación tiene las 3 columnas, cada cifra cita un id existente en `resultados.json` (comprobación con `grep` de los ids) y las discrepancias están explicadas.
  - **Cubre**: K1; FR-006; SC-001. Depende de T087.

- [x] T089 [US5] **Razonamiento a 100 M (K5)**: `docs/evidencias/mediciones/escalado.md` con almacenamiento (bytes por fila medidos × 10^8, con índices), coste por operación según la tendencia medida entre los 3 tamaños, particionado por `event_time`, índices que se conservan o descartan según E6, carga por lotes frente a una transacción por mensaje y varios consumidores (partición de Kafka por clave); cada extrapolación con fórmula y marca SUPUESTO; sin lenguaje de predicción ni de riesgo (§21).
  - **Prueba**: al menos 4 puntos de razonamiento, cada cifra con su origen (id de medición o `almacenamiento.md`) y su fórmula; `grep -i -E "riesgo|predic"` sin usos como conclusión.
  - **Cubre**: K5; FR-023; SC-006. Depende de T087, T088.

- [x] T090 [US5] **Propuestas ligadas a hallazgos (K7) y veredictos de índices**: en `escalado.md`, cada propuesta como «problema observado (id y cifra) → mejora → medición que la confirmaría»; sin propuestas genéricas ni fuera de §12; en `indices.md`, las recomendaciones sobre cada índice marcadas como propuesta al alumno, sin editar DDL ni contrato (prov. 4).
  - **Prueba**: 0 propuestas sin id de medición y cifra; `git diff --stat` de `sql/` y `specs/001-contratos-y-modelo/` vacío.
  - **Cubre**: K7, E6; FR-005, FR-024, FR-028; SC-006. Depende de T089.

## Bloque 5 — Procedimiento, borrador del README, evidencias y cierre (§16)

- [x] T091 [P] [US1] **Procedimiento reproducible**: `docs/evidencias/mediciones/procedimiento.md` con los comandos exactos, el orden, los requisitos (stack levantado, `.env`), el tiempo estimado real de la corrida y las fuentes de ruido; completar el campo del equipo anfitrión de `equipo.md` solo si lo aporta el alumno.
  - **Prueba**: seguir `quickstart.md` y `procedimiento.md` desde cero reproduce las mismas tablas (misma estructura y mismo ranking de estrategias por operación y tamaño; los valores pueden variar).
  - **Cubre**: K2; FR-011; SC-007.

- [x] T092 [US5] **Borrador del README §7**: `docs/borradores/mediciones-costes.md` con «Complejidad, mediciones y costes» (operaciones, tamaños, equipo, resultados clave, veredictos de índices como recomendación, costes con lo pendiente del alumno, razonamiento a 100 M), cifras copiadas de la evidencia y etiqueta SINTÉTICO donde corresponda; enlace desde `README.md`. No se edita `docs/memoria.md`.
  - **Prueba**: cada cifra del borrador aparece en `docs/evidencias/mediciones/`; las cifras de `bench` llevan SINTÉTICO; el enlace del README resuelve.
  - **Cubre**: K1 a K7, E6; FR-027; SC-004.

- [x] T093 [US5] **Evidencias y cierre**: `docs/evidencias/mediciones/README.md` con índice y veredicto SC-001 a SC-007; ejecutar `pytest -m "not integration"` completo y `pytest -m integration` en el servicio `tests`; actualizar `CODEMAP.md` (módulos `scripts/benchmarks/`, tests, evidencias; historial) y `specs/011-mediciones-costes/bitacora.md`. Detenerse y esperar la revisión del alumno (§19); sin commit ni merge.
  - **Prueba**: ambas suites en verde, cada ruta del `CODEMAP.md` existe (`ls`), `docker compose config --services` sin servicios nuevos, `git diff --stat` de contratos, `sql/`, `docs/enunciado/`, `pyproject.toml` y `uv.lock` vacío.
  - **Cubre**: K1 a K7, E6; FR-026, FR-028; SC-001 a SC-007; constitución §16. Depende de T091, T092.

## Dependencias

```
Bloque 1: T073 -> T074 ; T076 -> T077 ; T078 ; T075 (todas [P] salvo las cadenas)
Bloque 2: T078 -> T079 -> {T080, T082} ; T077 -> {T080, T081} ; T074 -> {T080, T081, T082} ; T083
Bloque 3: T084, T085 -> T086 ; T073..T086 -> T087
Bloque 4: T087 -> T088 -> T089 -> T090
Bloque 5: T091, T092 (tras T090) -> T093
```

## Cobertura de requisitos

| ID | Tareas |
|---|---|
| K1 | T080, T081, T082, T087, T088 |
| K2 | T073, T074, T075, T080, T081, T082, T087, T091 |
| K3 | T079, T080, T087 |
| K4 | T076, T077, T078, T087 |
| K5 | T089 |
| K6 | T084, T085, T086 |
| K7 | T090 |
| E6 | T079, T082, T083, T090 |
| K1 a K7, E6 (cierre) | T092, T093 |
| K8 | fuera de alcance |
