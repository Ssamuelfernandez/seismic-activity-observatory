# Feature Specification: Contratos y modelo de datos

**Feature Branch**: `001-contratos-y-modelo`

**Created**: 2026-11-01

**Status**: Implemented

**Input**: User description: "Feature: contratos-y-modelo. Dejar fijados y documentados los tres contratos del sistema (mensaje Kafka productor→consumidor, esquema de base de datos consumidor→API y API→panel) y el modelo de datos, para que las demás features los referencien sin redefinirlos. Cubre E1–E5, E7, contrato Kafka, esquema de BD (`sql/001_schema.sql`), `api.md` y reglas de versiones (C4)."

## Clarifications

### Session 2026-11-01

- Q: Si llegan dos versiones del mismo evento con el mismo `updated` pero contenido distinto, ¿qué hace el sistema con la segunda? → A: Se conserva la primera recibida; la segunda se ignora y se anota en el log con el `event_id`.
- Q: Cuando una consulta de eventos devuelve más puntos de los permitidos, ¿cómo pide el cliente el resto? → A: Cursor: la respuesta incluye un cursor opaco para pedir la página siguiente, con orden estable por tiempo del evento e `id`.
- Q: ¿Cómo se elige si el panel ve datos en vivo o de reproducción? → A: Parámetro de consulta `mode=live|replay` en `/api/eventos` y `/api/estadisticas`; por defecto `live`; otro valor es error de parámetro; `metadata.mode` devuelve el modo servido.
- Q: ¿Qué valores llevan `country_id` y `country_name` cuando un evento no tiene país asignado? → A: Ambos son `null`; el panel traduce `null` a "Sin país asignado".
- Q: ¿Qué forma tiene el cuerpo de respuesta cuando un endpoint devuelve un error? → A: Cuerpo JSON propio y común a todos los endpoints, `{"error": {"code": "...", "message": "..."}}`; HTTP 400 para parámetros inválidos y 503 si falla la base.
- Q: ¿Cómo se expresa en `/api/estadisticas` la comparación con el histórico de 2025? → A: Se compara las últimas 24 horas con la media diaria de 2025. La API devuelve `n_recent` (eventos de las últimas 24 horas con los filtros pedidos, salvo las fechas), `n_2025` (eventos de 2025 con los mismos filtros, salvo las fechas), `daily_mean_2025 = n_2025 / 365` y `variation_pct`; `variation_pct` es `null` si no hay base de comparación.
- Q: ¿Cuál es el número máximo de eventos que devuelve `/api/eventos` en una respuesta antes de truncar y paginar? → A: 5 000, como constante configurable; el cliente puede pedir un `limit` menor, no mayor.
- Q: Cuando se filtra por magnitud mínima, ¿dónde informa la API de cuántos eventos con magnitud nula quedaron fuera? → A: En un campo de `metadata` de `/api/eventos` (conteo de eventos con magnitud nula excluidos por el filtro) y el mismo dato como "sin valor" en `/api/estadisticas`.
- Q: ¿Qué campos devuelve `GET /api/salud` y quién decide si los datos están desactualizados? → A: `status` (`"ok"` si la API y la base responden), `last_ingestion` (ms Unix UTC, `null` si aún no hubo ingesta) y `generated` (ms); si la base falla, 503 con el formato de error común. El umbral de desactualizado vive en el `config.json` del panel y la antigüedad se calcula con las fechas del servidor (`generated` menos `last_ingestion`).
- Q: ¿Qué tramos usan los histogramas de magnitud y de profundidad de `/api/estadisticas`? → A: Magnitud: tramos de 1 unidad, con el primero abierto (menos de 1, incluye negativos) y el último abierto (7 o más). Profundidad: 5 tramos (menos de 10 km, que incluye las profundidades negativas; 10–35; 35–70; 70–300; y 300 km o más). Ambos con un recuento aparte de "sin valor".
- Q: ¿En qué tramo del histograma de profundidad cae una profundidad negativa? → A: En el primer tramo, que pasa a ser "menos de 10 km" con límite inferior `null`.
- Q: Cuando `/api/eventos` trunca la respuesta, ¿qué cuenta `metadata.count` y dónde va el total de eventos que cumplen el filtro? → A: `count` = eventos de esta respuesta; un campo nuevo `total` en `metadata` = todos los que cumplen los filtros; un campo de cursor para la página siguiente, `null` en la última.
- Q: Si `start` o `end` llegan sin zona horaria, ¿cómo los interpreta la API? → A: Como UTC; una fecha sin hora equivale a las 00:00 UTC de ese día.
- Q: ¿Qué campos lleva exactamente `properties` en cada evento de `/api/eventos` y puede `magType` ser nulo? → A: Once campos: `mag`, `magType` (puede ser `null`), `place`, `time`, `updated`, `country_id`, `country_name`, más cuatro adicionales: `is_synthetic`, `status`, `url` y `sig`.
- Q: En modo `replay`, ¿qué significan `generated` y `last_ingestion` en `metadata`? → A: `generated` es siempre la hora real de la respuesta; `last_ingestion` es siempre la última consulta correcta a USGS del modo en vivo, también en `replay`; el modo se distingue solo por `metadata.mode`.

