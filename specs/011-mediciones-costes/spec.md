# Feature Specification: Mediciones, complejidad y costes

**Feature Branch**: `011-mediciones-costes` (en `docs/planificacion/03-procedimiento-ejecucion.md` §4 figura como `016-mediciones-costes`; decisión del alumno: la carpeta real es `011`, no se renombra; el número es orientativo)

**Created**: 2026-11-13

**Status**: Draft (specify, clarify, plan, tasks y analyze hechos; las 6 decisiones provisionales de «Preguntas para el alumno» están adoptadas; pendiente la revisión del alumno antes de implementar)

**Input**: Feature `mediciones-costes` (roadmap F12): medir tiempo y memoria de tres operaciones con tres tamaños de entrada, justificar los índices con `EXPLAIN ANALYZE`, calcular los costes distinguiendo lo medido de lo supuesto y razonar el escalado a 100 millones de registros. K8 (ROI) **no se hace** y el ROI queda fuera de alcance (no hay un beneficio medible definido; no se inventa).

> Contratos de referencia, **sin modificar**: `specs/001-contratos-y-modelo/contracts/db-schema.md` (§3.3 columnas de `current_event`, §4 consultas Q1–Q5 e índices; la nota «Ningún índice se afirma como mejora hasta medirlo» y el candidato Q3 `ix_current_event_mag`). Esta spec los cita, no los repite. `docs/enunciado/`, `sql/001_schema.sql` y `.specify/memory/constitution.md` no se tocan; el checklist lo marca el alumno.

## Cobertura de requisitos

| ID | Qué cubre `mediciones-costes` | Dónde se comprueba |
|---|---|---|
| K1 (☐, EVAL) | Tres operaciones justificadas (búsqueda por id, integración geográfica, agregación por ventanas), con coste medio y peor caso teóricos y el observado | US1 a US3, FR-001 a FR-006, FR-020, SC-001 |
| K2 (☐) | Tiempo y memoria con 3 tamaños de entrada; equipo, procedimiento y unidades | US1 a US3, FR-007 a FR-011, SC-002 |
| K3 (☐) | Lista secuencial vs `dict` **y** consulta sin/con índice | US1, FR-001, SC-001 |
| K4 (☐) | Los datos replicados para escalar son sintéticos, marcados y fuera del análisis real | US4, FR-012 a FR-017, SC-003, SC-004 |
| K5 (☐) | Razonamiento a 100 millones de registros | US5, FR-023, SC-006 |
| K6 (☐) | Costes: hardware, electricidad, almacenamiento, transferencia, mantenimiento y horas de desarrollo; medido vs supuesto; cuota gratuita ≠ coste cero | US5, FR-018 a FR-022, SC-005 |
| K7 (☐) | Escalado y mejoras ligadas a problemas concretos observados | US5, FR-024, SC-006 |
| E6 (☐) | Cada índice de `current_event` justificado por su consulta con medición antes/después | US3, FR-005, FR-006, SC-001 |
| K8 | **No se hace** (ROI fuera de alcance) | — |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Búsqueda de versiones por id: lista, `dict`, Postgres sin y con índice (Priority: P1)

El alumno obtiene, para tres tamaños de entrada, cuánto cuesta localizar un evento por `event_id` con cuatro estrategias y puede explicar por qué difieren.

**Why this priority**: K1 (EVAL), K2 y K3 son obligatorios y esta operación es la base de la idempotencia (Q5/Q6 de `db-schema.md` §4).

**Independent Test**: ejecutar el script de la operación «búsqueda por id» y obtener, por cada estrategia y tamaño, mediana y dispersión de tiempo, memoria y, para Postgres, los planes `EXPLAIN (ANALYZE, BUFFERS)` guardados.

**Acceptance Scenarios**:

