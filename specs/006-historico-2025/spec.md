# Feature Specification: Histórico 2025

**Feature Branch**: `006-historico-2025`

**Created**: 2026-11-05

**Status**: Implemented (2026-11-05). 25/25 tareas. Evidencias: `docs/evidencias/historico-2025/` (609 unitarias y 85 de integración sin fallos; 18302 eventos únicos cargados, recarga sin cambios). Tareas diferidas: ninguna. Pendiente del alumno: revisar, marcar B12–B18 y pasar `docs/borradores/historico-2025.md` a la memoria.

**Input**: User description: "Descargar el histórico de 2025 de USGS (mundial, M>=4, solo terremotos, por meses) con procedencia registrada y cargarlo en la base reutilizando el procesamiento del consumidor, con origen `usgs_historical`. Cubre B13-B18 y documenta el procedimiento de recuperación de un hueco de más de 24 h (B12)."

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `006-historico-2025` (F6). El nombre (slug) es el estable.

## Clarifications

### Session 2026-11-05

Respuestas con la opción recomendada (la herramienta no puede preguntar al alumno). Lo que toca contratos, alcance o dependencias está en "Preguntas para el alumno" con decisión provisional.

- Q: ¿Qué valor lleva `source` de los eventos históricos? → A: `usgs_historical`. El brief escribe `historical`, pero `kafka-message.md` §3, `db-schema.md` y el `CHECK` de `sql/001_schema.sql` fijan `usgs_historical`; usar otro valor haría fallar la inserción. No es un cambio de contrato: es el valor que el contrato ya reserva para este origen.
- Q: ¿Por Kafka o por lote? → A: Por lote directo al esquema `live`, sin Kafka. Lo fija `kafka-message.md` §1 («el histórico 2025 se carga por lote directamente en el esquema `live`») y `db-schema.md` §1 («la carga histórica solo escribe en `live`; nunca en `replay`»). La justificación completa va en el borrador de memoria (FR-018). Las reglas son las mismas porque se reutilizan las funciones de `common/` (B16).
- Q: ¿Dónde se guardan los archivos? → A: En `data/historical/` (no en `data/raw/`, que está en `.gitignore` por ser regenerable). Se versionan si la suma de los 12 archivos y el manifiesto es menor de ~50 MB (se comprueba tras la descarga); si no, los archivos van a `.gitignore` y solo se versionan script, `manifest.json` y checksums.
- Q: ¿Los archivos guardan la respuesta cruda o ya deduplicada? → A: Cruda (tal como la devolvió USGS, sin tocar), porque es la prueba de procedencia (B15). La deduplicación se aplica al armar el conjunto de eventos únicos, y el manifiesto registra registros por archivo, duplicados descartados y total único (B14). El cargador aplica la misma regla (por `id`, se queda con el `updated` mayor), de modo que no depende de que el descargador haya corrido.
- Q: ¿Qué intervalos usan los meses y cómo se evita perder el extremo? → A: Meses naturales en UTC, con `starttime` incluido y `endtime` el primer instante del mes siguiente. Si USGS devuelve el evento del límite en dos consultas, la deduplicación lo resuelve. Un mes nunca se trunca: si `count > 20000` se divide en dos mitades (recursivo) y los trozos se guardan en el mismo archivo mensual `usgs_2025-MM.geojson` (el nombre no cambia; el manifiesto lista las consultas que lo componen).
- Q: ¿Qué hace el descargador si el recuento no cuadra? → A: Contrasta la suma de registros únicos con la consulta `count` de USGS para todo el año (y la de cada consulta con su `count`). Si difieren, termina con error y código distinto de 0 que muestra las dos cifras; no da el resultado por bueno ni corrige en silencio (B13). Límite conocido: USGS puede publicar revisiones entre la consulta `count` y la descarga; el error pide repetir la descarga.
- Q: ¿Se vuelve a descargar si ya existen los archivos? → A: No. Si un archivo mensual existe y su sha256 coincide con el del manifiesto, se reutiliza (B15, «descargar una vez y reutilizar»). Una opción explícita fuerza la descarga.
- Q: ¿Qué `ingested_at` llevan los eventos históricos? → A: La fecha de extracción registrada en el manifiesto para ese archivo. Así el dato refleja el instante en que USGS entregó la instantánea (B18), no el de la carga.
- Q: ¿Qué rol de base usa la carga? → A: `observatory_consumer`, que ya tiene los permisos de escritura que necesita (`current_event`, `event_version`, `quarantine`, `date_dim`, `country`). Evita tocar `sql/002_roles.sql`. La contraseña viene del entorno; nada de secretos en el repositorio.
- Q: ¿`is_synthetic` y `mode` de los eventos históricos? → A: `is_synthetic = false` y `mode = live` (el histórico vive en el esquema `live`, `db-schema.md` §1).
- Q: ¿Qué referencia al origen llevan los eventos y la cuarentena del lote? → A: `kafka_topic`, `kafka_partition` y `kafka_offset` quedan en `NULL` (el contrato lo admite para la carga por lote, `db-schema.md` §3.2). La referencia al original en la cuarentena es el JSON del evento y su `original_sha256`, más el nombre del archivo en el log.
- Q: ¿Qué pasa con un evento histórico inválido? → A: Va a cuarentena con el mismo motivo y la misma regla que en vivo (`common/validation.py`); no se cuenta como cargado y no detiene la carga (constitución §6). No se añaden motivos nuevos.
- Q: ¿Se solapa el histórico con el feed en vivo? → A: No en la práctica: el histórico cubre 2025 y el feed solo la última ventana. Si un mismo `id` llegara por ambos caminos, rigen las reglas de versiones por `updated` (constitución §2); el histórico nunca pisa una versión posterior.
- Q: ¿Qué hace la recarga si USGS cambió una revisión desde la extracción? → A: Nada: se cargan los archivos guardados, que son una instantánea a la fecha de extracción. Una nueva descarga es una decisión explícita y entonces las reglas de versiones aplican la versión con `updated` mayor (B18).

