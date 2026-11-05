# Feature Specification: API de consulta

**Feature Branch**: `007-api`

**Created**: 2026-11-05

**Status**: Implemented (2026-11-05). 25/25 tareas. Evidencias: `docs/evidencias/api/` (731 unitarias y 202 de integración sin fallos; coherencia con SQL independiente; recorrido real con `curl`; 503 real). Tareas diferidas: ninguna. F9 (CORS) queda en `despliegue` y F12 es parcial hasta la feature de replay. Pendiente del alumno: revisar, marcar F1–F8, F10 y F11 y pasar `docs/borradores/api.md` a la memoria.

**Input**: User description: "API que lee de PostgreSQL ya procesado y sirve al panel: `GET /api/eventos` (filtros, paginación, metadata completo), `GET /api/salud` y `GET /api/estadisticas` (mismos filtros), con la forma exacta de `contracts/api.md`, rol de solo lectura, 503 si la base falla, cuerpos 404/405 del error común y `mode=replay` aceptado devolviendo un intervalo vacío. Cubre F1-F8, F10 y F11; F9 (CORS) queda en la feature de despliegue (P1) y F12 se completa en la feature replay."

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `007-api` (F7). Contratos de referencia, sin modificar: `specs/001-contratos-y-modelo/contracts/api.md` (forma de las respuestas), `db-schema.md` (§1.1 roles, Q1/Q8) y `kafka-message.md`. El contrato mínimo del profesor está en `docs/enunciado/CONTRATO-API.md` (solo lectura). Esta spec no repite las tablas de `api.md`: las cita.

## Clarifications

### Session 2026-11-05

Respuestas con la opción recomendada (la herramienta no puede preguntar al alumno). Lo que toca contratos o alcance está en «Preguntas para el alumno» con decisión provisional.

- Q: ¿La API lee el esquema `replay` en `mode=replay` o devuelve un vacío fijo? → A: Lee de verdad `replay.current_event` (el rol de solo lectura ya tiene `SELECT`, `db-schema.md` §1.1). Como esa tabla está vacía hasta la feature replay, el resultado es el intervalo vacío que pide el brief, sin código de reproducción y sin tener que reescribir la API después. El esquema se elige con una lista cerrada (`live`, `replay`), nunca con texto del cliente (`db-schema.md` §1).
- Q: ¿Qué devuelve `mode=replay` en `/api/estadisticas`? → A: Lo que fija `api.md` §5.1: bloques calculados sobre `replay.current_event` (ceros, listas de recuentos vacías o con ceros) y `comparison: null`. `/api/salud` no cambia con el modo (`api.md` §4).
- Q: ¿Qué hace un parámetro repetido o desconocido (`?foo=1`, `?min_mag=1&min_mag=2`)? → A: Un parámetro desconocido se ignora (no hay contrato que lo rechace). Un parámetro conocido repetido es `400 invalid_parameter` («se admite un solo valor», `api.md` §3.1 para `country_id`; se extiende a todos por simplicidad).
- Q: ¿Qué es un `min_mag` válido? → A: Un número finito. `nan`, `inf` y `-inf` son `400 invalid_parameter` (constitución §5: nunca NaN/Infinity). Los negativos son válidos.
- Q: ¿Qué es un `limit` válido? → A: Entero entre 1 y el máximo configurable (por defecto 5 000, `api.md` §3.1). `0`, negativo, decimal o texto, o mayor que el máximo, es `400 invalid_parameter`. El máximo se lee de una variable de entorno nueva que se documenta en `.env.example` (constitución §10) y en el README, sin editar `contracts/config.md` de `002` (P3).
- Q: ¿Un `start`/`end` fuera de rango razonable (año 0001, 9999) es error? → A: Solo si no es ISO 8601 o si `start >= end`. Un rango enorme es válido y devuelve lo que haya. Límite conocido: un rango de un año en `by_hour` devuelve unas 8 760 entradas.
- Q: ¿Qué `period` y `filters.country_id` devuelve estadísticas con `country_id=none`? → A: `period` es el rango efectivo en ms; `filters.country_id` repite el valor normalizado (`"ESP"` o `"none"`), `null` si no se envió.
- Q: ¿Cuál es «ahora» en una petición? → A: Un único instante tomado al empezar a atender la petición; sirve para `generated`, para el rango por defecto y para `comparison.recent_period`. Así `generated`, `period.end` y `recent_period.end` son coherentes dentro de una respuesta.
- Q: ¿Qué errores no previstos devuelve la API? → A: Cualquier excepción no esperada es `500 internal_error` con el cuerpo común, sin traza ni SQL (`api.md` §6). Las validaciones de parámetros nunca responden `422` ni cuerpo `{"detail": …}`.
- Q: ¿Qué pasa si la base está parada cuando arranca la API? → A: Se mantiene el comportamiento de `002`: la API reintenta la conexión al arrancar y no atiende hasta tenerla. El 503 se prueba con la API en marcha y la base parada después (como en `docs/evidencias/infra-compose/`). Límite conocido de una línea.
- Q: ¿Cuánto tarda el 503 con la base parada? → A: Debe responder en un tiempo acotado (máximo 10 s medidos en la prueba), no colgarse. El tiempo máximo de espera de la conexión es un parámetro de configuración con valor por defecto.
- Q: ¿CORS en esta feature? → A: No; lo resuelve la feature de despliegue (brief). Ver «Preguntas para el alumno» P1 por F9.

