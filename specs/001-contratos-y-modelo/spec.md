# Feature Specification: Contratos y modelo de datos

**Feature Branch**: `001-contratos-y-modelo`

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "Feature: contratos-y-modelo. Dejar fijados y documentados los tres contratos del sistema (mensaje Kafka productor→consumidor, esquema de base de datos consumidor→API y API→panel) y el modelo de datos, para que las demás features los referencien sin redefinirlos. Cubre E1–E5, E7, contrato Kafka, esquema de BD (`sql/001_schema.sql`), `api.md` y reglas de versiones (C4)."

## Clarifications

### Session 2026-11-01

- Q: Si llegan dos versiones del mismo evento con el mismo `updated` pero contenido distinto, ¿qué hace el sistema con la segunda? → A: Se conserva la primera recibida; la segunda se ignora y se anota en el log con el `event_id`.
- Q: Cuando una consulta de eventos devuelve más puntos de los permitidos, ¿cómo pide el cliente el resto? → A: Cursor: la respuesta incluye un cursor opaco para pedir la página siguiente, con orden estable por tiempo del evento e `id`.
- Q: ¿Cómo se elige si el panel ve datos en vivo o de reproducción? → A: Parámetro de consulta `mode=live|replay` en `/api/eventos` y `/api/estadisticas`; por defecto `live`; otro valor es error de parámetro; `metadata.mode` devuelve el modo servido.
- Q: ¿Qué valores llevan `country_id` y `country_name` cuando un evento no tiene país asignado? → A: Ambos son `null`; el panel traduce `null` a "Sin país asignado".
- Q: ¿Qué forma tiene el cuerpo de respuesta cuando un endpoint devuelve un error? → A: Cuerpo JSON propio y común a todos los endpoints, `{"error": {"code": "...", "message": "..."}}`; HTTP 400 para parámetros inválidos y 503 si falla la base.

## User Scenarios & Testing *(mandatory)*

Los "usuarios" de esta feature son quienes construyen y evalúan el resto del sistema: la persona que implementa productor, consumidor, API y panel (el alumno, con su agente), y el profesor que evalúa el modelo de datos. Esta feature no entrega comportamiento ejecutable: entrega documentos y un DDL que las demás features obedecen.

### User Story 1 - Contrato del mensaje y reglas de versiones (Priority: P1)

Quien implementa productor y consumidor dispone de una definición única del mensaje que viaja entre ambos y de la regla que decide qué versión de un evento gana, sin tener que deducirlas del código ni de otros documentos.

**Why this priority**: Todo el flujo de datos depende de este contrato. Sin él, productor y consumidor se desacoplan mal y la idempotencia (C4) no se puede verificar.

**Independent Test**: Se revisa `kafka-message.md` con un mensaje de ejemplo real tomado del feed (`docs/evidencias/f1/explore_usgs_salida.txt`) y se comprueba que cada campo tiene nombre, tipo, obligatoriedad y valores permitidos, y que la regla de versiones resuelve los casos de la sección de escenarios sin ambigüedad.

**Acceptance Scenarios**:

1. **Given** un evento real del feed, **When** se compone el mensaje según el contrato, **Then** todos sus campos están definidos (origen, modo, instante de ingesta, instante de reproducción, evento original) y la clave del mensaje es el identificador del evento.
2. **Given** un evento ya guardado con `updated` = X, **When** llega una versión con `updated` menor o igual que X, **Then** el contrato establece que el estado actual no cambia, pero la versión recibida se conserva.
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
- **FR-006**: El esquema MUST permitir valores nulos de magnitud, profundidad y país sin sustituirlos por 0, y MUST aceptar magnitud y profundidad negativas.
- **FR-007**: El esquema MUST marcar los datos sintéticos de forma que queden separados de los reales.
- **FR-008**: El contrato MUST fijar las reglas de versiones: una versión con `updated` menor o igual nunca sustituye a una mayor; cada evento tiene una única fila actual; toda versión con un valor de `updated` no visto antes para ese evento se conserva sin pisar una posterior; un reenvío con el mismo `updated` no se duplica (C4). Si llegan dos versiones con el mismo `updated` y contenido distinto, se conserva la primera recibida; la segunda se ignora y se anota en el log con el `event_id`.

**Contrato de la API (`api.md`)**

