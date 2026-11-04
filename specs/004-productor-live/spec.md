# Feature Specification: Productor en vivo

**Feature Branch**: `004-productor-live`

**Created**: 2026-11-05

**Status**: Implemented (2026-11-05). 22/22 tareas verificadas. Evidencias: `docs/evidencias/productor-live/`. Tareas diferidas: ninguna. Pendiente del alumno: pasar `docs/borradores/productor-live.md` a la memoria (B2, B11, B12).

**Input**: User description: "Productor real que consulta USGS cada POLL_SECONDS y publica en `earthquakes.live` sin duplicar. Cubre B1-B12 y A10. Pruebas de aceptación 1 (evento nuevo, real) y 2 (reenvío)."

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `003-productor-live`; la carpeta es `004-productor-live` porque Spec Kit numera por orden de creación. En los documentos se usa el nombre (slug), que es estable.

## Clarifications

### Session 2026-11-05

Respuestas con la opción recomendada (la herramienta no puede preguntar al alumno). Lo que toca alcance o trabajo ya cerrado está en "Preguntas para el alumno" con decisión provisional.

- Q: ¿Qué feed consulta por defecto? → A: `summary/all_day.geojson` (ENUNCIADO §4.1), configurable con una variable de entorno. Es la ventana de 24 h que justifica la explicación de B12 (hueco tras una parada de más de 24 h).
- Q: ¿Sobre qué se calcula el hash de `raw_response` (B5)? → A: Sobre el contenido de `features` (JSON canónico: claves ordenadas, sin espacios). El cuerpo guardado es la respuesta completa. Motivo: `metadata.generated` cambia cada minuto, así que un hash del cuerpo entero sería siempre distinto y no evitaría copias idénticas. Compatible con `db-schema.md` §3.9 (sha256 hex de 64 caracteres). Se compara con el último `ingest_run` correcto.
- Q: ¿Qué retención tiene `raw_response` (B5, la fija esta feature según `db-schema.md` §3.9)? → A: 7 días (la misma que el tema de Kafka), configurable; la purga se hace al terminar cada ciclo correcto con la consulta Q9. Estimación: ~150 KB por respuesta distinta (medido en `explore_usgs_salida.txt`) y unos cientos al día, del orden de cientos de MB en 7 días: asumible. `ingest_run` no se purga (una fila pequeña por consulta).
- Q: ¿Cómo es el backoff ante 429, 5xx o timeout (B10)? → A: Exponencial con jitter: espera inicial de 2 s, se duplica en cada fallo consecutivo, tope de 60 s, con jitter aleatorio (entre 50 % y 100 % de la espera calculada). El tope de 60 s es menor que `HEALTH_MAX_AGE_SECONDS` (120 s) para que el contenedor no se marque `unhealthy` por un fallo de USGS. Tras un ciclo correcto vuelve a esperar `POLL_SECONDS`.
- Q: ¿Cuál es el timeout HTTP? → A: 10 s por defecto, configurable (`HTTP_TIMEOUT_SECONDS`). La latencia medida es ~0,2 s.
- Q: ¿Cuándo se renueva el latido del productor? → A: Al terminar cada ciclo completado, sea correcto o con error de USGS controlado (el productor está vivo). No se renueva si falla Kafka o PostgreSQL (el contenedor puede quedar `unhealthy`, coherente con `infra-compose`).
- Q: ¿Qué pasa si Kafka falla a mitad de un ciclo? → A: Se interrumpe el ciclo en el evento que falló; los ya confirmados quedan marcados y el que falló no. El error se registra en el log (no hay segunda fila en `ingest_run`: esa tabla describe la consulta al feed, que fue correcta) y el siguiente ciclo reintenta (con el backoff de arriba). Nada se marca sin ack.
- Q: ¿Qué `ingested_at` llevan los mensajes? → A: El instante en que se recibió la respuesta del feed, el mismo para todos los eventos del ciclo (`kafka-message.md` §3).
- Q: ¿Qué se hace con eventos sin `id` o sin `updated`? → A: Se publican (contrato `kafka-message.md` §3: la invalidez tiene prioridad sobre la exclusión) con clave nula si falta el `id`; no se anotan en `ingest_state` porque no se pueden comparar. El consumidor los lleva a cuarentena, que es idempotente por hash y motivo. Límite conocido: se vuelven a publicar en cada ciclo; con datos reales de USGS es un caso excepcional.
- Q: ¿Qué se hace con un evento cuyo `type` falta o es nulo? → A: Es distinto de `earthquake`: se excluye con `observed_type` nulo (columna que lo admite).
- Q: ¿Se renombra `PRODUCER_INTERVAL_SECONDS`? → A: Sí, a `POLL_SECONDS` (nombre del roadmap F4), con valor por defecto 60 (B1). La coherencia con el latido se mantiene: `POLL_SECONDS` ≤ `HEALTH_MAX_AGE_SECONDS` / 2 = 60. Se actualizan `.env.example`, `compose.yaml` y `config.md` en el plan/tareas (A10).
- Q: ¿Hasta dónde se demuestra la prueba 1 aquí? → A: Hasta PostgreSQL: un evento real de USGS llega a `live.current_event` pasando por el consumidor existente (sin modificarlo). Que se vea en la API, el mapa y el análisis es de `pruebas-aceptacion`, cuando existan esas piezas.