## User Scenarios & Testing *(mandatory)*

Los «usuarios» son quien evalúa el pipeline (profesor y alumno que lo defiende) y los servicios que usarán el histórico más adelante (API de comparación, panel, replay). Esta feature no añade pantallas ni endpoints.

### User Story 1 - Descargar 2025 con procedencia, sin truncar (Priority: P1)

Una ejecución del descargador deja en disco los 12 archivos mensuales y un manifiesto con la procedencia de cada consulta, y confirma que el total cuadra con el recuento de USGS.

**Why this priority**: B13 y B15 son obligatorios y todo lo demás parte de los archivos.

**Independent Test**: Ejecutar el descargador contra USGS real una vez; comprobar 12 archivos, manifiesto completo, sha256 correctos y total igual al `count` de USGS.

**Acceptance Scenarios**:

1. **Given** el año 2025, **When** se ejecuta el descargador, **Then** existen `usgs_2025-01.geojson` … `usgs_2025-12.geojson` y un `manifest.json`, y cada consulta usa `minmagnitude=4`, `eventtype=earthquake` y `orderby=time-asc` (B13).
2. **Given** el manifiesto, **When** se lee, **Then** cada archivo tiene URL(s) de consulta, fecha de extracción, nº de registros y sha256, y el sha256 coincide con el contenido real del archivo (B15).
3. **Given** un mes con más de 20000 eventos (se simula con un USGS de prueba), **When** se descarga, **Then** se divide en intervalos menores, el total del mes coincide con el `count` y no se pierde ningún evento ni se trunca en silencio (B13).
4. **Given** una descarga completa, **When** termina, **Then** el log muestra el nº de registros por consulta, los duplicados descartados, el total único y el `count` de USGS; si las cifras no cuadran, el proceso termina con error (B13, B14).
5. **Given** los archivos ya descargados y válidos, **When** se vuelve a ejecutar el descargador, **Then** no hace ninguna petición a USGS salvo la opción de forzar (B15).

