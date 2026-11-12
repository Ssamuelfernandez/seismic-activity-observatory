# Investigación: mediciones-costes (011)

Decisiones de diseño con alternativas. Las marcadas «(prov. n)» son las provisionales adoptadas de «Preguntas para el alumno» (spec).

## D1. Dónde corre y cómo se lee el equipo (prov. 1)

- **Decisión**: servicio `tests` (perfil `test`), que ya tiene el administrador, la red de Compose y `scripts/`, `data/catalogo` y `data/historical` montados. Se añade solo un montaje de escritura para las evidencias. CPU, núcleos y RAM salen de `/proc/cpuinfo`, `/proc/meminfo`, `os.cpu_count()` y los límites de cgroup; SO y versiones, de `platform` y de las bibliotecas. El modelo de equipo anfitrión y su potencia son «PENDIENTE (alumno)».
- **Motivo**: los roles de servicio no pueden crear esquemas; reutilizar `tests` evita un servicio nuevo (FR-028).
- **Alternativas**: ejecutar en el anfitrión con el puerto de Postgres publicado (no está publicado, §10); un servicio nuevo (viola FR-028).
- **Límite**: lo visible es la VM de Docker Desktop, no el PC; `equipo.md` lo dice.

## D2. Memoria sin `psutil` (prov. 2)

- **Decisión**: pico de `tracemalloc` para las estructuras en Python (lista, `dict`, índice `STRtree`, resultados); para Postgres, buffers (`shared hit/read`) y memoria de nodos del plan (`Memory`/`Sort Space`) de `EXPLAIN (ANALYZE, BUFFERS)`, y tamaños con `pg_total_relation_size`.
- **Motivo**: no tocar `pyproject.toml`/`uv.lock` (§11) ni la imagen.
- **Límite**: `tracemalloc` ralentiza el código; por eso **tiempo y memoria se miden en pasadas distintas** (una serie sin `tracemalloc` para el tiempo y una pasada aparte con él para el pico). No hay RSS del proceso.

## D3. Aislamiento (prov. 3)

- **Decisión**: esquema `bench` en la base del stack. Guardas: nombre fijo; si ya existe, aborta, salvo `--clean` y solo si su `COMMENT` lleva la marca del script (`SINTETICO-BENCH-TEMPORAL`); `try/finally` más manejador de `SIGTERM` para `DROP SCHEMA bench CASCADE`; comprobación `to_regnamespace('bench') IS NULL`; lista cerrada de sentencias de escritura que siempre califican con `bench.` (prueba estática sobre el código fuente).
- **Alternativa**: base temporal (las pruebas de integración ya la usan). Aislaría más, pero el brief fija el esquema.
- **Roles**: el administrador solo toca `bench`; las lecturas de `live`/`replay`/`public` van con `observatory_api` en transacción de solo lectura (FR-016).

## D4. Integración geográfica: misma regla en ambos métodos

- **Decisión**: el bucle ingenuo recorre los polígonos de `parse_country_catalog` (`common/geo.py`) **ordenados por `ADM0_A3` ascendente** con `geometry.covers(Point)` (borde incluido) y se detiene en el primer acierto (US2): con ese orden el primer acierto es el `ADM0_A3` menor, que es la regla de empate de `assign_country`. El método con `STRtree` llama a `assign_country`.
- **Motivo**: FR-003 exige la misma regla; el orden previo la garantiza sin recorrer todo. Los puntos sin país recorren los 177 polígonos (peor caso).
- **Medición**: construir el índice (`build_country_index`) se mide aparte; el catálogo se parsea fuera de la medición.
- **Peor caso**: el conjunto «océano» (puntos sin país) se mide como conjunto aparte con los mismos tamaños.

## D5. Sin índice real sobre `event_id` (consecuencia de `LIKE`)