### Session 2026-11-02

El alumno aprobó todas las propuestas de `contracts/api.md` (sin excepciones); pasan a decididas:

- Q: ¿Cómo se llaman los parámetros y campos de paginación y de filtros de `/api/eventos`, y qué orden y formato de cursor usa? → A: Parámetros `limit` y `cursor`; en `metadata`, `total`, `next_cursor` y `null_mag_excluded`. Orden descendente por tiempo del evento e `id` (más reciente primero); el cursor es una cadena opaca (base64url de un JSON con el instante en ms y el `id`); cursor mal formado → error 400. `limit` mayor que el máximo → error 400. `truncated` es `true` cuando `count < total`.
- Q: ¿Cómo se trata `country_id` y qué rango se aplica si falta `start` o `end`? → A: `country_id` admite un solo valor y el valor reservado `none` selecciona los eventos «Sin país asignado». Sin `start` ni `end`: últimas 24 h; solo `start`: de `start` a ahora; solo `end`: de `end` − 24 h a `end` (hora del servidor). Si `start >= end`, error 400.
- Q: ¿`status`, `url`, `sig` y `place` pueden ser nulos en `properties`? → A: Sí, los cuatro pueden ser `null`.
- Q: ¿Qué códigos de error usa la API? → A: `invalid_parameter` (400), `invalid_cursor` (400), `not_found` (404), `method_not_allowed` (405), `database_unavailable` (503) e `internal_error` (500).
- Q: ¿`/api/salud` informa del modo? → A: No; `last_ingestion` es siempre el del modo en vivo.
- Q: ¿Qué forma tiene el resto de `/api/estadisticas`? → A: Bloques `metadata`, `period`, `filters`, `total`, `by_hour`, `by_country`, `histograms` (`magnitude`, `depth`) y `comparison`; cada bloque con resultados lleva `unit` y `no_value`. En `comparison`: `diff_abs` (con signo), `recent_incomplete` (siempre `true`), `recent_period`, `reference_period` y `unit`.
- Q: ¿Cómo aparece el país nulo en `by_country`? → A: Como un elemento propio con `country_id`, `country_name` y `subregion` a `null`; `no_value` repite su recuento de forma informativa y no se suma.
- Q: ¿Qué magnitud mínima usa la comparación histórica y qué devuelve en `replay`? → A: `max(min_mag solicitado, 4.0)` en las últimas 24 h y en 2025, declarado en `comparison.min_mag_applied`; en `mode=replay`, `comparison` es `null`.
- Q: ¿El mensaje Kafka lleva un campo para marcar datos sintéticos y qué motivos de cuarentena define? → A: Sí, `is_synthetic` (booleano obligatorio) en el mensaje, que el consumidor copia a las tablas. Motivos iniciales de cuarentena: `invalid_json`, `invalid_envelope`, `mode_topic_mismatch`, `missing_id`, `missing_time`, `missing_updated`, `invalid_geometry` y `coordinates_out_of_range` (lista ampliable en `consumidor-idempotente` y `geografia-pais`).
- Q: ¿Se aprueba la unicidad de cuarentena y de exclusión? → A: Sí: `quarantine` es única por `(original_sha256, reason)` y `exclusion` por `(event_id, updated_ms, kind)`.
- Q: ¿Qué motivos de cuarentena se añaden y quién valida los límites de cordura de los `CHECK`? → A: Se añaden `mag_out_of_range`, `depth_out_of_range`, `invalid_field_type` (tipos incorrectos, p. ej. `sig` o `status`) y `replay_at_missing` (`mode = replay` sin `replay_at`). Los límites de cordura (`mag` −10…15, `depth_km` −100…1000, `lon`/`lat` en su rango) están decididos y el consumidor los valida antes de insertar; si aun así la base rechaza el `INSERT`, se aplica el motivo de último recurso (ver la decisión siguiente).
- Q: ¿Cómo se llaman los campos propios de `/api/estadisticas` (constitución §13)? → A: En inglés: `n_recent`, `daily_mean_2025`, `variation_pct` y `no_value`; `n_2025` se mantiene.
- Q: ¿Cuándo es `truncated` verdadero? → A: En cada página cuyo contenido no incluya todos los eventos que cumplen los filtros (`count < total`), también en la última; el final de la paginación lo marca `next_cursor` a `null`.
- Q: ¿Cómo se trata un `country_id` en minúsculas? → A: Se normaliza a mayúsculas (`esp` pasa a `ESP`); se sigue rechazando todo valor que no sean tres letras ni `none`.
- Q: ¿Tiene el replay estado de ingesta propio? → A: No: las tablas `ingest.*` son compartidas y el replay no usa estado de ingesta propio.
- Q: ¿Qué pasa con los valores que desbordan los tipos de la base y con los rechazos imprevistos de la base? → A: Se añaden `value_out_of_range` (`sig` fuera del rango de `integer`, o `time`/`updated` que desbordan `timestamptz`) y el motivo de último recurso `db_constraint_violation`: si la base rechaza el `INSERT`, el consumidor hace `rollback` de ese mensaje, lo lleva a `quarantine` con ese motivo y confirma el offset, sin bloquear la cola.
- Q: ¿Qué motivo se registra si un mensaje incumple varias validaciones? → A: Un mensaje genera una sola fila de cuarentena, con el primer motivo que falle en el orden de prevalencia de `kafka-message.md` §6 (14 motivos, de `invalid_json` a `db_constraint_violation`; `replay_at_missing` va justo después de `mode_topic_mismatch`).
- Q: ¿Qué se aclara sobre las versiones de un evento en el escenario 2 de la historia 1 y en SC-004? → A: Con `updated` igual no se duplica y, si el contenido es distinto, se ignora la segunda; con `updated` menor y no visto, se conserva en el historial. Son cinco casos de versiones.