---

### User Story 2 - Un evento, una vez: deduplicación entre intervalos (Priority: P1)

Los eventos que aparecen en dos intervalos consecutivos (extremos incluidos en ambos) se cuentan una sola vez.

**Why this priority**: B14 obligatorio; sin él los totales del panel serían incorrectos.

**Independent Test**: Con archivos de prueba que repiten un `id` en dos meses, el conjunto único tiene un solo registro de ese `id` y se conserva el de `updated` mayor.

**Acceptance Scenarios**:

1. **Given** dos archivos con el mismo `id` en su frontera, **When** se arma el conjunto único, **Then** el `id` aparece una vez, con el `updated` mayor, y el manifiesto cuenta un duplicado descartado.
2. **Given** el conjunto único de 2025, **When** se comprueba, **Then** el número de `id` distintos es igual al número de eventos del conjunto (B14).

---

### User Story 3 - Cargar el histórico con las mismas reglas que el vivo (Priority: P1)

El cargador lee los archivos y escribe cada evento con las mismas funciones de validación, transformación (ms a UTC), país por geometría y escritura idempotente del consumidor, con `source = usgs_historical`.

**Why this priority**: B16 y B17 obligatorios y la verificación central de F6.

**Independent Test**: Cargar los archivos sobre una base limpia: eventos en `current_event` = `id` únicos − `id` en cuarentena; repetir la carga y comprobar que nada cambia.

**Acceptance Scenarios**:

1. **Given** una base con esquema y catálogo de países, **When** se carga el histórico, **Then** `live.current_event` contiene `id` únicos de los archivos menos los de cuarentena, todos con `source = usgs_historical`, `mode = live` e `is_synthetic = false`, y `event_version` tiene una fila por cada `(id, updated)` único.
2. **Given** la carga ya hecha, **When** se repite, **Then** no se inserta ni cambia ninguna fila en `current_event`, `event_version` ni `quarantine` (0 diferencias).
3. **Given** un evento histórico con `mag` nula, con magnitud o profundidad negativas, o con coordenadas inválidas, **When** se carga, **Then** se tratan igual que en vivo: nulo se conserva, negativos válidos, inválido a cuarentena con motivo y referencia al original (constitución §5 y §6).
4. **Given** un evento histórico en tierra y otro en mar, **When** se carga, **Then** el primero recibe `country_id` por geometría y el segundo `NULL`, con la misma regla de frontera y empate que en vivo (constitución §4).
5. **Given** la carga terminada y un reinicio de los contenedores (sin `down -v`), **When** se consulta la base, **Then** el histórico sigue presente (B17).
6. **Given** que la carga y el consumidor comparten funciones, **When** se revisa el código del cargador, **Then** no contiene validación, conversión de tiempos ni asignación de país propias (B16).

---

### User Story 4 - Procedimiento documentado: por qué lote y cómo cubrir un hueco (Priority: P2)

La documentación explica por qué el histórico va por lote y no por Kafka, que es una instantánea a la fecha de extracción, el comando reproducible de carga y cómo recuperar un hueco de más de 24 h con el mismo mecanismo.

**Why this priority**: B12, B16 (documentar la elección), B17 y B18 obligatorios/solicitados, pero son texto sobre lo ya construido.

**Independent Test**: Seguir el procedimiento de hueco sobre un intervalo de prueba y comprobar que los eventos aparecen una sola vez.

**Acceptance Scenarios**:

1. **Given** el README, **When** se lee, **Then** contiene el comando de descarga y el de carga, repetibles, y qué esperar (B17).
2. **Given** el borrador de memoria, **When** se lee, **Then** hay un párrafo de «por qué lote» apoyado en los contratos (volumen, ventana de retención de 7 días de Kafka, sin necesidad de tiempo real, misma lógica reutilizada) y uno de «instantánea a la fecha de extracción, no todas las revisiones pasadas» (B16, B18).
3. **Given** una parada del productor de más de 24 h, **When** se sigue el procedimiento documentado, **Then** se descarga el intervalo del hueco, se carga con el mismo cargador y los eventos ya presentes no se duplican ni retroceden de versión (B12).