## User Scenarios & Testing *(mandatory)*

Los «usuarios» son el panel (que consume la API), quien evalúa el sistema con `curl` y las pruebas automáticas. La feature no añade pantallas, replay, túnel ni despliegue.

### User Story 1 - Consultar eventos con filtros (Priority: P1)

Quien consulta pide `GET /api/eventos` y recibe un `FeatureCollection` con la versión actual de cada evento (una sola vez), con el `metadata` completo y los once campos de `properties`, filtrado por `start`, `end`, `min_mag`, `country_id` y `mode`. Sin filtros, las últimas 24 h.

**Why this priority**: F1-F4 son obligatorios y el panel no funciona sin este endpoint.

**Independent Test**: Cargar eventos sintéticos y reales en una base de prueba; consultar con y sin filtros y comparar con el resultado esperado; repetir con `curl` contra el stack con datos reales.

**Acceptance Scenarios**:

1. **Given** eventos en la base, **When** se pide `/api/eventos` sin parámetros, **Then** responde 200, `Content-Type: application/json`, solo eventos de las últimas 24 h con la forma exacta de `api.md` §3 y sin eventos repetidos (F1, F2).
2. **Given** ningún evento en el rango, **When** se consulta, **Then** 200 con `features: []`, `count: 0`, `total: 0`, `truncated: false` y `next_cursor: null` (F1).
3. **Given** `start` solo fecha, `start` con zona y `start` sin zona, **When** se consulta, **Then** se interpretan como `api.md` §3.1 (solo fecha = 00:00 UTC; sin zona = UTC; `start` incluido, `end` excluido) (F3).
4. **Given** un evento con `mag` nula y otro con `mag` negativa, **When** se pide `min_mag=0`, **Then** el nulo no aparece y se cuenta en `null_mag_excluded`; el negativo se excluye por ser menor, no por ser negativo; sin `min_mag`, ambos aparecen y `null_mag_excluded` es 0 (F3, F4).
5. **Given** un evento con `mag`, profundidad o país desconocidos, **When** se consulta, **Then** esos campos van a `null`, nunca a 0, NaN ni Infinity, y la geometría es un `Point` válido `[lon, lat, depth]` con la profundidad `null` si no existe (F4).
6. **Given** `country_id=esp`, `country_id=ESP` y `country_id=none`, **When** se consulta, **Then** los dos primeros dan el mismo resultado (se normaliza) y `none` devuelve solo eventos «Sin país asignado» (`country_id` y `country_name` a `null`); un código con forma válida que no existe devuelve `features: []` sin error (F3).
7. **Given** un evento que recibió una revisión, **When** se consulta, **Then** aparece una sola vez con su versión de mayor `updated` y conserva su posición (F1).