## User Scenarios & Testing *(mandatory)*

Los "usuarios" de esta feature son quienes construyen y evalúan el resto del sistema: la persona que implementa productor, consumidor, API y panel (el alumno, con su agente), y el profesor que evalúa el modelo de datos. Esta feature no entrega comportamiento ejecutable: entrega documentos y un DDL que las demás features obedecen.

### User Story 1 - Contrato del mensaje y reglas de versiones (Priority: P1)

Quien implementa productor y consumidor dispone de una definición única del mensaje que viaja entre ambos y de la regla que decide qué versión de un evento gana, sin tener que deducirlas del código ni de otros documentos.

**Why this priority**: Todo el flujo de datos depende de este contrato. Sin él, productor y consumidor se desacoplan mal y la idempotencia (C4) no se puede verificar.

**Independent Test**: Se revisa `kafka-message.md` con un mensaje de ejemplo real tomado del feed (`docs/evidencias/f1/explore_usgs_salida.txt`) y se comprueba que cada campo tiene nombre, tipo, obligatoriedad y valores permitidos, y que la regla de versiones resuelve los casos de la sección de escenarios sin ambigüedad.

**Acceptance Scenarios**:

1. **Given** un evento real del feed, **When** se compone el mensaje según el contrato, **Then** todos sus campos están definidos (origen, modo, instante de ingesta, instante de reproducción, evento original) y la clave del mensaje es el identificador del evento.
2. **Given** un evento ya guardado con `updated` = X, **When** llega una versión con `updated` menor o igual que X, **Then** el contrato establece que el estado actual no cambia; con `updated` igual no se duplica y, si el contenido es distinto, se ignora la segunda; con `updated` menor y no visto antes, la versión se conserva en el historial.
3. **Given** un evento ya guardado con `updated` = X, **When** llega una versión con `updated` mayor que X, **Then** el contrato establece que sustituye al estado actual y que sigue existiendo una única fila actual por evento.
4. **Given** un mensaje con modo de reproducción, **When** se consulta el contrato, **Then** queda definido por qué canal y en qué espacio de datos se aísla del modo en vivo (J3).