## User Scenarios & Testing *(mandatory)*

Los "usuarios" son quien evalúa el pipeline (profesor y alumno que lo defiende) y el consumidor ya existente, que recibe los mensajes. Esta feature sustituye el productor mínimo de `002-infra-compose` (eventos sintéticos) por uno que lee el feed real de USGS.

### User Story 1 - Un evento real de USGS llega a PostgreSQL (Priority: P1)

Con el sistema levantado, el productor consulta el feed de USGS, publica los terremotos en `earthquakes.live` y el consumidor existente los deja en PostgreSQL como eventos reales (`is_synthetic = false`, `source = usgs_feed`).

**Why this priority**: Es la prueba 1 (evento nuevo, real) y el criterio de cierre de F4. Sin esto no hay datos reales.

**Independent Test**: Arrancar el stack, esperar un ciclo y consultar `live.current_event`; después esperar a que USGS publique un evento nuevo y comprobar que aparece una fila nueva con su `event_id`.

**Acceptance Scenarios**:

1. **Given** el stack levantado y `ingest_state` vacío, **When** termina el primer ciclo, **Then** cada evento de tipo `earthquake` de la respuesta se ha publicado una vez, con clave igual a su `id`, y `live.current_event` contiene una fila por cada uno, todas con `is_synthetic = false`.
2. **Given** un ciclo ya hecho, **When** USGS incorpora un evento que no estaba, **Then** en el ciclo siguiente se publica solo ese evento y aparece una fila nueva en `live.current_event` (prueba 1, hasta PostgreSQL).
3. **Given** un evento ya publicado, **When** USGS lo revisa con un `updated` mayor, **Then** se publica la nueva versión y el consumidor la aplica; si el `updated` es menor o igual, no se publica.
4. **Given** cualquier mensaje publicado, **When** se inspecciona, **Then** cumple `kafka-message.md` §3: `source = usgs_feed`, `mode = live`, `ingested_at`, `replay_at = null`, `is_synthetic = false` y `event` tal como lo entrega USGS, sin cambios (incluidos `mag` nulo y valores negativos).

---

### User Story 2 - No duplicar al repetir ciclos ni al reiniciar (Priority: P1)

El mismo evento no se publica dos veces, aunque la ventana de 24 h lo repita en cada respuesta y aunque el productor se pare y arranque.

**Why this priority**: Es B6 y la prueba 2 (reenvío) vista desde el productor.

**Independent Test**: Dos ciclos seguidos contando mensajes publicados; después parar y arrancar el contenedor y contar de nuevo.

**Acceptance Scenarios**:

1. **Given** un primer ciclo con N eventos publicados, **When** ocurre el segundo ciclo, **Then** no se publica ningún evento cuyo `id` y `updated` ya estuvieran publicados (solo los realmente nuevos o revisados, normalmente 0 a unos pocos).
2. **Given** el productor parado y vuelto a arrancar, **When** hace su primer ciclo, **Then** no republica los eventos ya marcados en `ingest_state` (el estado sobrevive en PostgreSQL, no en memoria).
3. **Given** un corte del proceso justo después del ack de Kafka y antes de marcar el evento, **When** reinicia, **Then** puede reenviar ese mensaje una vez; el consumidor lo tolera y el recuento en `live.current_event` y `live.event_version` no cambia (prueba 2).
4. **Given** una publicación que Kafka no confirma, **When** se examina `ingest_state`, **Then** el evento no está marcado como publicado.

---

### User Story 3 - Los fallos de USGS no corrompen el estado (Priority: P1)