---

### User Story 2 - Truncado y paginación (Priority: P1)

Si hay más eventos que el máximo, la respuesta lo dice (`truncated: true`, `total` completo) y permite recorrer todas las páginas con `limit` y `cursor` sin repetir ni perder eventos.

**Why this priority**: F5 es obligatorio y el panel no debe calcular nada sobre una muestra truncada.

**Independent Test**: Con 25 eventos y `limit=10`, recorrer las páginas con `next_cursor` y comprobar que la unión son los 25 eventos, sin repetidos y en orden `event_time` descendente e `id` descendente.

**Acceptance Scenarios**:

1. **Given** 25 eventos y `limit=10`, **When** se piden tres páginas siguiendo `next_cursor`, **Then** `count` es 10, 10 y 5, `total` es 25 en las tres, `truncated` es `true` en las tres y `next_cursor` es `null` solo en la última; la unión no tiene repetidos ni huecos (F5).
2. **Given** eventos con el mismo `time`, **When** se pagina, **Then** el desempate por `id` evita repetir o perder alguno (F5).
3. **Given** un evento que se revisa entre la página 1 y la 2, **When** se pide la 2, **Then** no aparece dos veces ni cambia de posición (F5, `api.md` §3.3).
4. **Given** `limit` mayor que el máximo, `limit=0` o `cursor` mal formado, **When** se consulta, **Then** 400 con `invalid_parameter` (límite) o `invalid_cursor` (cursor) y mensaje en español.
5. **Given** más de 5 000 eventos y sin `limit`, **When** se consulta, **Then** se devuelven como máximo 5 000, `truncated: true` y `total` es el real (F5).

---

### User Story 3 - Estadísticas calculadas por la API, coherentes con el mapa (Priority: P1)

`GET /api/estadisticas` acepta los mismos filtros que `/api/eventos` (salvo `limit` y `cursor`) y devuelve los bloques de `api.md` §5, calculados sobre todos los eventos que cumplen los filtros, nunca sobre una página.

**Why this priority**: F7 es obligatorio y el frontend no puede calcular estadísticas (constitución §17).

**Independent Test**: Con los mismos filtros, `total` de estadísticas == `metadata.total` de eventos == suma de `by_hour`, == suma de `by_country`, == suma de cada histograma más su `no_value` cuando proceda; contraste con una cuenta directa en SQL en la prueba.

**Acceptance Scenarios**:

1. **Given** datos cargados y unos filtros combinados, **When** se piden eventos y estadísticas con los mismos filtros, **Then** `total` coincide y las sumas de `by_hour`, `by_country` y de los dos histogramas cuadran con `total`, contando el tramo `<1` con los negativos y «sin valor» según `api.md` §5.1 (F7).
2. **Given** eventos sin país, **When** se piden las estadísticas, **Then** `by_country` incluye un elemento con `country_id`, `country_name` y `subregion` a `null` y `no_value` igual a su recuento, y ese elemento no se suma dos veces (F7).
3. **Given** una hora UTC sin eventos dentro del periodo, **When** se piden las estadísticas, **Then** `by_hour` incluye esa hora con `count: 0`; el recuento solo incluye eventos dentro de `period` (F7).
4. **Given** magnitud nula con `min_mag` enviado, **When** se piden las estadísticas, **Then** `histograms.magnitude.no_value` coincide con `null_mag_excluded` de `/api/eventos` con los mismos filtros (F3, F7).
5. **Given** el histórico 2025 cargado (`006`), **When** se pide la comparación, **Then** `n_2025`, `daily_mean_2025 = n_2025/365`, `diff_abs`, `variation_pct` (2 decimales, `null` si la media es 0), `min_mag_applied = max(min_mag, 4.0)`, `recent_period`, `reference_period` y `recent_incomplete: true` siguen `api.md` §5.1 (F7).
6. **Given** que las estadísticas se piden con `limit` o `cursor`, **When** se consulta, **Then** esos parámetros se ignoran como desconocidos (no hay paginación en estadísticas).