1. **Given** una colección de N ids (N = 1.000, 10.000 y 100.000), **When** se buscan ids situados al principio, en el medio, al final y ausentes, **Then** se mide cada estrategia (recorrido secuencial de lista, `dict`, consulta en Postgres **sin** índice sobre `event_id`, consulta con índice) y se informa el caso medio y el peor caso por separado.
2. **Given** las consultas de Postgres, **Then** el plan guardado muestra el nodo que el planificador usó (`Seq Scan` o `Index Scan`) y su tiempo de ejecución, y se contrasta con el tiempo medido desde el cliente.
3. **Given** el resultado, **Then** el informe explica cualquier discrepancia con la teoría (por ejemplo, que a 1.000 filas el `Seq Scan` no sea peor) en lugar de ocultarla.

---

### User Story 2 - Integración geográfica: bucle ingenuo vs `STRtree` con el catálogo real (Priority: P1)

Se mide asignar país a N puntos con un bucle ingenuo sobre todos los polígonos de `data/catalogo/paises.geojson` frente al índice espacial `STRtree` que usa el proyecto.

**Why this priority**: es la operación más cara del consumidor y la que justifica el `STRtree` (C9–C12 ya implementados); K1 y K2 la piden.

**Independent Test**: para N = 1.000, 10.000 y 100.000 puntos, obtener tiempos y memoria de ambos métodos y comprobar que asignan el mismo país a cada punto.

**Acceptance Scenarios**:

1. **Given** los 177 polígonos reales y N puntos, **When** se ejecuta el bucle ingenuo (todos los polígonos, parando en el primer acierto) y la asignación con `STRtree` de `common/geo.py`, **Then** ambos devuelven el mismo `ADM0_A3` (o ambos ninguno) en el 100 % de los puntos; cualquier diferencia se lista y se explica.
2. **Given** los puntos sin país (océano), que obligan al bucle ingenuo a recorrer los 177 polígonos, **Then** se informan aparte como peor caso.
3. **Given** la construcción del índice, **Then** su tiempo y memoria se miden por separado del tiempo por punto (se amortiza o no según N).

---

### User Story 3 - Agregación por ventanas e índices de `current_event` (E6) (Priority: P1)

Se mide `GROUP BY date_trunc('hour', event_time AT TIME ZONE 'UTC')` con y sin índice en `event_time`, y se contrastan con la medición los otros dos índices de `current_event`.

**Why this priority**: K1, K2 y **E6** (obligatorio): `db-schema.md` §4 deja `ix_current_event_mag` como candidato «que se mantiene solo si `EXPLAIN ANALYZE` lo justifica» y exige medir antes de afirmar cualquier mejora.

**Independent Test**: sobre tablas del esquema temporal con 1.000, 10.000 y 100.000 filas, ejecutar Q4 con y sin `ix_current_event_time`, Q3 con y sin `ix_current_event_mag` y Q2 con y sin `ix_current_event_country_time`, y guardar los planes.

**Acceptance Scenarios**:

1. **Given** Q4 sobre una ventana estrecha (un día) y sobre toda la tabla, **When** se ejecuta sin índice y con él, **Then** se guardan ambos planes y tiempos y se informa si el planificador usó el índice; si no lo usa en alguna ventana, se dice y se explica con el plan, sin forzarlo.
2. **Given** Q3 (`mag >= 4`) y Q2 (`country_id = :c` en un intervalo), **When** se miden sin y con su índice, **Then** cada índice queda con veredicto «justificado», «no justificado con estos datos» o «no concluyente», citando su medición; ese veredicto **no modifica** `sql/001_schema.sql` ni `db-schema.md` (se propone al alumno; ver Preguntas).
3. **Given** el esquema real, **When** se lee (solo lectura) `pg_indexes`, el tamaño de cada índice y `pg_stat_user_indexes` (`idx_scan`) de `live.current_event`, **Then** se anota el coste en espacio y el uso real de cada índice junto a la medición sintética.
4. **Given** que el planificador depende de las estadísticas, **Then** tras cargar y tras crear/quitar cada índice se ejecuta `ANALYZE` de la tabla de bench y el procedimiento lo declara.

---

### User Story 4 - Datos sintéticos aislados del análisis real (Priority: P1)

Replicar datos para llegar a 100.000 filas no contamina `live`, `replay` ni ninguna cifra del análisis.

**Why this priority**: K4 y la constitución §7 (separación) son obligatorias; es el riesgo principal de la feature.