---

### Edge Cases

- **Mes con más de 20000 eventos**: se divide; nunca se trunca. En 2025 con M>=4 ningún mes lo supera (se espera del orden de mil por mes), por lo que el camino se demuestra con un USGS de prueba.
- **Fallo de red, 429 o 5xx durante la descarga**: el descargador reintenta con espera creciente un número acotado de veces y, si agota, termina con error nombrando el mes; los archivos ya buenos se conservan (se reutilizan al reintentar).
- **Archivo del manifiesto ausente o con sha256 distinto**: el cargador se detiene y nombra el archivo; no carga datos de procedencia dudosa.
- **Mismo `id` con distinto `updated` en dos archivos**: se conserva el `updated` mayor; solo ese pasa a estado actual.
- **Evento con `mag` nula**: se conserva `NULL`; cuenta en los totales (constitución §5).
- **Eventos antiguos del histórico que USGS revisó después de la extracción**: la base conserva la revisión de la fecha de extracción (límite conocido, B18).
- **Precisión del país**: la del catálogo simplificado (límite conocido de `geografia-pais`).

## Requirements *(mandatory)*

### Functional Requirements

**Descarga y procedencia (B13, B14, B15)**

- **FR-001**: El descargador MUST pedir a USGS, por cada mes natural de 2025 en UTC, los eventos mundiales con `minmagnitude=4`, `eventtype=earthquake` y `orderby=time-asc`, y MUST guardar cada mes en `data/historical/usgs_2025-MM.geojson` tal como lo devuelve USGS (B13).
- **FR-002**: Antes de descargar un intervalo, MUST consultar su `count` a USGS; si es mayor de 20000, MUST dividirlo en intervalos menores hasta que cada consulta quede por debajo del límite, y MUST NOT truncar ni descartar eventos en silencio (B13).
- **FR-003**: MUST escribir un `manifest.json` con, por archivo: URL(s) de consulta con sus parámetros, fecha de extracción (UTC), nº de registros por consulta y por archivo y sha256 del archivo; y, en total: duplicados descartados, eventos únicos y `count` de USGS para el año (B15).
- **FR-004**: MUST deduplicar por `id` entre intervalos conservando el registro con `updated` mayor, y MUST comprobar que el nº de `id` distintos es igual al nº de eventos únicos (B14).
- **FR-005**: MUST contrastar el total único con la consulta `count` de USGS para el año y, si no coincide, terminar con error (código distinto de 0) mostrando ambas cifras (B13).
- **FR-006**: MUST registrar en el log el nº de registros por consulta (B13) y MUST reutilizar los archivos existentes cuyo sha256 coincida con el manifiesto sin pedirlos de nuevo, salvo opción explícita de forzar (B15).
- **FR-007**: Ante timeout, 429 o 5xx MUST reintentar con espera progresiva y un máximo de intentos; al agotarlos MUST terminar con error que nombra el mes y conservar los archivos ya válidos.

**Carga (B16, B17)**