---

### User Story 2 - Esquema de base de datos y modelo de datos (Priority: P1)

Quien implementa consumidor, carga histórica y API dispone de un esquema de base de datos completo, con grano, claves, relaciones e índices justificados, que cubre estado actual, historial de versiones, cuarentena, exclusiones, estado de ingesta y catálogo de países.

**Why this priority**: Es el segundo contrato crítico (consumidor → API) y el núcleo de la evaluación de modelado (E1–E5, E7).

**Independent Test**: Se revisa `db-schema.md` y `sql/001_schema.sql` tabla por tabla: cada una declara qué representa una fila, su clave y sus relaciones; cada índice cita la consulta concreta que lo motiva; el DDL y el documento describen las mismas tablas y columnas.

**Acceptance Scenarios**:

1. **Given** el documento del esquema, **When** se lee la descripción de cada tabla, **Then** se indica qué es una fila (grano), su clave, sus relaciones y sus índices con la consulta que los justifica (E2).
2. **Given** un evento del feed con magnitud o profundidad negativas, o con magnitud nula, **When** se contrasta con el esquema, **Then** el esquema puede guardarlo sin rechazarlo ni sustituir el nulo por 0.
3. **Given** un evento del feed, **When** se contrasta con el esquema, **Then** se conservan su instante completo con precisión suficiente para agrupar por hora UTC (E7) y el valor original en milisegundos Unix.
4. **Given** el esquema, **When** se revisa el aislamiento de reproducción, **Then** existen espacios de datos separados para datos en vivo y de reproducción con las mismas tablas, y el catálogo de países compartido (J3, E4).
5. **Given** un dato inválido, **When** se consulta el esquema, **Then** hay un lugar donde se guarda con el motivo y una referencia al original.

---

### User Story 3 - Contrato de la API con las decisiones propias (Priority: P2)

Quien implementa la API y el panel dispone de `api.md`, que parte del contrato mínimo del profesor y resuelve, de forma justificada, todo lo que ese contrato deja sin definir.

**Why this priority**: Permite construir el panel contra un mock y la API real sin divergencias, pero depende de decisiones que toma el alumno en la fase de aclaración.

**Independent Test**: Se compara `api.md` con `docs/enunciado/CONTRATO-API.md` y con `docs/planificacion/decisiones-abiertas-contrato.md`: nada del contrato mínimo se contradice y cada punto abierto aparece resuelto con su justificación.

**Acceptance Scenarios**:

1. **Given** el contrato mínimo del profesor, **When** se lee `api.md`, **Then** conserva todo lo que el profesor fija (rutas, filtros, campos, `null` para valores desconocidos, error explícito si falla la base) sin contradecirlo.
2. **Given** la lista de puntos abiertos, **When** se lee `api.md`, **Then** cada uno de los seis puntos (ver FR-009) tiene una decisión concreta y su justificación.
3. **Given** un ejemplo de respuesta de cada endpoint en `api.md`, **When** se contrasta con valores reales del feed, **Then** ningún campo contradice lo observado (tipos, nulos, rangos).

---

### User Story 4 - Borrador de modelos conceptual, lógico y físico para la memoria (Priority: P3)

La persona que redacta la memoria dispone de un borrador de los tres niveles del modelo y de la equivalencia entre los nombres en inglés del proyecto y los del enunciado.

**Why this priority**: Es un entregable evaluable (E1, E3) pero se deriva de las historias anteriores.

**Independent Test**: Se revisa el borrador destinado a `docs/memoria.md` §5: los tres niveles describen la misma base de datos y la tabla de equivalencias cubre todas las tablas citadas en el enunciado.

**Acceptance Scenarios**:

1. **Given** el borrador, **When** se compara el nivel conceptual, el lógico y el físico, **Then** describen las mismas entidades y relaciones con distinto nivel de detalle (E1).
2. **Given** las tablas del enunciado (evento actual, versiones, país, fecha, cuarentena), **When** se consulta la equivalencia, **Then** cada una tiene su nombre en inglés correspondiente (E3).