---

### User Story 4 - Salud y fallo de la base: nunca «0 eventos» (Priority: P1)

`GET /api/salud` informa de que la API y la base responden y de la última ingesta correcta. Si la base falla, los tres endpoints devuelven `503 database_unavailable` con mensaje en español, no un 500 ni una lista vacía.

**Why this priority**: F6 y F8 son obligatorios; mostrar «0 eventos» por un fallo sería un dato falso.

**Independent Test**: Con la API en marcha, parar PostgreSQL y consultar los tres endpoints: 503 con el cuerpo de `api.md` §6 en el tiempo acotado. Volver a arrancarla y comprobar que se recupera sin reiniciar la API.

**Acceptance Scenarios**:

1. **Given** la base sana, **When** se pide `/api/salud`, **Then** 200 con `status: "ok"`, `last_ingestion` en ms (o `null` si aún no hubo ingesta) y `generated`; sin credenciales ni datos de conexión (F6).
2. **Given** la base parada, **When** se piden `/api/eventos`, `/api/estadisticas` y `/api/salud`, **Then** los tres devuelven 503 `database_unavailable` en menos de 10 s, nunca `features: []` ni 200 (F8).
3. **Given** la base de nuevo disponible, **When** se repite la consulta, **Then** vuelve a responder 200 sin reiniciar la API (F8).
4. **Given** datos sintéticos y reales en la base, **When** se consultan, **Then** `is_synthetic` los distingue en cada feature (constitución §7).

---

### User Story 5 - Errores de petición con el cuerpo común y modo `replay` vacío (Priority: P2)

Cualquier petición incorrecta recibe el cuerpo `{"error": {"code", "message"}}` con el código de `api.md` §6: 400 por parámetros, 404 por ruta inexistente, 405 por método distinto de GET (`OPTIONS` incluido hasta la feature de despliegue, P1). `mode=replay` se acepta y devuelve un intervalo vacío hasta que exista la feature replay.

**Why this priority**: cierra el pendiente heredado de `002` (404/405) y evita un panel que dependa de formas de error distintas; el replay solo necesita que la API no falle.

**Independent Test**: Peticiones inválidas en las pruebas con `httpx` y `curl` real; comparar status y `code`. Con `mode=replay` y la tabla de replay vacía, comprobar la forma de la respuesta.

**Acceptance Scenarios**:

1. **Given** `min_mag=abc`, `min_mag=nan`, fecha no ISO 8601, `start>=end`, `mode=otro`, `country_id` que no son tres letras ni `none`, o un parámetro conocido repetido, **When** se consulta cualquiera de los endpoints que lo admite, **Then** 400 `invalid_parameter` con mensaje en español que nombra el parámetro, sin 422 ni `{"detail": …}`.
2. **Given** una ruta inexistente (`/api/foo`, `/`), **When** se pide, **Then** 404 `not_found` con el cuerpo común (pendiente heredado de `002`).
3. **Given** `POST`, `PUT`, `PATCH` o `DELETE` sobre `/api/eventos`, **When** se pide, **Then** 405 `method_not_allowed` con el cuerpo común y la cabecera `Allow` (pendiente heredado de `002`).
4. **Given** un fallo inesperado de la API que no es de la base, **When** ocurre, **Then** 500 `internal_error` sin traza, SQL ni credenciales.
5. **Given** `mode=replay`, **When** se piden eventos y estadísticas, **Then** 200 con `metadata.mode: "replay"`, `features: []`, `total: 0`, `comparison: null`, y `generated`/`last_ingestion` con el significado de `api.md` §3.2; `mode=live` por defecto devuelve los datos de `live`. Los datos de `live` nunca aparecen en `replay` ni a la inversa (F12 parcial, constitución §7).
6. **Given** cualquier respuesta, **When** se inspecciona, **Then** todas llevan `Content-Type: application/json`, no existe ninguna ruta de administración y la documentación interactiva sigue desactivada (F10).