- **Decisión**: `CREATE TABLE bench.event_<N> (LIKE live.current_event INCLUDING DEFAULTS)`. Sin `INCLUDING CONSTRAINTS` (el `CHECK` de `source` solo admite los orígenes reales y rechazaría `synthetic_bench`) y sin `INCLUDING INDEXES` (la clave primaria sería un índice sobre `event_id` y no existiría el caso «sin índice»). `NOT NULL` sí se copia.
- **Consecuencia**: las comprobaciones de rangos las hace el generador (pruebas de `synth.py`): `mag`, `depth_km`, `lon`, `lat`, `time_ms`, `updated_ms` y `date_id` coherentes.
- **Índices**: las definiciones (`pg_indexes.indexdef` de `live.current_event`: clave primaria, `ix_current_event_time`, `ix_current_event_country_time`, `ix_current_event_mag`) se leen y se reescriben sustituyendo esquema, tabla y nombre del índice por `bench.event_<N>` y un sufijo; no se copia el DDL a mano (§15).

## D6. Repeticiones y presupuesto (prov. 6)

- **Decisión**: N = 15 tras un calentamiento descartado (FR-008). Presupuesto de tiempo **por combinación**: `BUDGET_SECONDS = 90`. `plan_repetitions(t_warmup, budget, n_max=15, n_min=3)` devuelve `clamp(floor(budget / t_warmup), 3, 15)`. Si el propio calentamiento supera el presupuesto, el calentamiento **cuenta como una de las repeticiones** (código Python puro, sin efectos de caché relevantes) y se hacen 2 más (N = 3 con 3 ejecuciones totales).
- **Estimación (SUPUESTO, a confirmar en la primera ejecución)**: bucle ingenuo a 100.000 puntos × 177 polígonos del orden de minutos por repetición; el peor caso (océano) con N = 3 puede ocupar unos 15–20 min. Tiempo total estimado de la corrida completa: menos de una hora.
- **Regla**: nunca se omite una combinación ni se estima sin medir; la N real va en cada celda. Si ni N = 3 cabe en un tiempo razonable, se pregunta antes de reducir el tamaño (spec, prov. 6).
- **Parámetros** `--repeats` y `--budget` permiten un ensayo rápido con valores bajos para pruebas; la evidencia final usa los valores por defecto.

## D7. Qué se mide en cada operación (K1, K2, K3)

- **a) Búsqueda por id**: 4 ids (primero, medio, último, ausente) × 4 estrategias. Lista: recorrido secuencial; `dict`: acceso por clave (la construcción del `dict` se mide aparte); Postgres sin y con índice (`event_id`): `SELECT … WHERE event_id = $1`, tiempo de cliente y `Execution Time` del plan.
- **b) Geografía**: conjuntos «mixto» (coordenadas de los eventos del tamaño N) y «océano» (sin país) × {ingenuo, `STRtree`}; tiempo de construcción y de consulta; pico `tracemalloc`.
- **c) Agregación**: Q4 (`date_trunc('hour', event_time AT TIME ZONE 'UTC')`) en ventana de un día y en tabla completa, sin y con `ix_current_event_time`.
- **Teoría (FR-006)**: lista O(n) medio y peor; `dict` O(1) medio y O(n) peor teórico; B-tree O(log n); `Seq Scan` O(n); bucle ingenuo O(n·p) con p = 177 polígonos y `STRtree` O(log p) más contraste de candidatos; agregación O(n) (más ordenación o `HashAggregate`).

## D8. E6: Q3 con dos umbrales y veredicto (prov. 4)

- **Problema**: la semilla son terremotos de M ≥ 4 (todos los 18.302), así que `mag >= 4` selecciona ~100 % de las filas y el planificador no usará `ix_current_event_mag`; el veredicto sería trivial y poco informativo.
- **Decisión**: Q3 se mide con el umbral de la spec (`mag >= 4`) **y** con un umbral selectivo `mag >= p99` calculado de los datos de ese tamaño (se registra su valor y la fracción de filas). Q2: `country_id = :c` con el país más frecuente de la semilla, en un mes y en todo el rango; la selectividad se registra.
- **Veredicto** por índice (`verdicts.py`, puro): «justificado» si el plan con índice usa el índice y el tiempo de ejecución baja respecto al plan sin él por encima del rango intercuartílico de ambos; «no justificado con estos datos» si el planificador no lo usa o no mejora; «no concluyente» si los rangos se solapan o N < 3. Cada veredicto cita los identificadores de medición. **Solo recomendación**; no se edita DDL ni contrato (prov. 4). El coste en espacio (tamaño del índice) y el `idx_scan` real acompañan al veredicto.
- **`ANALYZE`** tras cargar y tras cada creación o borrado de índice (FR del spec); caché caliente (calentamiento descartado).
- **Un índice cada vez**: se crea, se mide, se borra, para que el plan no mezcle índices.