- **FR-008**: El cargador MUST leer los archivos listados en el manifiesto, comprobar su sha256 y, si alguno falta o no coincide, detenerse nombrando el archivo.
- **FR-009**: El cargador MUST procesar cada evento con las mismas funciones que el consumidor (validación, conversión de tiempos, asignación de país, construcción de filas y escritura idempotente, reglas de versiones por `updated`) y MUST NOT duplicar esa lógica (B16, constitución §14).
- **FR-010**: Cada evento cargado MUST llevar `source = usgs_historical`, `mode = live`, `is_synthetic = false`, `ingested_at` igual a la fecha de extracción del manifiesto para su archivo y referencia Kafka `NULL`; el evento original MUST conservarse íntegro en `event_version.original`.
- **FR-011**: Un evento inválido MUST ir a `live.quarantine` con motivo y referencia al original, sin detener la carga; MUST NOT añadirse ningún motivo nuevo (constitución §6).
- **FR-012**: La carga MUST ser repetible: ejecutarla de nuevo sobre los mismos archivos MUST NOT insertar ni modificar ninguna fila (constitución §1).
- **FR-013**: Al terminar, el cargador MUST escribir un resumen con eventos únicos leídos, escritos como actuales, versiones nuevas, a cuarentena y sin cambios, y MUST comprobar que `current_event` (histórico) = únicos − cuarentena.
- **FR-014**: La carga MUST usar nombres de servicio para llegar a la base (constitución §9), credenciales del entorno y MUST escribir solo en el esquema `live`, nunca en `replay`.
- **FR-015**: Los datos cargados MUST persistir al reiniciar los contenedores sin repetir la descarga (B17).

**Documentación (B12, B16, B17, B18)**

- **FR-016**: El README MUST incluir los comandos reproducibles de descarga y carga, la ubicación de los archivos y el resultado esperado (B17).
- **FR-017**: La documentación MUST explicar la elección «lote en lugar de Kafka» apoyándose en los contratos (B16).
- **FR-018**: Un borrador para la memoria (`docs/borradores/historico-2025.md`) MUST contener: el párrafo «por qué lote», el párrafo de «instantánea a la fecha de extracción» (B18) y el procedimiento de recuperación de un hueco de más de 24 h con este mismo mecanismo (B12).
- **FR-019**: Si la suma de los archivos y el manifiesto es menor de ~50 MB MUST versionarse junto al manifiesto; si no, MUST añadirse a `.gitignore` y versionarse solo script, manifiesto y checksums.

**Contratos y cierre**

- **FR-020**: `kafka-message.md`, `db-schema.md`, `sql/001_schema.sql` y `docs/enunciado/` MUST NOT modificarse. Si algo obliga, se escala al alumno.
- **FR-021**: Al terminar MUST existir evidencia en `docs/evidencias/historico-2025/` (salida de pruebas, log de la descarga con registros por consulta, consulta SQL de la verificación y recarga sin diferencias) y `README` y `CODEMAP.md` actualizados (constitución §16).
- **FR-022**: Las pruebas MUST usar un USGS simulado y archivos pequeños etiquetados como sintéticos (`synthetic-…`) para los casos de mes >20000, duplicados y eventos inválidos; los datos reales son solo los de la descarga de 2025.

### Key Entities

- **Archivo mensual** (`data/historical/usgs_2025-MM.geojson`): respuesta cruda de USGS para un mes; solo lectura una vez guardado.
- **Manifiesto** (`data/historical/manifest.json`): procedencia de cada archivo (consultas, fecha de extracción, registros, sha256) y totales (duplicados, únicos, `count` de USGS).
- **Evento histórico**: evento de los archivos que, tras el procesamiento común, vive en `live.current_event` / `live.event_version` con `source = usgs_historical`.
- **Cuarentena** (`live.quarantine`): eventos históricos inválidos con motivo y original.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras una descarga completa existen 12 archivos y un manifiesto cuyos sha256 coinciden al 100 % con el contenido, y el total único es igual al `count` de USGS para 2025 (0 diferencia).
- **SC-002**: Con un USGS simulado que devuelve un mes de más de 20000 eventos, el total descargado de ese mes es igual al del recuento simulado y 0 eventos se pierden.
- **SC-003**: En el conjunto único de 2025, el nº de `id` distintos es igual al nº de eventos (0 repetidos); con dos archivos de prueba que comparten un `id`, queda 1.
- **SC-004**: Tras la carga sobre base limpia, `count(live.current_event WHERE source = 'usgs_historical')` es igual a `id` únicos de los archivos menos `id` distintos en cuarentena (0 diferencia).
- **SC-005**: Repetir la carga 2 veces más deja 0 filas nuevas y 0 filas modificadas en `current_event`, `event_version` y `quarantine`.
- **SC-006**: Un evento histórico con `mag` nula queda con `mag` nulo (0 casos con valor 0), uno con latitud 145 produce 1 fila de cuarentena y uno en el Atlántico queda con `country_id` nulo.
- **SC-007**: Tras reiniciar los contenedores sin borrar volúmenes, el recuento de SC-004 no cambia.
- **SC-008**: El cargador no contiene validación, conversión de tiempos ni asignación de país propias: 0 duplicados de lógica, comprobado por revisión y porque la prueba de la carga usa las funciones comunes.
- **SC-009**: `kafka-message.md`, `db-schema.md`, `sql/001_schema.sql` y `docs/enunciado/` no cambian (`git diff` vacío).