---

### Edge Cases

- Una versión llega con `updated` **igual** al guardado (reenvío): no cambia el estado actual ni duplica la versión.
- Una versión **antigua** llega tarde, después de una más reciente: se conserva en el historial sin pisar el estado actual.
- Magnitud nula: se guarda como nula; no cumple un filtro de magnitud mínima y se cuenta aparte.
- Magnitud o profundidad negativas (el feed real trae ambas, p. ej. −0,06 y −0,18 km): válidas; no se rechazan ni se corrigen.
- Evento sin país (punto en el mar o fuera de cobertura): el país queda nulo y se muestra como "Sin país asignado".
- Evento sin identificador, sin instante, sin geometría o con coordenadas fuera de rango: dato inválido, va a cuarentena con motivo y referencia al original.
- Valores fuera de los límites de cordura (`mag` fuera de −10…15, `depth_km` fuera de −100…1000), campos de tipo incorrecto (p. ej. `sig` o `status`) o `mode = replay` sin `replay_at`: el consumidor los valida antes de insertar y los lleva a cuarentena con motivo (`mag_out_of_range`, `depth_out_of_range`, `invalid_field_type`, `value_out_of_range`, `replay_at_missing`); si aun así la base rechaza el `INSERT`, se aplica el motivo de último recurso `db_constraint_violation` (rollback del mensaje, cuarentena y confirmación del offset, sin bloquear la cola).
- Tipo de evento distinto de terremoto: los eventos con `properties.type` distinto de `"earthquake"` se excluyen antes de publicar y se registran en la tabla de exclusiones con su motivo (B3, obligatorio).
- Mensaje de reproducción: conserva el instante original del evento y añade el de reproducción; nunca se mezcla con los datos en vivo.
- Dos versiones de un mismo evento con el mismo `updated` y contenido distinto: se conserva la primera recibida; la segunda se ignora y se anota en el log con el `event_id`.

## Requirements *(mandatory)*

### Functional Requirements

**Contrato del mensaje (`kafka-message.md`)**

- **FR-001**: El contrato del mensaje MUST definir todos los campos del mensaje (origen, modo, instante de ingesta, instante de reproducción, evento original), con tipo, obligatoriedad, valores permitidos de origen y modo, y la clave del mensaje (identificador del evento).
- **FR-002**: El contrato MUST definir los canales de mensajes para datos en vivo y de reproducción (nombres, número de particiones y retención), de modo que el aislamiento de la reproducción quede garantizado (J3).

**Esquema y modelo (`db-schema.md`, `sql/001_schema.sql`)**

- **FR-003**: El esquema MUST describir, para cada tabla, el grano (qué representa una fila), la clave, las relaciones y los índices, y cada índice MUST citar la consulta concreta que lo justifica (E2).
- **FR-004**: El esquema MUST cubrir estado actual (una única fila por evento), historial de versiones (una fila por evento y valor de `updated`), cuarentena (motivo y referencia al original), exclusiones, estado de ingesta, catálogo de países y fechas, y MUST separar espacios de datos en vivo y de reproducción con las mismas tablas (E1, E3, E4).
- **FR-005**: El esquema MUST conservar el instante completo del evento con precisión suficiente para agrupar por hora UTC, y el valor original en milisegundos Unix (E7).
- **FR-006**: El esquema MUST permitir valores nulos de magnitud, profundidad y país sin sustituirlos por 0, y MUST aceptar magnitud y profundidad negativas. El consumidor valida antes de insertar y, si aun así la base rechaza el mensaje, se aplica el motivo de último recurso `db_constraint_violation` (ver Edge Cases).
- **FR-007**: El esquema MUST marcar los datos sintéticos de forma que queden separados de los reales.
- **FR-007b**: El esquema MUST guardar, además, el estado de revisión (`status`), el enlace al evento (`url`) y la significancia (`sig`) de cada evento, porque la API los expone en `properties`.
- **FR-008**: El contrato MUST fijar las reglas de versiones: una versión con `updated` menor o igual nunca sustituye a una mayor; cada evento tiene una única fila actual; toda versión con un valor de `updated` no visto antes para ese evento se conserva sin pisar una posterior; un reenvío con el mismo `updated` no se duplica (C4). Si llegan dos versiones con el mismo `updated` y contenido distinto, se conserva la primera recibida; la segunda se ignora, se anota en el log con el `event_id` y se cuenta en los contadores de transformaciones del consumidor (C8).