## D9. Replicación sintética determinista (K4)

- **Decisión**: semilla `random.Random(20251113)` fijada y registrada. Tamaños ≤ 18.302: submuestra ordenada por `event_id` de la semilla. 100.000: réplicas con `event_id = synthetic-bench-<n>`, tiempo perturbado dentro del año 2025 (ms enteros, `event_time`, `date_id` derivados coherentes), `updated_ms ≥ event_time_ms`, `lon`/`lat`/`mag`/`depth_km` perturbados dentro de rangos válidos, `country_id` asignado con `assign_country` (misma geometría real), `source = 'synthetic_bench'`, `is_synthetic = true`. Las filas de submuestra también llevan prefijo y `is_synthetic` (FR-013: todas).
- **Etiquetas**: `COMMENT ON SCHEMA bench` y toda tabla o cifra derivada llevan «SINTÉTICO».
- **Verificación final**: 0 filas `synthetic-bench-%` o de origen bench en `live`, `replay`, `quarantine` y `exclusion`; `replay.*` y `usgs_historical` sin cambios; el total de `live` no se compara (el consumidor sigue ingiriendo).

## D10. Costes y transferencia (K6)

- **Medido**: `pg_total_relation_size` y `pg_indexes_size` de las tablas reales por esquema, tamaño de `data/historical/` y `data/catalogo/`, bytes bajo `/api/eventos` (límite por defecto y máximo), `/api/estadisticas` y `/api/salud` pedidos a `http://api:8000` desde el servicio `tests` (el nombre de servicio, §9).
- **Supuesto** (fórmula visible): volumen mensual de transferencia = visitas × bytes medidos; hardware = precio / (vida útil en meses); electricidad = vatios × horas × €/kWh; mantenimiento y horas de desarrollo = horas × tarifa.
- **«PENDIENTE (alumno)»**: horas de desarrollo, potencia del PC, precio y vida útil del equipo, €/kWh, horas de encendido, tarifa de nube de referencia, horas de mantenimiento, visitas mensuales. El código no lleva valores por defecto; la salida es «no calculable» hasta que se rellenen (`costs.py` devuelve un valor `PENDING` explícito, no un 0).
- **Cuota gratuita**: fila aparte para el túnel y el hosting estático con límite, fecha de consulta (a rellenar por el alumno si no se consulta) y consecuencia de superarla; 0 € solo si la cuota cubre el uso estimado y el coste real de la máquina y la electricidad sigue en sus filas. No se consulta la web durante la implementación: los límites son «PENDIENTE (alumno)» salvo que el alumno los aporte.

## D11. Razonamiento a 100 M y propuestas (K5, K7)

- **Decisión**: se redactan **después** de la medición y solo con cifras medidas: almacenamiento = bytes/fila (con índices) × 10^8; coste de cada operación según la tendencia observada entre 1.000, 10.000 y 100.000 (pendiente en escala log-log); particionado por `event_time`; qué índices conservar según E6; carga por lotes frente a una transacción por mensaje; varios consumidores (partición de Kafka por clave `event.id`). Cada extrapolación va marcada SUPUESTO con su fórmula; sin lenguaje de predicción (§21).
- **Propuestas** (K7): formato «problema (identificador de medición y cifra) → mejora → medición que la confirmaría». Una propuesta sin cifra se descarta.
- **Fuera**: Spark, Flink, Kubernetes, ML (§12).

## Límites conocidos (una línea cada uno)

- Un solo equipo, y el que se ve es la VM de Docker Desktop; no es una comparativa general.
- El stack en marcha añade ruido; la dispersión (rango intercuartílico, mínimo, máximo) lo recoge.
- `tracemalloc` mide Python, no Postgres; por eso la memoria de Postgres se informa por plan y tamaños.
- Los datos replicados a 100.000 no reproducen la distribución real de más años; sirven para la forma de la curva.