- **FR-009**: `api.md` MUST partir del contrato mínimo del profesor sin contradecirlo y MUST resolver y justificar los seis puntos que ese contrato deja abiertos (según `docs/planificacion/decisiones-abiertas-contrato.md`):
  1. Forma exacta de `GET /api/salud` y `GET /api/estadisticas` (campos, tipos, formato de fecha, estados posibles, periodo, filtros, unidad, registros sin valor, comparación histórica, error explícito si falla la base).
  2. Paginación: el mecanismo es por cursor opaco, con orden estable por tiempo del evento e `id` (decidido en la aclaración). Queda por resolver el límite máximo de puntos por respuesta, la ubicación del total completo, el significado de `count` y el nombre y forma del cursor y del límite.
  3. Modo (en vivo / reproducción): lo elige el cliente con el parámetro de consulta `mode=live|replay` en `/api/eventos` y `/api/estadisticas`, por defecto `live`, y `metadata.mode` devuelve el modo servido (decidido en la aclaración). Queda por resolver el efecto en `generated` y `last_ingestion` en modo `replay`, y si `/api/salud` informa del modo.
  4. `country_name` y campos adicionales: un evento sin país lleva `country_id` y `country_name` a `null`, y el panel lo muestra como "Sin país asignado" (decidido en la aclaración). Queda por resolver la lista cerrada de campos de `properties` y si `magType` puede ser nulo.
  5. Filtros: dónde se informa de las magnitudes nulas excluidas por magnitud mínima, interpretación de fechas sin zona horaria y respuesta ante parámetros inválidos.
  6. Formato de error común a todos los endpoints: cuerpo `{"error": {"code": "...", "message": "..."}}`, HTTP 400 para parámetros inválidos y 503 si falla la base (decidido en la aclaración). Queda por resolver la lista de códigos de error.
- **FR-010**: Las decisiones del punto anterior las toma el alumno en la fase de aclaración; esta especificación no las da por resueltas.
- **FR-011**: Ningún campo, tipo o rango de los contratos MUST contradecir los valores observados en el feed real (`docs/evidencias/f1/explore_usgs_salida.txt`) ni el contrato mínimo del profesor.

**Documentación**

- **FR-012**: La feature MUST entregar un borrador de los modelos conceptual, lógico y físico para `docs/memoria.md` §5, coherente con el esquema, y la equivalencia entre los nombres en inglés del proyecto y los de la estructura orientativa del enunciado (E1, E3).
- **FR-013**: Los tres contratos MUST vivir únicamente en `specs/001-contratos-y-modelo/contracts/` y no duplicarse en otras features; `docs/enunciado/` no se modifica.
- **FR-014**: El DDL (`sql/001_schema.sql`) MUST ser coherente con `db-schema.md` (mismas tablas, columnas, claves e índices) (E5).

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
- **SC-002**: Las seis decisiones abiertas de `api.md` están resueltas y justificadas (6 de 6) antes de pasar a la planificación.
- **SC-003**: El 100 % de las tablas del esquema indica su grano, clave y relaciones, y el 100 % de los índices cita la consulta que lo motiva.
- **SC-004**: Las reglas de versiones resuelven sin ambigüedad los cuatro casos de la prueba de versiones: evento nuevo, reenvío con mismo `updated`, versión más reciente y versión antigua tardía.
- **SC-005**: Ningún campo de los contratos contradice los valores del feed real de la muestra (210 eventos) ni el contrato mínimo del profesor: 0 discrepancias detectadas en la revisión.
- **SC-006**: Las features siguientes (productor, consumidor, API, panel) pueden referenciar los contratos sin redefinir ni duplicar ninguno de sus campos.
- **SC-007**: El borrador de modelos cubre los tres niveles (conceptual, lógico, físico) y la equivalencia de nombres incluye las 5 tablas orientativas del enunciado.

## Assumptions

- Esta feature solo produce documentos y un DDL; no ejecuta código ni arranca servicios. La ejecución del DDL en una base de datos real se comprueba en la feature `consumidor-idempotente` y esta feature se valida con ella.
- El mensaje y el esquema parten de las propuestas del roadmap §1 (`02-roadmap-implementacion.md`), que se confirman o ajustan aquí.
- Los identificadores del proyecto (tablas, columnas, canales) van en inglés; documentos y comentarios en español; se respetan los nombres fijados por el profesor (`country_id`, `country_name`, rutas `/api/...`).
- Los tiempos de USGS están en milisegundos Unix y se convierten a UTC conservando el original.
- Tipos de evento: los eventos con `properties.type` distinto de `"earthquake"` se excluyen antes de publicar y se registran en la tabla de exclusiones con su motivo (B3, obligatorio).
- Las decisiones de `api.md` listadas en FR-009 se resuelven en la fase de aclaración con el alumno; hasta entonces permanecen abiertas.
- Dependencias: contrato mínimo del profesor (`docs/enunciado/CONTRATO-API.md`), enunciado §7, FAQ 20, constitución y evidencia del feed (`docs/evidencias/f1/explore_usgs_salida.txt`).
- Fuera de alcance: implementar productor, consumidor, API o frontend; Docker Compose y despliegue; cargar el catálogo de países o el histórico; modificar `docs/enunciado/`; cualquier ampliación fuera de los tres contratos y el modelo.