**Contrato de la API (`api.md`)**

- **FR-009**: `api.md` MUST partir del contrato mínimo del profesor sin contradecirlo y MUST resolver y justificar los seis puntos que ese contrato deja abiertos (según `docs/planificacion/decisiones-abiertas-contrato.md`):
  1. Forma exacta de `GET /api/salud` y `GET /api/estadisticas` (campos, tipos, formato de fecha, estados posibles, periodo, filtros, unidad, registros sin valor, error explícito si falla la base). La comparación histórica de `/api/estadisticas` compara las últimas 24 horas con la media diaria de 2025 y devuelve `n_recent`, `n_2025`, `daily_mean_2025 = n_2025 / 365` y `variation_pct`, que es `null` si no hay base de comparación (decidido en la aclaración); `GET /api/salud` devuelve `status` (`"ok"` si la API y la base responden), `last_ingestion` (ms Unix UTC, `null` si aún no hubo ingesta) y `generated` (ms), con 503 y el formato de error común si falla la base; el umbral de desactualizado vive en el `config.json` del panel y la antigüedad se calcula con las fechas del servidor (decidido en la aclaración). Los histogramas de `/api/estadisticas` usan, para la magnitud, tramos de 1 unidad con el primero abierto (menos de 1, incluye negativos) y el último abierto (7 o más), y para la profundidad 5 tramos (menos de 10 km con límite inferior `null`, que incluye las profundidades negativas; 10–35; 35–70; 70–300; y 300 km o más), ambos con un recuento aparte de "sin valor" (decidido en la aclaración). El resto de `GET /api/estadisticas` (periodo, filtros, unidades, conteos por hora y país) queda fijado en `contracts/api.md` (decidido en la aclaración de 2026-11-02).
  2. Paginación: el mecanismo es por cursor opaco, con orden estable por tiempo del evento e `id` (decidido en la aclaración). El límite máximo es de 5 000 eventos por respuesta, como constante configurable, y el cliente puede pedir un `limit` menor, no mayor (decidido en la aclaración). `metadata.count` es el número de eventos de la respuesta, `metadata.total` es el total de eventos que cumplen los filtros y un campo de cursor da la página siguiente, `null` en la última (decidido en la aclaración). El nombre y la forma del cursor quedan fijados en `contracts/api.md` (decidido en la aclaración de 2026-11-02).
  3. Modo (en vivo / reproducción): lo elige el cliente con el parámetro de consulta `mode=live|replay` en `/api/eventos` y `/api/estadisticas`, por defecto `live`, y `metadata.mode` devuelve el modo servido (decidido en la aclaración). En modo `replay`, `generated` es la hora real de la respuesta y `last_ingestion` sigue siendo la última consulta correcta a USGS del modo en vivo; el modo se distingue solo por `metadata.mode` (decidido en la aclaración). `/api/salud` no informa del modo (decidido en la aclaración de 2026-11-02).
  4. `country_name` y campos adicionales: un evento sin país lleva `country_id` y `country_name` a `null`, y el panel lo muestra como "Sin país asignado" (decidido en la aclaración). La lista cerrada de `properties` son once campos: `mag`, `magType` (puede ser `null`), `place`, `time`, `updated`, `country_id`, `country_name`, más cuatro adicionales: `is_synthetic`, `status`, `url` y `sig` (decidido en la aclaración). El esquema de base de datos MUST guardar `status`, `url` y `sig`, y el mock del panel MUST incluirlos.
  5. Filtros: las magnitudes nulas excluidas por magnitud mínima se informan en un campo de `metadata` de `/api/eventos` y como "sin valor" en `/api/estadisticas` (decidido en la aclaración). Las fechas `start` y `end` sin zona horaria se interpretan como UTC, y una fecha sin hora equivale a las 00:00 UTC de ese día (decidido en la aclaración). El nombre del campo y la respuesta ante parámetros inválidos quedan fijados en `contracts/api.md` (decidido en la aclaración de 2026-11-02).
  6. Formato de error común a todos los endpoints: cuerpo `{"error": {"code": "...", "message": "..."}}`, HTTP 400 para parámetros inválidos y 503 si falla la base (decidido en la aclaración). La lista de códigos de error queda fijada en `contracts/api.md` (decidido en la aclaración de 2026-11-02).