**Independent Test**: ejecutar el conjunto completo y comprobar con SQL que `live`, `replay`, `public` e `ingest` no contienen filas del bench y que el esquema `bench` ya no existe.

**Acceptance Scenarios**:

1. **Given** el arranque del script, **When** ya existe un esquema `bench`, **Then** el script **aborta** sin tocarlo, salvo que lleve el comentario de esquema temporal del propio script y se pida la limpieza explícita (`--clean`); nunca borra un esquema ajeno.
2. **Given** una ejecución normal (o interrumpida por error), **Then** el esquema `bench` se elimina al final (`DROP SCHEMA bench CASCADE` en la salida garantizada) y se verifica `to_regnamespace('bench') IS NULL`.
3. **Given** el final de la ejecución, **Then** hay 0 filas con `id` `synthetic-bench-…` o `is_synthetic = true` de origen bench en `live`, `replay`, `quarantine` y `exclusion`, y el recuento de `replay.*` y de las filas `usgs_historical` de `live.current_event` es idéntico al inicial (no se compara el total de `live`: el consumidor sigue ingiriendo feed real mientras el stack está encendido).
4. **Given** los resultados publicados, **Then** toda tabla, gráfico o cifra derivada de bench lleva la etiqueta «SINTÉTICO» y ninguna se usa en análisis, panel ni README como dato sísmico.

---

### User Story 5 - Costes, 100 millones de registros y propuestas (Priority: P1)

Se entrega una tabla de costes donde cada fila es MEDIDO o SUPUESTO con su fórmula, un razonamiento a 100 M de registros apoyado en lo medido y propuestas ligadas a problemas observados.

**Why this priority**: K5, K6 y K7 son obligatorios y se evalúan en el apartado de reflexión de la rúbrica.

**Independent Test**: abrir `costes.md` y comprobar que cada fila tiene etiqueta, fórmula, entradas y unidad, que las celdas sin dato son «PENDIENTE (alumno)» y que cada propuesta de K7 cita una medición concreta.

**Acceptance Scenarios**:

1. **Given** la tabla de costes, **Then** tiene exactamente las seis categorías de K6 (hardware con amortización, electricidad, almacenamiento, transferencia, mantenimiento, horas de desarrollo), cada una con MEDIDO o SUPUESTO, su fórmula y sus unidades.
2. **Given** una entrada que solo el alumno conoce (horas de desarrollo, potencia del PC, precio y vida útil del equipo, €/kWh, tarifa de nube de referencia), **Then** aparece como «PENDIENTE (alumno)» y el total de esa fila indica «no calculable», sin cifra inventada.
3. **Given** servicios con cuota gratuita (túnel, hosting estático), **Then** figuran con su coste en euros como 0 solo si la cuota cubre el uso estimado, anotando el límite de la cuota, la fecha en que se consultó y qué pagaría quien la supere; «gratuito» no se presenta como «sin coste» (el coste incluye la máquina y la electricidad que mantienen el túnel).
4. **Given** el razonamiento a 100 M, **Then** parte de cifras medidas (bytes por fila, tiempos por tamaño y su tendencia), muestra la extrapolación con su fórmula y la marca SUPUESTO, y no usa lenguaje de predicción ni de riesgo (constitución §21).

---

### Edge Cases

- **Operación muy lenta (bucle ingenuo a 100.000 puntos)**: se aplica un presupuesto de tiempo por combinación; si no se alcanzan las N repeticiones, se reduce N (mínimo 3), se informa la N real y nunca se omite la combinación ni se estima sin medir.
- **PostgreSQL no disponible o sin rol administrador**: el script falla antes de crear nada, con mensaje claro; no hay estado a limpiar.
- **Interrupción a mitad (Ctrl+C, error)**: el esquema temporal se elimina igualmente; si el proceso muere sin poder limpiar, `--clean` lo elimina (solo si lleva la marca del script).
- **Mismo seed, distinto equipo**: los tiempos cambian, la forma (cuál es más rápida, cómo crece) debe repetirse; los datos sintéticos son idénticos entre ejecuciones (semilla fija).
- **`seed` real incompleto o alterado** (falta un archivo o su sha256 no coincide con `manifest.json`): el script se detiene; no se mide con datos dudosos.
- **El planificador ignora un índice**: es un resultado válido (se documenta con el plan), no un fallo.
- **El stack sigue en marcha**: el consumidor y el productor comparten la máquina y la base durante la medición; se anota como fuente de ruido y la dispersión lo refleja (ver Preguntas).
- **Ejecución dentro de un contenedor**: la CPU y la RAM visibles son las del entorno de ejecución, no necesariamente las del anfitrión; se registran ambas cosas (ver FR-010).