### Edge Cases

- Base sin ninguna ingesta: `last_ingestion: null` en salud y metadata, no un 0.
- Evento con `time` exactamente igual a `end`: excluido; igual a `start`: incluido.
- Evento con `place`, `status`, `url`, `sig` o `magType` nulos: se devuelven como `null`.
- `country_id` inexistente en el catálogo pero con forma válida (`ZZZ`): `features: []` sin error.
- Dos eventos con el mismo `time` en páginas distintas: desempate por `id`.
- Cursor válido usado con filtros distintos a los de la página anterior: no se detecta; el cliente debe repetir los filtros (`api.md` §3.1). Límite conocido.
- Revisión de un evento mientras se pagina: no se repite ni cambia de posición (conserva `time` e `id`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La API MUST exponer `GET /api/eventos`, `GET /api/salud` y `GET /api/estadisticas` con la forma exacta de `api.md` §3, §4 y §5; el contrato no se modifica ni se duplica (F1, F2, F6, F7, constitución §15).
- **FR-002**: `/api/eventos` MUST devolver cada evento una vez, con su versión actual, ordenado por `event_time` descendente e `id` descendente, con los once campos de `properties` y el `metadata` de ocho campos (F1, F2).
- **FR-003**: Sin `start` ni `end`, el rango MUST ser las últimas 24 h; con uno solo, según la tabla de `api.md` §3.1 (F1, F3).
- **FR-004**: Los filtros `start` (incluido), `end` (excluido), `min_mag`, `country_id` (normalizado a mayúsculas, `none` = sin país) y `mode` MUST aplicarse igual en eventos y estadísticas, con la misma validación (F3, F7).
- **FR-005**: La magnitud nula MUST NOT cumplir `min_mag` y MUST contarse en `null_mag_excluded`; los nulos MUST devolverse como `null`, nunca como 0, NaN ni Infinity (F3, F4, constitución §5).
- **FR-006**: Las magnitudes y profundidades negativas MUST tratarse como valores válidos (constitución §5).
- **FR-007**: `/api/eventos` MUST aplicar un máximo configurable (por defecto 5 000), devolver `truncated`, `total` y `next_cursor`, y paginar por clave `(event_time, id)` con cursor opaco (F5, `api.md` §3.3).
- **FR-008**: `/api/estadisticas` MUST calcular todas las cifras en la base, sobre todos los eventos que cumplen los filtros y desde el estado actual (`current_event`), nunca con contadores por mensaje ni sobre una página (F7, constitución §8). El frontend no calcula estadísticas (constitución §17).
- **FR-009**: `/api/estadisticas` MUST incluir `period`, `filters`, `total`, `by_hour`, `by_country`, `histograms.magnitude`, `histograms.depth` y `comparison`, cada bloque con `unit` y `no_value`, y `comparison: null` en `replay` (F7).
- **FR-010**: Con los mismos filtros, `total` de estadísticas MUST ser igual a `metadata.total` de eventos y a la suma de `by_hour`, `by_country` y de cada histograma (más `no_value` cuando `api.md` §5.1 lo defina así) (F7, coherencia).
- **FR-011**: `/api/salud` MUST devolver `status`, `last_ingestion` y `generated`, sin credenciales ni datos de conexión, y MUST NOT informar del modo (F6).
- **FR-012**: Si la base falla, los tres endpoints MUST responder `503 database_unavailable` en un tiempo acotado, nunca `features: []` ni 0 eventos como resultado válido, y MUST recuperarse solos cuando la base vuelva (F8).
- **FR-013**: Todos los errores MUST usar el cuerpo común `{"error": {"code", "message"}}` con los códigos de `api.md` §6 (`invalid_parameter`, `invalid_cursor`, `not_found`, `method_not_allowed`, `database_unavailable`, `internal_error`), incluidos los 404 y 405 generados por el framework y las validaciones de parámetros (que MUST NOT devolver 422). El `message` está en español y no incluye credenciales, SQL ni trazas (pendiente heredado de `002`, roadmap F7).
- **FR-014**: La API MUST usar el rol de base de datos de solo lectura `observatory_api` (db-schema.md §1.1), sin escribir en ninguna tabla; el esquema (`live`/`replay`) se elige con una lista cerrada, nunca con texto del cliente; todos los valores del cliente MUST ir parametrizados en SQL (F10, F11).
- **FR-015**: `mode` MUST aceptar `live` (por defecto) y `replay`; cualquier otro valor es 400. En `replay` la API MUST leer solo del esquema `replay`, y cuando está vacío devolver el intervalo vacío con la misma forma (F12 parcial).
- **FR-016**: Solo `GET` MUST estar permitido (`OPTIONS` responde 405 hasta la feature de despliegue, P1); MUST NOT existir rutas de administración ni la API MUST exponer secretos (F10, constitución §10).
- **FR-017**: La API MUST consultar solo datos ya procesados en la base y no depender de que el panel esté abierto (F11).
- **FR-018**: Las respuestas MUST llevar `Content-Type: application/json` y las fechas MUST ser milisegundos Unix UTC en `metadata`, `properties`, `period` y `comparison` (F2, `api.md` §1).
- **FR-019**: El máximo de eventos por respuesta y el tiempo máximo de espera de la base MUST ser configurables por variables de entorno con valor por defecto, documentadas en `.env.example`; no puede haber secretos en el repositorio (constitución §10).
- **FR-020**: Los identificadores del código MUST estar en inglés y los docstrings y comentarios en español; salvo las rutas y campos fijados por el contrato (constitución §13). Cada función MUST hacer una sola cosa y la lógica pura (validar, construir cursor, calcular tramos) MUST estar separada del acceso a la base (constitución §14).

### Key Entities

- **Evento actual**: una fila de `current_event` del esquema del modo, con su país opcional; se sirve como `Feature` GeoJSON.
- **Filtros de consulta**: rango efectivo `[start, end)`, `min_mag` opcional, `country_id` opcional o `none`, `mode`; comunes a eventos y estadísticas.
- **Cursor de paginación**: posición `(event_time, id)` del último evento servido, opaca para el cliente.
- **Estado de ingesta**: última consulta correcta a USGS (`last_ingestion`), tomada de `ingest.ingest_run`, igual en ambos modos.
- **Error común**: `{"error": {"code", "message"}}` con código estable.
- **Estadísticas**: bloques agregados (`by_hour`, `by_country`, histogramas, `comparison`) con periodo, filtros, unidad y registros sin valor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una consulta sin parámetros devuelve solo eventos de las últimas 24 h, con cero eventos repetidos y la forma de `api.md` §3 (comprobado contra los datos reales cargados, histórico y live).
- **SC-002**: Con 25 eventos sintéticos y `limit=10`, la unión de las tres páginas son exactamente 25 eventos sin repetidos y `truncated: true` en cada página (F5).
- **SC-003**: Para al menos cinco combinaciones de filtros (con `min_mag`, con `country_id`, con `none`, con rango, combinados), `total` de estadísticas == `metadata.total` de eventos == suma de `by_hour` == suma de `by_country` y cada histograma suma `total` (F7).
- **SC-004**: Con la base parada, los tres endpoints responden 503 `database_unavailable` en menos de 10 s en el 100 % de las pruebas, y 0 respuestas 200 con `features: []`; tras volver la base, responden 200 sin reiniciar la API (F8).
- **SC-005**: El 100 % de las peticiones inválidas de las pruebas (parámetro erróneo, ruta inexistente, método no permitido) devuelve el cuerpo `{"error": {"code", "message"}}` con el `code` esperado; ninguna devuelve 422 ni `{"detail": …}`.
- **SC-006**: Con un evento de magnitud nula, `min_mag` lo excluye de `features` y lo cuenta en `null_mag_excluded`; con magnitud negativa y profundidad negativa el evento se sirve sin rechazarse (F3, F4).
- **SC-007**: Contra el stack real, `curl` de `/api/eventos` (con y sin filtros, `mode=live` y `mode=replay`), `/api/salud` y `/api/estadisticas` queda guardado como evidencia en `docs/evidencias/api/`, incluido un conteo SQL independiente que coincide con `total` y con `n_2025` de la comparación para 2025 cargado.
- **SC-008**: Un análisis de las consultas SQL de la API confirma que el rol no escribe (`INSERT`/`UPDATE`/`DELETE` rechazado con el rol de la API) y que no existen rutas distintas de las tres de lectura (F10).

## Assumptions

- Base: `002` a `006` fusionadas en `main`: stack de Compose, esquema y roles (`observatory_api` ya con `SELECT` sobre `live.current_event`, `replay.current_event`, `public.country`, `ingest.ingest_run`), consumidor, productor, país por geometría e histórico 2025 cargado.
- El histórico y el feed en vivo comparten esquema `live` (`db-schema.md` §1); la API no distingue el origen salvo por `is_synthetic`.
- Las tablas de `replay` existen y están vacías hasta la feature replay, así que `mode=replay` devuelve vacío sin código especial.
- Los datos de pruebas con eventos sintéticos van etiquetados (`synthetic-…`, `is_synthetic = true`); la evidencia real usa los datos cargados.
- Las pruebas con `httpx` se ejecutan contra una base de pruebas con el rol de solo lectura, siguiendo el patrón de `tests/integration/` (servicio `tests` del perfil `test`).
- Los índices existentes (`ix_current_event_time` y los del esquema) bastan; no se añaden índices ni se modifica `sql/001_schema.sql`.
- Proporcionalidad: trabajo de clase de unas 2 semanas; máximo 25 tareas y 5 bloques; sin fuzz, sin auditorías ni endurecimiento de casos raros. Lo raro se documenta como límite conocido (una línea).
- Fuera de alcance: panel, replay (productor/consumidor/datos de replay y selector de intervalo), túnel y despliegue (ngrok, Netlify), CORS (la feature de despliegue), autenticación, caché y limitación de tasa.
- Límites conocidos: rango de un año en `by_hour` ≈ 8 760 entradas; un cursor reutilizado con otros filtros no se detecta; el 503 se verifica con la API en marcha (si la base está parada al arrancar, la API reintenta y no atiende todavía); parámetros desconocidos se ignoran; un error SQL imprevisto sale como 503 `database_unavailable`, no como 500.

## Preguntas para el alumno

Decisiones del orquestador, adoptadas como **provisionales** y reflejadas en el plan (`plan.md` §4). El alumno las confirma o las cambia al revisar.

- **P1 (F9, CORS)**: CORS queda **fuera de esta feature** (el brief lo dice expresamente); F9 queda cubierto por la feature de despliegue. Consecuencia: `OPTIONS` devuelve 405 hasta entonces y el panel en `localhost:4200` necesita un proxy o esa feature. *Recomendación:* mantenerlo.
- **P2 (replay y rango por defecto)**: misma regla de rango por defecto (últimas 24 h reales) en ambos modos; la feature replay decide si el panel envía siempre `start`/`end`. No se toca `api.md`. *Recomendación:* mantenerlo.
- **P3 (variables nuevas)**: `API_MAX_EVENTS` y `API_DB_TIMEOUT_SECONDS` se documentan en `.env.example` y en el README, sin editar `specs/002-infra-compose/contracts/config.md`; se anota en `docs/evidencias/sprint/decisiones.md`. *Recomendación:* mantenerlo.