- **FR-010**: Las decisiones del punto anterior las tomó el alumno en la fase de aclaración (sesiones 2026-11-01 y 2026-11-02) y están registradas en la sección Clarifications; `api.md` las recoge todas como decididas.
- **FR-011**: Ningún campo, tipo o rango de los contratos MUST contradecir los valores observados en el feed real (`docs/evidencias/f1/explore_usgs_salida.txt`) ni el contrato mínimo del profesor.

**Documentación**

- **FR-012**: La feature MUST entregar un borrador de los modelos conceptual, lógico y físico para `docs/memoria.md` §5, coherente con el esquema, y la equivalencia entre los nombres en inglés del proyecto y los de la estructura orientativa del enunciado (E1, E3).
- **FR-013**: Los tres contratos MUST vivir únicamente en `specs/001-contratos-y-modelo/contracts/` y no duplicarse en otras features; `docs/enunciado/` no se modifica.
- **FR-014**: El DDL (`sql/001_schema.sql`) MUST ser coherente con `db-schema.md` (mismas tablas, columnas, claves e índices) (E5). Criterio de aceptación E5: `sql/001_schema.sql` existe, crea tablas e índices, es coherente con `db-schema.md` y se aplicó dos veces sin errores en PostgreSQL 16 el 2-nov-2026, probando además sus restricciones, las reglas de versiones y el aislamiento `live`/`replay` (evidencia: `docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql`). La comprobación posterior en `consumidor-idempotente` se mantiene como prueba de integración.

**Estadísticas (`/api/estadisticas`)**

- **FR-015**: La comparación histórica MUST incluir `n_recent`, `n_2025`, `daily_mean_2025`, la diferencia absoluta, `variation_pct` (`null` si la media es 0) y un indicador de periodo reciente posiblemente incompleto. El frontend no calcula ninguno de estos valores.
- **FR-016**: Cada histograma MUST devolver la definición de cada tramo (límites inferior y superior, con `null` en los límites abiertos) y su recuento, más el recuento de "sin valor". El frontend no calcula los tramos ni los recuentos.
- **FR-017**: Los recuentos por país MUST incluir `country_id`, `country_name` y subregión, con la categoría "Sin país asignado" para el país nulo. La serie por hora UTC MUST incluir también las horas con cero eventos.

### Key Entities *(include if feature involves data)*

- **Mensaje de evento**: unidad que viaja del productor al consumidor; lleva el evento original más metadatos de origen, modo e instantes de ingesta y reproducción; su clave es el identificador del evento.
- **Evento actual**: la versión más reciente de un terremoto; una fila por identificador de evento; incluye magnitud, tipo de magnitud, profundidad, instante, posición, lugar, país, origen y marca de dato sintético.
- **Versión de evento**: cada versión observada de un evento, identificada por evento y valor de `updated`; conserva el original recibido.
- **Cuarentena**: registro rechazado con su motivo y la referencia al original.
- **Exclusión**: registro descartado de forma controlada, con motivo y tipo.
- **Estado de ingesta**: último `updated` publicado por evento, ejecuciones de consulta al feed y respuestas originales conservadas.
- **País**: entidad del catálogo geográfico, identificada por `country_id`.
- **Fecha**: día UTC al que pertenece un evento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los tres contratos existen en `specs/001-contratos-y-modelo/contracts/` y el 100 % de sus campos y tablas tienen definidos tipo, obligatoriedad y significado.
- **SC-002**: Las seis decisiones de `api.md` están resueltas y justificadas (6 de 6), todas registradas como decididas en Clarifications.
- **SC-003**: El 100 % de las tablas del esquema indica su grano, clave y relaciones, y el 100 % de los índices cita la consulta que lo motiva.
- **SC-004**: Las reglas de versiones resuelven sin ambigüedad los cinco casos de la prueba de versiones: evento nuevo, reenvío con mismo `updated`, versión más reciente, versión antigua tardía y mismo `updated` con contenido distinto. De este último caso, la evidencia de esta feature demuestra la parte SQL (`ON CONFLICT DO NOTHING` conserva la primera versión; pruebas T17 y T18); ignorar la segunda versión, anotarla en el log y contarla lo prueba la feature `consumidor-idempotente`.
- **SC-005**: Ningún campo de los contratos contradice los valores del feed real de la muestra (210 eventos) ni el contrato mínimo del profesor: 0 discrepancias detectadas en la revisión.
- **SC-006**: Las features siguientes (productor, consumidor, API, panel) pueden referenciar los contratos sin redefinir ni duplicar ninguno de sus campos.
- **SC-007**: El borrador de modelos cubre los tres niveles (conceptual, lógico, físico) y la equivalencia de nombres incluye las 5 tablas orientativas del enunciado.