### Límites conocidos (una línea cada uno)

- Es un trabajo de clase: se mide en un solo equipo, no es una comparativa de rendimiento general.
- La extrapolación a 100 M es un razonamiento, no una medición (se etiqueta SUPUESTO).
- La memoria de Postgres no se mide como proceso; se informa por buffers y memoria del plan, y la del cliente por el pico de `tracemalloc` (no es el RSS del proceso).
- Los costes dependen de cifras del alumno que esta feature no puede conocer.
- Corrida completa cercana a 1 h por el bucle ingenuo a 100.000 puntos; los costes dependen de datos del alumno (modelo/potencia del PC, horas, tarifas: PENDIENTE (alumno)); los costes se miden sobre los datos reales del alumno, no sobre un entorno de producción.

## Requirements *(mandatory)*

### Functional Requirements

**Operaciones y tamaños (K1, K2, K3)**

- **FR-001**: Debe medirse la **búsqueda de versiones por `event_id`** con cuatro estrategias: recorrido secuencial de una lista, `dict`, consulta en Postgres sin índice sobre `event_id` y consulta con índice, cada una con tres tamaños de entrada (por defecto 1.000, 10.000 y 100.000). Los ids buscados incluyen primero, medio, último y ausente.
- **FR-002**: Debe medirse la **integración geográfica** (asignar país a N puntos) con un bucle ingenuo sobre los polígonos reales de `data/catalogo/paises.geojson` y con el `STRtree` de `common/geo.py`, con los mismos tres tamaños. El método con `STRtree` MUST reutilizar `common/geo.py` (sin duplicar su lógica; constitución §14/§15); el bucle ingenuo solo existe como línea base de medición.
- **FR-003**: Ambos métodos geográficos MUST aplicar la misma regla de pertenencia (borde incluido, empate por `ADM0_A3` menor) y el informe MUST dar el número de puntos con resultado distinto (esperado 0; si no, se explica).
- **FR-004**: Debe medirse la **agregación por ventanas** `GROUP BY date_trunc('hour', event_time AT TIME ZONE 'UTC')` (Q4) con y sin índice en `event_time`, sobre una ventana estrecha y sobre toda la tabla, con los tres tamaños.
- **FR-005**: Para E6 se miden también Q3 (`mag >= 4`) con y sin `ix_current_event_mag` y Q2 (`country_id` en intervalo) con y sin `ix_current_event_country_time`, con los tres tamaños (Q3 además con un umbral selectivo, porque la semilla es M ≥ 4 y `mag >= 4` selecciona casi todas las filas; ver `research.md` D8), y se emite un veredicto por índice citando su medición. Las definiciones de los índices se leen del esquema real (`pg_indexes`), no se reescriben a mano.
- **FR-006**: Cada operación incluye una tabla «coste medio / peor caso teórico / observado» (K1), y todo planteamiento teórico se contrasta con la medición.

**Medición (K2)**