Ante timeout, HTTP 429 o 5xx, o un cuerpo que no es JSON válido, el productor lo registra, espera con backoff y sigue, sin tocar el estado válido anterior.

**Why this priority**: B10 es obligatorio y tiene prueba con fallo simulado.

**Independent Test**: Un servidor simulado (mock) que devuelve 500, 429, un cuerpo lento y un cuerpo no JSON; después el mock vuelve a responder bien. Se compara `ingest_state` antes y después.

**Acceptance Scenarios**:

1. **Given** una respuesta 429 o 5xx, **When** el productor la recibe, **Then** guarda una fila en `ingest_run` con `status` y `error`, no publica, no modifica `ingest_state` y espera con backoff exponencial y jitter antes de reintentar.
2. **Given** una consulta que excede el timeout, **When** ocurre, **Then** se registra una fila en `ingest_run` con `error` (sin `status` ni hash) y se reintenta con backoff.
3. **Given** un cuerpo que no es JSON válido (o no es una colección de eventos), **When** llega, **Then** se registra el error en `ingest_run`, no se guarda en `raw_response` ni se publica nada, y `ingest_state` queda intacto.
4. **Given** fallos consecutivos y luego una respuesta correcta, **When** esta llega, **Then** el productor retoma el ritmo normal de `POLL_SECONDS` y publica solo lo que corresponda según `ingest_state`.

---

### User Story 4 - Originales, filtro y trazabilidad (Priority: P2)

Cada consulta deja rastro; el original se guarda antes de transformar; los que no son terremotos se excluyen con motivo; las copias idénticas no se acumulan.

**Why this priority**: B3, B4 y B5 son obligatorios, pero se comprueban sobre el mismo ciclo de la historia 1.

**Independent Test**: Un ciclo con una respuesta que incluye un evento de otro `type`; repetir con la misma respuesta; consultar `ingest_run`, `raw_response` y `live.exclusion`.

**Acceptance Scenarios**:

1. **Given** una respuesta correcta, **When** se procesa, **Then** hay una fila en `ingest_run` con fecha, URL, `status`, latencia en ms, número de eventos y hash, y el cuerpo original completo en `raw_response`, escrito antes del filtro y de la transformación.
2. **Given** una respuesta cuyo contenido de `features` es igual al de la consulta anterior, **When** se procesa, **Then** se registra su `ingest_run` pero no se añade fila a `raw_response`.
3. **Given** un evento con `properties.type` distinto de `earthquake`, **When** se procesa, **Then** no se publica y queda una fila en `live.exclusion` con `kind = non_earthquake_type`, el motivo, el `observed_type` y `is_synthetic = false`; repetir el ciclo no duplica la fila (unicidad `event_id, updated_ms, kind`).
4. **Given** respuestas guardadas hace más de 7 días, **When** termina un ciclo correcto, **Then** se purgan de `raw_response`.

---

### User Story 5 - Arranque robusto y configuración (Priority: P2)

El productor arranca aunque Kafka o PostgreSQL aún no estén listos, y su configuración vive en variables de entorno documentadas.

**Why this priority**: A4 y A10 ya estaban cubiertos para el productor mínimo; hay que mantenerlos con el productor real.

**Independent Test**: Arrancar el productor antes que Kafka; ejecutar el comprobador de `.env.example`.

**Acceptance Scenarios**:

1. **Given** Kafka o PostgreSQL no disponibles al arrancar, **When** arranca el productor, **Then** reintenta la conexión con espera creciente, deja constancia en el registro y empieza a consultar cuando ambos responden, sin terminar.
2. **Given** las variables nuevas (`POLL_SECONDS`, URL del feed, timeout, retención de originales), **When** se ejecuta `scripts/check_env_example.py`, **Then** `.env.example`, `compose.yaml` y el código coinciden y no hay secretos.
3. **Given** un valor de configuración inválido (p. ej. `POLL_SECONDS` mayor que la mitad del máximo del latido), **When** arranca, **Then** falla con un error que nombra la variable.

---

### Edge Cases