## Assumptions

- `002` a `005` están implementadas: Compose, PostgreSQL con esquema y roles, `public.country` cargado al arrancar el consumidor y funciones de procesamiento en `common/` y `consumer/`.
- La API de USGS (`fdsnws/event/1`) admite `count`, `starttime`, `endtime`, `minmagnitude`, `eventtype`, `orderby` y `format=geojson`, con un máximo de 20000 resultados por consulta.
- El catálogo de países lo asegura el propio cargador reutilizando `consumer/catalog_loader.py` (upsert repetible, `research.md` D1); si falta el archivo del catálogo o el esquema, el cargador falla con un mensaje claro y no escribe países vacíos.
- Los datos de 2025 de M>=4 caben en una sola carga de unos pocos miles de eventos al mes; el rendimiento no es un objetivo.
- La reutilización de las funciones del consumidor puede exigir adaptarlas para aceptar un evento sin referencia Kafka; es un cambio de código compartido, no de contrato.

## Fuera de alcance

Replay, API, frontend, reconciliación exhaustiva de revisiones antiguas (B11), publicación del histórico por Kafka, descarga de años distintos de 2025 como producto, endurecimiento de casos raros (fuzz, auditorías), modificación de contratos y automatización del procedimiento de hueco más allá de lo indicado en la pregunta 1.

## Preguntas para el alumno

1. **Recuperar un hueco de más de 24 h (B12): ¿solo documentar o añadir opciones de intervalo?** Decisión provisional: el descargador acepta, además del modo 2025, un intervalo opcional `--start/--end` (UTC) que guarda `usgs_gap_<start>_<end>.geojson` y lo añade al manifiesto; el cargador lo procesa igual. Motivo: sin intervalo el procedimiento no sería reproducible con el mismo mecanismo. Alternativa: solo texto con la URL de USGS y copiar el archivo a mano (más corto, menos reproducible). Recomendación: las opciones de intervalo (cambio pequeño). Afecta a alcance y número de tareas.
2. **Reutilización del procesamiento del consumidor.** El brief y el roadmap citan `common.processing.process_event()`, que no existe con ese nombre: hoy la canalización es `consumer/pipeline.py::process_record`, con `RawRecord` de Kafka. Decisión provisional: el cargador construye un mensaje con el formato del contrato (`source=usgs_historical`, `mode=live`) y reutiliza las funciones comunes, adaptando solo lo mínimo para admitir referencia Kafka `NULL` (el contrato la admite). Se decide en `plan`; ningún contrato cambia. Recomendación: no duplicar `validate_message` ni `build_event_rows`. **Resuelta en `plan` (`research.md` D1)**: el cargador llama a `consumer.pipeline.process_record` tal cual; el único cambio compartido es que `MessageRef.partition/offset` admiten `None` (columnas `kafka_*` nulas).
3. **Tamaño de los archivos (~50 MB).** Decisión provisional: se mide tras la primera descarga real. Se estima por debajo de 50 MB (unos 16 000 eventos), por lo que irían versionados; si no, a `.gitignore`. Recomendación: versionar si caben, para que el clon sea autosuficiente (B17).