- **FR-007**: El tiempo se mide con `time.perf_counter`; la memoria de las estructuras en Python con `tracemalloc` (pico; sin `psutil` ni RSS, decisión provisional 2). Para Postgres se guardan `EXPLAIN (ANALYZE, BUFFERS)` completos y se informan buffers y memoria de nodos del plan.
- **FR-008**: Cada combinación operación × estrategia × tamaño se repite N veces tras descartar una vuelta de calentamiento (por defecto N = 15; N mínimo 3 si se reduce por tiempo, FR del borde) y se reporta **mediana** y **dispersión** (rango intercuartílico, mínimo y máximo), con la N real. Se declara que las consultas son con caché caliente.
- **FR-009**: Las unidades están en cada tabla (ms o s; KiB o MiB, indicando base 1024; filas; N).
- **FR-010**: El equipo se **lee de la máquina**, no se teclea: modelo de CPU, núcleos físicos y lógicos, RAM total, sistema operativo y versión, versión de Python, de PostgreSQL y de `shapely`. Si el script corre en un contenedor, se registran también los límites visibles y se avisa de que el anfitrión (modelo de equipo, potencia) lo completa el alumno.
- **FR-011**: El procedimiento de repetición (comandos exactos, orden, requisitos y tiempo estimado) está escrito en `docs/evidencias/mediciones/` y permite reproducir los resultados desde un clon limpio con el stack levantado.

**Datos sintéticos y aislamiento (K4, constitución §7)**

- **FR-012**: Los datos de bench viven **solo** en un esquema temporal `bench` de la base del stack, creado al empezar y eliminado al terminar (`DROP SCHEMA bench CASCADE` garantizado también ante errores), con un comentario de esquema que lo identifica como temporal y SINTÉTICO. Nunca se escribe en `live`, `replay`, `public` ni `ingest`.
- **FR-013**: Las tablas de bench derivan su estructura de `live.current_event` (`CREATE TABLE … (LIKE …)`) sin copiar el DDL a mano (constitución §15), y **todas** sus filas llevan `is_synthetic = true`, `id` con prefijo `synthetic-bench-` y `source` distinto de los reales.
- **FR-014**: La **semilla real** son los **18.302 eventos únicos de 2025** que ya están, versionados, en `data/historical/` (12 archivos mensuales de USGS, más el archivo del ensayo de hueco; `manifest.json` con sha256) y cargados en la base como `live.current_event` con `source = usgs_historical`. El script lee los **archivos** (verifica el sha256 del manifiesto y deduplica con `historical/dedup.py`) para ser reproducible sin base cargada; el recuento en la base se lee solo para contrastarlo (debe dar 18.302 en `usgs_historical`).
- **FR-015**: Los tamaños ≤ 18.302 se forman con submuestras de la semilla y los mayores se generan por replicación determinista (semilla pseudoaleatoria fija, registrada) con ids, tiempos y coordenadas perturbados dentro de rangos válidos; todo queda etiquetado sintético aunque parta de datos reales, y ninguna cifra de bench se usa como dato sísmico.
- **FR-016**: Las lecturas de las tablas reales (`live`, `replay`, `public`, catálogo de índices y tamaños) se hacen con el rol de solo lectura `observatory_api` en transacción de solo lectura; el rol administrador se usa únicamente para crear y destruir `bench` (ningún rol de servicio puede crear esquemas). Las sentencias de escritura del script se limitan a una lista cerrada que califica siempre con `bench.`, y una prueba estática lo verifica.
- **FR-017**: Antes y después de la ejecución se comprueban: ausencia de filas de bench fuera del esquema temporal, recuentos de `replay.*` y de `usgs_historical` en `live.current_event` sin cambios, y que `bench` no existe. El resultado se guarda como evidencia.

**Costes (K6)**

- **FR-018**: `costes.md` tiene una fila por categoría (hardware con amortización, electricidad, almacenamiento, transferencia, mantenimiento, horas de desarrollo) con columnas: etiqueta MEDIDO o SUPUESTO, fórmula, entradas con su origen, unidad y resultado.
- **FR-019**: Almacenamiento MEDIDO: `pg_total_relation_size` de cada tabla real y sus índices (lectura), el total por esquema, el tamaño de `data/historical/`, `data/catalogo/` y el volumen de Docker de Postgres/Kafka si puede leerse, con bytes por fila derivados.
- **FR-020**: Transferencia MEDIDA: bytes reales de respuestas de `/api/eventos`, `/api/estadisticas` y `/api/salud` (con `limit` por defecto y con el máximo) a partir de peticiones locales; el volumen mensual resultante es SUPUESTO (visitas × bytes) con las visitas a rellenar.
- **FR-021**: Las entradas que solo conoce el alumno (horas de desarrollo, potencia del PC en vatios, precio y vida útil del equipo, €/kWh, horas de encendido, tarifa de nube de referencia, horas de mantenimiento) son campos «PENDIENTE (alumno)»; el script no inventa ni rellena por defecto ninguna de ellas, y la fila resultante dice «no calculable» hasta que se rellenen.
- **FR-022**: Se incluye una fila o nota explícita de cuotas gratuitas (hosting estático, túnel y los demás servicios usados) con límite, fecha de consulta y consecuencia de superarlo; cuota gratuita no es coste cero.