- Evento sin `id` o sin `updated`: se publica y lo trata el consumidor (ver Clarifications). Límite conocido: se republica cada ciclo.
- `mag` nulo o negativo, profundidad negativa: se publican tal cual (constitución §5).
- Respuesta correcta con 0 eventos: ciclo correcto, nada que publicar, sin error.
- Un evento que sale de la ventana de 24 h no se considera eliminado por USGS; la reconciliación exhaustiva es una ampliación (B11, texto en la memoria).
- Parada del productor de más de 24 h: los eventos que no vio quedan fuera del feed; se recuperan con el catálogo histórico, procedimiento documentado, no automatizado (B12, texto en la memoria).
- Límite conocido: no se respeta la cabecera `Retry-After`.
- Límite conocido: dos productores simultáneos no están soportados (hay uno).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (B1): Cada `POLL_SECONDS` (por defecto 60) el productor hace un GET al feed configurado con un timeout, y registra cada ciclo en el log.
- **FR-002** (B4): Por cada consulta con respuesta, guardar una fila en `ingest.ingest_run` (fecha, URL, status, latencia, número de eventos, hash) y el cuerpo original completo en `ingest.raw_response`, antes de filtrar o transformar.
- **FR-003** (B5): El hash se calcula sobre el contenido de `features`; `raw_response` solo recibe una fila si el hash difiere del de la última consulta correcta. Retención de `raw_response`: 7 días, configurable, con purga al terminar cada ciclo correcto. La política queda escrita en el README.
- **FR-004** (B3): Filtrar `properties.type == "earthquake"`; los demás no se publican y se registran en `live.exclusion` con `kind`, motivo, `observed_type` y `fetched_at`, de forma idempotente.
- **FR-005** (B6): Para cada evento de tipo `earthquake`, comparar `id` y `updated` con `ingest.ingest_state`: publicar si el `id` es nuevo o el `updated` es mayor; omitir si es igual o menor.
- **FR-006** (B7, B8): Publicar en `earthquakes.live` con clave = `event.id` y valor conforme a `kafka-message.md` §3 (`source = usgs_feed`, `mode = live`, `ingested_at`, `replay_at = null`, `is_synthetic = false`, `event` sin modificar). Los contratos se usan sin cambios.
- **FR-007** (B9): Esperar la confirmación de Kafka (`acks=all`, productor idempotente) por cada mensaje, y actualizar `ingest_state` (`last_updated_ms`, `published_at`) solo después de ese ack.
- **FR-008** (B10): Ante timeout, 429, 5xx o cuerpo no válido, registrar la consulta fallida en `ingest_run` con su error, no publicar, no modificar `ingest_state` ni `raw_response`, y esperar con backoff exponencial y jitter (2 s inicial, tope 60 s) hasta una respuesta correcta.
- **FR-009** (A4): Al arrancar, reintentar la conexión a Kafka y PostgreSQL hasta que estén listos, con constancia en el log.
- **FR-010** (A10): Toda la configuración del productor viene de variables de entorno presentes en `.env.example` y `compose.yaml`, sin secretos; `PRODUCER_INTERVAL_SECONDS` pasa a `POLL_SECONDS`.
- **FR-011**: El productor renueva el latido de `infra-compose` al completar cada ciclo (ver Clarifications) y deja de generar eventos sintéticos.
- **FR-012** (constitución §14): La lógica pura (hash, filtro, decisión de publicar, construcción del mensaje, cálculo del backoff) está separada de la E/S (HTTP, Kafka, PostgreSQL) y vive en código compartido o reutilizable por el histórico y el replay.
- **FR-013** (B2, B11, B12): La documentación (memoria/README) explica la respuesta del feed, los errores y la latencia (apoyándose en `explore_usgs.py`), la limitación de la ventana frente a eventos eliminados y cómo recuperar un hueco de más de 24 h con el catálogo histórico.
- **FR-014**: Pruebas con servidor simulado para 500, 429, timeout y JSON inválido; ejecución real contra USGS con el consumidor existente; evidencias en `docs/evidencias/productor-live/`.

### Fuera de alcance

Cambios en el consumidor; asignación de país; histórico 2025; replay; API y frontend; reconciliación exhaustiva de eventos eliminados; respetar `Retry-After`; fuzz, auditorías o endurecimiento de casos raros.

### Key Entities