## Assumptions

- Esta feature solo produce documentos y un DDL; no ejecuta código de aplicación ni arranca servicios. El 2-nov-2026 `sql/001_schema.sql` se aplicó dos veces sin errores en PostgreSQL 16 y se probaron sus restricciones, las reglas de versiones y el aislamiento `live`/`replay`, con evidencia en `docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql`. La comprobación posterior en la feature `consumidor-idempotente` se mantiene como prueba de integración.
- El mensaje y el esquema parten de las propuestas del roadmap §1 (`02-roadmap-implementacion.md`), que se confirman o ajustan aquí.
- Los identificadores del proyecto (tablas, columnas, canales) van en inglés; documentos y comentarios en español; se respetan los nombres fijados por el profesor (`country_id`, `country_name`, rutas `/api/...`).
- Los tiempos de USGS están en milisegundos Unix y se convierten a UTC conservando el original.
- Tipos de evento: los eventos con `properties.type` distinto de `"earthquake"` se excluyen antes de publicar y se registran en la tabla de exclusiones con su motivo (B3, obligatorio).
- Las decisiones de `api.md` listadas en FR-009 se resolvieron con el alumno en la fase de aclaración (sesiones 2026-11-01 y 2026-11-02) y figuran como decididas en Clarifications.
- Dependencias: contrato mínimo del profesor (`docs/enunciado/CONTRATO-API.md`), enunciado §7, FAQ 20, constitución y evidencia del feed (`docs/evidencias/f1/explore_usgs_salida.txt`).
- Fuera de alcance: implementar productor, consumidor, API o frontend; Docker Compose y despliegue; cargar el catálogo de países o el histórico; modificar `docs/enunciado/`; cualquier ampliación fuera de los tres contratos y el modelo.

## Criterios de aceptación

Cada criterio parte de un ID del checklist (`docs/planificacion/01-checklist-requisitos.md`). Esta feature no tiene prueba de aceptación propia; se valida con las comprobaciones de `quickstart.md` y con la feature `consumidor-idempotente`.

- **E1**: existen los modelos conceptual, lógico y físico como borrador para la memoria (`data-model.md`); su reescritura en `docs/memoria.md` §5 es la tarea T018.
- **E2**: cada tabla explica su grano, claves, relaciones e índices, y cada índice cita su consulta (`contracts/db-schema.md` §3 y §4).
- **E3**: queda escrita la equivalencia de nombres en inglés con el enunciado (`contracts/db-schema.md` §6 y `data-model.md` §4).
- **E4**: el modelo integra cada evento con atributos del catálogo de países (`public.country`, `current_event.country_id`).
- **E5**: `sql/001_schema.sql` existe, crea tablas e índices y es coherente con `db-schema.md` (FR-014); se aplicó dos veces sin errores en PostgreSQL 16 y se probaron sus restricciones (evidencia en `docs/evidencias/contratos-y-modelo/`).
- **E7**: se conserva el timestamp completo del evento (`timestamptz` con precisión de microsegundo) junto con el valor original en milisegundos Unix, con `CHECK` de coherencia.
- **C4**: el contrato fija que solo gana una versión con `updated` estrictamente mayor y que toda versión recibida se conserva (`contracts/kafka-message.md` §5, `contracts/db-schema.md` §5); las reglas SQL se probaron en PostgreSQL 16 (pruebas T11, T17 y T18 de la evidencia: `ON CONFLICT DO NOTHING` conserva la primera versión); ignorar la segunda versión, registrarla en el log y contarla lo prueba `consumidor-idempotente`.