**Escalado, 100 M y propuestas (K5, K7)**

- **FR-023**: El apartado de 100 millones de registros estima almacenamiento (bytes por fila medidos × 10^8, con índices), coste de cada operación (según la tendencia medida: lineal, logarítmica…) y razona al menos: particionado por fecha (`event_time`), qué índices se conservan o se descartan según E6, carga y escritura por lotes frente a una transacción por mensaje, y varios consumidores (partición de Kafka por clave). Cada extrapolación va marcada SUPUESTO con su fórmula.
- **FR-024**: Cada propuesta de escalado o mejora (K7) cita el problema concreto observado (la medición con su cifra), la medida propuesta y qué medición confirmaría el efecto; no hay propuestas genéricas sin cifra, ni mejoras fuera del alcance de la constitución (§12: sin Spark, Flink, Kubernetes ni ML).

**Salida y cierre (constitución §16)**

- **FR-025**: Los scripts son reproducibles y viven en `scripts/benchmarks/` (decisión por `CODEMAP.md`: `scripts/` ya aloja los CLI de verificación y el servicio `tests` los monta en solo lectura), con la lógica pura (estadísticos, generación de datos, cálculo de costes) separada del I/O (base, archivos, máquina), funciones de una sola responsabilidad e identificadores en inglés (constitución §13, §14). Las pruebas viven en `tests/scripts/` (las de integración del ciclo de vida de `bench`, en `tests/integration/`, como las demás features).
- **FR-026**: Los resultados (JSON con cada repetición, tablas Markdown, planes `EXPLAIN`, `equipo.md`, `costes.md`, el procedimiento) se guardan en `docs/evidencias/mediciones/`.
- **FR-027**: El borrador del apartado de mediciones y costes del README (§7 «Complejidad, mediciones y costes» del índice de la memoria) se redacta en `docs/borradores/mediciones-costes.md` con cifras copiadas de la evidencia y etiqueta SINTÉTICO donde corresponda; en el cierre se enlaza desde el README y `CODEMAP.md` se actualiza. `docs/memoria.md` lo rellena el alumno.
- **FR-028**: La feature no modifica contratos, `sql/001_schema.sql`, `docs/enunciado/` ni el checklist; no añade servicios a Compose ni cambia el comportamiento de las features cerradas, y no incluye ROI (K8).

### Key Entities