- **Ciclo de consulta**: una ejecución del bucle; produce un `ingest_run` y, si el contenido cambia, un `raw_response`.
- **Estado de ingesta** (`ingest_state`): último `updated` publicado por evento.
- **Exclusión** (`live.exclusion`): evento descartado por no ser terremoto, con motivo.
- **Mensaje Kafka**: el definido en `kafka-message.md` §3; no se redefine aquí.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras el primer ciclo real, el número de filas en `live.current_event` (con `is_synthetic = false`) es igual al número de eventos `earthquake` de la respuesta (verificable con SQL contra `raw_response`).
- **SC-002**: En el segundo ciclo consecutivo, 0 mensajes publicados corresponden a un `id` y `updated` ya publicados.
- **SC-003**: Parar y arrancar el productor no publica ningún evento ya presente en `ingest_state` con el mismo `updated`.
- **SC-004**: Con un corte forzado entre el ack y el marcado, el recuento de `live.current_event` y `live.event_version` es el mismo antes y después del reenvío.
- **SC-005**: Con el servidor simulado, para cada uno de 500, 429, timeout y JSON inválido: 1 fila de error en `ingest_run`, 0 mensajes publicados y `ingest_state` idéntico antes y después; tras volver el servicio, el productor se recupera sin intervención.
- **SC-006**: Los tiempos de espera entre fallos consecutivos crecen (2, 4, 8… hasta 60 s) con jitter y nunca superan 60 s.
- **SC-007**: Una respuesta con contenido idéntico a la anterior no añade filas a `raw_response`; una purga elimina las de más de 7 días.
- **SC-008**: Un evento real nuevo de USGS aparece en `live.current_event` dentro de 2 ciclos desde que está en el feed (prueba 1, hasta PostgreSQL).
- **SC-009**: Las pruebas unitarias de funciones puras no necesitan Kafka, PostgreSQL ni red; `check_env_example.py` termina sin errores.

## Assumptions

- Kafka, PostgreSQL y el consumidor de `002`/`003` están disponibles y no se modifican.
- El feed por defecto es `all_day.geojson`; solo cambia la URL si se configura otra.
- Los contratos `kafka-message.md` y `db-schema.md` bastan sin cambios; el hash sobre `features` y la retención de 7 días son decisiones de esta feature que `db-schema.md` §3.9 le delega.
- El rol `observatory_producer` necesita `SELECT` y `DELETE` en `ingest.raw_response` (purga; el `WHERE` exige leer); `sql/002_roles.sql` lo concede hoy solo para insertar. Es un ajuste de `infra-compose`, no de los contratos (ver Preguntas). `db-schema.md` NO se edita: la feature solo concreta §3.9 y el `GRANT SELECT, DELETE` va en `sql/002_roles.sql` (no es contrato). En volúmenes ya creados hay que reaplicar el `GRANT` o hacer `down -v`.
- Límites conocidos: el timeout de `urllib` es por operación de socket, no sobre la descarga total; los eventos sin `id` o `updated` se republican en cada ciclo.
- Desviación de `CODEMAP.md`: se actualiza una sola vez en T021, no tarea a tarea (proporcionalidad; se confirma con el alumno).
- El producto es trabajo de clase de unas dos semanas, no de producción.

### Notas para el plan (sin diseñar)

Ciclo y orden de operaciones; estado de `ingest_state` y tabla de decisión `id + updated`; formato canónico del hash; backoff y latido; qué variables nuevas aparecen (URL del feed, timeout, retención); cómo el servicio de pruebas simula USGS; qué se hace con `common/synthetic_event.py` y con el check A1 de `verify_stack.py`.

## Preguntas para el alumno

1. **Retirar los eventos sintéticos del productor.** El productor mínimo publicaba un evento sintético por intervalo y el check A1 de `scripts/verify_stack.py` busca `event_id=synthetic-…` en el log del consumidor. *Decisión provisional:* el productor real solo publica datos reales; `common/synthetic_event.py` se conserva para pruebas y el check A1 se adapta (o se sustituye por un check con el mock de USGS) en esta feature. *Recomendación:* esa, porque la constitución §7 pide separar sintéticos y reales y el brief dice «sustituye el productor mínimo». Afecta a evidencias de `002` y `003`.
2. **Permiso `DELETE` (y `SELECT`) para la purga de `raw_response`.** *Decisión provisional:* añadir `GRANT SELECT, DELETE ON ingest.raw_response` a `observatory_producer` en `sql/002_roles.sql` y actualizar la tabla de §1.1 de `db-schema.md` solo si el alumno aprueba que cuente como cambio de contrato; si no, la purga se haría con un script aparte. *Recomendación:* conceder `DELETE` al productor (mínimo privilegio, su propia tabla). Nota: `postgres_init.sh` solo corre con volumen nuevo; un volumen existente necesita reaplicar el script o `down -v`.
3. **Retención de 7 días y hash sobre `features`.** *Decisión provisional:* las del apartado Clarifications. *Recomendación:* mantenerlas; si prefiere otro periodo, solo cambia el valor por defecto.