- **Operación**: búsqueda por id, integración geográfica o agregación por ventanas (con las consultas Q2, Q3 y Q4 de E6).
- **Estrategia**: variante medida de una operación (lista, `dict`, sin índice, con índice, bucle ingenuo, `STRtree`).
- **Tamaño de entrada**: número de filas o puntos (1.000, 10.000, 100.000).
- **Medición**: serie de N tiempos y un pico de memoria para una combinación operación × estrategia × tamaño, con mediana y dispersión.
- **Equipo**: CPU, RAM, SO y versiones leídas de la máquina de ejecución.
- **Esquema `bench`**: esquema temporal con datos SINTÉTICOS derivados de la semilla real.
- **Semilla real**: los 18.302 eventos únicos de 2025 de `data/historical/`.
- **Fila de coste**: categoría, etiqueta MEDIDO/SUPUESTO, fórmula, entradas, unidad y resultado o «PENDIENTE (alumno)».
- **Propuesta**: problema observado (cifra y medición) → mejora → medición que la confirmaría.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las 3 operaciones de K1 y las 2 consultas extra de E6 (Q2, Q3) tienen resultados para los 3 tamaños, y los pares exigidos por K3 (lista/`dict` y sin/con índice) y por E6 (Q2, Q3 y Q4 antes/después) están completos: 0 celdas vacías; el plan `EXPLAIN` de cada consulta de Postgres está guardado.
- **SC-002**: Cada celda de resultado tiene mediana, dispersión, N real, unidad y, cuando procede, memoria; `equipo.md` contiene CPU, núcleos, RAM y SO leídos por el script (0 campos tecleados a mano salvo el modelo de equipo anfitrión si se ejecuta en contenedor).
- **SC-003**: Tras la ejecución completa `to_regnamespace('bench')` es NULL y hay 0 filas de bench en `live`, `replay`, `quarantine`, `exclusion`; los recuentos de `replay.*` y de `usgs_historical` en `live.current_event` coinciden con los iniciales.
- **SC-004**: 100 % de las filas de bench tienen `is_synthetic = true` y el prefijo `synthetic-bench-`; 100 % de las tablas y cifras derivadas de bench en los documentos llevan la etiqueta SINTÉTICO; la semilla real se verifica con 13 sha256 del manifiesto y da 18.302 eventos únicos.
- **SC-005**: `costes.md` tiene 6 de 6 categorías, todas con etiqueta MEDIDO/SUPUESTO y fórmula; 0 cifras sin origen (las entradas del alumno figuran como «PENDIENTE (alumno)»); el almacenamiento es el medido con `pg_total_relation_size` y archivos.
- **SC-006**: El apartado de 100 M tiene como mínimo 4 puntos de razonamiento (particionado por fecha, índices, lotes, varios consumidores) y cada propuesta de K7 cita una medición concreta por identificador; 0 propuestas sin cifra.
- **SC-007**: Repetir el procedimiento desde un clon limpio, con el stack levantado, produce tablas con la misma estructura y el mismo ranking de estrategias por operación y tamaño (los valores absolutos pueden variar); las pruebas de los scripts pasan en verde y `CODEMAP.md` y las evidencias están actualizadas.

## Assumptions

- Hay stack levantado con la base cargada (`007-api` y `006-historico-2025` cerradas); el rol administrador (`POSTGRES_USER`) está disponible para crear `bench`, como ya hacen las pruebas de integración con el servicio `tests`.
- La base es PostgreSQL 16 y sus índices actuales son los de `sql/001_schema.sql`; la feature los mide, no los cambia.
- Los tres tamaños son los del brief (1.000, 10.000, 100.000); no se añade un cuarto tamaño.
- Solo hay un equipo de medición (el del alumno).
- Fuera de alcance: K8/ROI, ML, Spark/Flink/Kubernetes, panel o informes de calidad, nuevas rutas de API, cambios de esquema o de contratos, y pruebas de carga del stack completo.

## Clarifications

### Session 2026-11-13

- Q: ¿La semilla real se lee de los archivos o de la base? → A: De los archivos de `data/historical/` (verificados con sha256 y deduplicados con `historical/dedup.py`), porque así el procedimiento se reproduce desde un clon sin depender de la carga; de la base solo se leen recuentos, tamaños, índices y `idx_scan` (solo lectura, rol de la API) para contrastar y para las mediciones de coste.
- Q: ¿Cómo se define la estructura de las tablas de bench sin duplicar el contrato? → A: Con `CREATE TABLE bench.… (LIKE live.current_event INCLUDING DEFAULTS)` (sin `INCLUDING CONSTRAINTS`, porque el `CHECK` de `source` rechazaría el origen sintético, y sin `INCLUDING INDEXES`, para poder medir «sin índice») y los índices con la definición leída de `pg_indexes` sustituyendo el esquema; así no se copia el DDL (constitución §15) y el bench sigue al esquema real.
- Q: ¿Cómo se mide la memoria? → A: `tracemalloc` (pico) para las estructuras en Python (sin RSS ni `psutil`, ver Preguntas 2); para Postgres, buffers y memoria de nodos del plan (`EXPLAIN (ANALYZE, BUFFERS)`), porque la memoria del servidor no es atribuible a una consulta.
- Q: ¿Qué estadístico y cuántas repeticiones? → A: Mediana y rango intercuartílico (más mínimo y máximo), N = 15 tras una vuelta de calentamiento descartada; la mediana resiste a los picos de otros procesos del equipo y la N se reduce (mínimo 3) solo en combinaciones muy lentas, informando la N real.
- Q: ¿Caché fría o caliente en Postgres y estadísticas del planificador? → A: Caché caliente (tras descartar el calentamiento) y `ANALYZE` tras cada carga y cada creación o borrado de índice, para que el plan refleje lo que el planificador haría en producción; se declara en el procedimiento.
- Q: ¿Qué se considera «peor caso» en cada operación? → A: Lista: id ausente (recorre todo); `dict`: no se espera peor caso observable con claves de texto, se anota la teoría; Postgres sin índice: `Seq Scan` completo; bucle ingenuo: puntos sin país (recorre los 177 polígonos); agregación: ventana que abarca toda la tabla.
- Q: ¿Qué ocurre con un coste cuyo dato no existe? → A: La celda queda «PENDIENTE (alumno)» y el resultado «no calculable»; el script no usa valores por defecto (enunciado: distinguir medido de supuesto; brief: no inventar cifras).
- Q: ¿Se usan las tablas reales como un punto de medición más? → A: Sí, solo lectura: los tamaños, índices y `idx_scan` reales de `live.current_event` (~18.302 históricas más el feed en vivo) acompañan a las mediciones sintéticas como punto de referencia real, sin ejecutar nada que escriba.
- Q: ¿Dónde se redacta el apartado del README? → A: Como borrador en `docs/borradores/mediciones-costes.md` (patrón de las demás features), con enlace desde el README en el cierre; `docs/memoria.md` y el checklist los edita el alumno.

### Preguntas para el alumno

Estado: las seis decisiones siguientes están reflejadas en `plan.md` y `tasks.md`. Las seis: Decisión confirmada por supervisor; el alumno puede revisarla en la defensa.

1. **Dónde se ejecuta y de dónde sale el administrador** — *Decisión confirmada por supervisor; el alumno puede revisarla en la defensa*: en el servicio `tests` (perfil `test`, que ya tiene `POSTGRES_USER`/`POSTGRES_PASSWORD` y monta `scripts/`, `data/catalogo` y `data/historical`); en la implementación se añade solo un montaje de escritura para `docs/evidencias/mediciones` (sin servicio nuevo). CPU y RAM se **leen de la máquina** visible (la VM de Docker Desktop); el modelo y la potencia del PC anfitrión son un campo «PENDIENTE (alumno)» (FR-010).
2. **Dependencia `psutil`** — *Decisión confirmada por supervisor; el alumno puede revisarla en la defensa*: **no se añade**; `pyproject.toml` y `uv.lock` no se tocan (constitución §11). La memoria en Python es el pico de `tracemalloc`; para Postgres, buffers del plan y tamaños con `pg_total_relation_size`. CPU/RAM salen de `os`, `platform` y `/proc` (Linux del contenedor).
3. **Aislamiento: esquema `bench` en la base del stack** — *Decisión confirmada por supervisor; el alumno puede revisarla en la defensa* con las protecciones de FR-012 a FR-017 (nombre fijo, aborta si existe, `DROP` garantizado, lecturas con rol de solo lectura, comprobación final).
4. **Veredicto de índices (E6)** — *Decisión confirmada por supervisor; el alumno puede revisarla en la defensa*: solo se **recomienda** en la evidencia; no se edita `sql/001_schema.sql` ni `db-schema.md`. Si procede quitar un índice, se hace como cambio de contrato aparte, decidido por el alumno.
5. **Stack durante la medición** — *Decisión confirmada por supervisor; el alumno puede revisarla en la defensa*: en marcha, sin pararlo; se declara como fuente de ruido que la dispersión recoge.
6. **Presupuesto de tiempo del bucle ingenuo a 100.000 puntos** — *Decisión confirmada por supervisor; el alumno puede revisarla en la defensa*: presupuesto por combinación con N reducida (mínimo 3); el valor concreto está en `plan.md` (D6). Si ni 3 repeticiones caben en el tiempo razonable, se pregunta antes de reducir el tamaño.
