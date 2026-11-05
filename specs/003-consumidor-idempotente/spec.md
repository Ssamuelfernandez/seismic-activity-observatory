# Feature Specification: Consumidor idempotente

**Feature Branch**: `003-consumidor-idempotente`

**Created**: 2026-11-04

**Status**: Implemented

**Input**: User description: "Feature: consumidor-idempotente. Procesar de forma idempotente los mensajes de `earthquakes.live` y dejar PostgreSQL con los eventos actuales, el historial de versiones y la cuarentena. Cubre C1–C8 y C13. Pruebas de aceptación: 2 (reenvío, parte consumidor), 3, 4, 6 y 8."

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `004-consumidor-idempotente`. La carpeta se llama `003-consumidor-idempotente` porque Spec Kit numera por orden de creación y `productor-live` aún no existe. En los documentos se usa el nombre (slug), que es estable.

## Clarifications

### Session 2026-11-04

Respuestas elegidas con la opción recomendada (la herramienta no puede preguntar al alumno); las discutibles se sometieron después al alumno: sus decisiones están marcadas como "confirmadas por el alumno" y en "Preguntas para el alumno" solo queda lo que sigue abierto.

- Q: ¿Los contadores de C8 cuentan por mensaje o por intento cuando un mensaje se reintenta por caída de PostgreSQL o Kafka? → A: Por mensaje: cada contador se incrementa una sola vez por mensaje y sesión, después del commit del offset de Kafka (que a su vez sigue al commit en PostgreSQL o a la fila de cuarentena guardada), nunca en un intento que acaba en rollback o reintento. El reintento no cuenta como "recibido" otra vez; los reintentos se registran en el log, no en los contadores. Limitación documentada: si el commit del offset falla y hay redelivery en la misma sesión, el mensaje reentregado se cuenta como un mensaje nuevo recibido (reenvío); por eso SC-009 se verifica sin fallos inyectados.
- Q: ¿Qué errores de PostgreSQL se consideran `db_constraint_violation` y cuáles se reintentan? → A: Los errores de integridad (SQLSTATE clase 23: unicidad, FK, check, not null) y los de datos (clase 22: data exception, p. ej. carácter nulo en texto/jsonb, desbordamiento numérico o de fecha), en el `INSERT` o en el `COMMIT` de un mensaje ya validado, van a cuarentena, para que ningún mensaje no válido bloquee la partición (constitución §6). Cualquier otro error (conexión, 08*, 40*, 53*, 57*, permisos...) es transitorio o de configuración: se reintenta con espera, no se confirma el offset y no se envía a cuarentena. La extensión a la clase 22 es una lectura de `kafka-message.md` §6 ("la base rechaza el `INSERT`"), **confirmada por el alumno**.
- Q: ¿Cuántas veces se reintenta la base o Kafka antes de rendirse? → A: Sin límite, con espera creciente acotada, coherente con `infra-compose` FR-008/FR-009 (cada reintento deja constancia en el registro). El consumidor no termina de forma definitiva por una indisponibilidad temporal.
- Q: ¿Qué hace el consumidor si un mensaje hace fallar la base por un error que no es de integridad y que se repite siempre (mensaje venenoso)? → A: No se descarta en silencio: se sigue reintentando (el orden de partición se mantiene) y el fallo queda en el registro con `event_id`, tema, partición y offset en cada intento (un registro por intento, con espera acotada, sin crecimiento ilimitado de contenido). El latido no se renueva durante el reintento, así que el contenedor puede quedar `unhealthy`; es consecuencia aceptada. Fuera de alcance una cola de mensajes muertos.
- Q: ¿La cuarentena deduplica por contenido semántico o por bytes? → A: Por bytes (`original_sha256` + motivo), según FR-011/FR-012. El mismo JSON inválido con otra serialización genera otra fila; es consecuencia aceptada y se documenta en el plan.

## User Scenarios & Testing *(mandatory)*

Los "usuarios" de esta feature son quien evalúa el pipeline (el profesor y el alumno que lo defiende) y las features que leen la base de datos después (API, histórico, replay). Esta feature convierte el consumidor mínimo de `002-infra-compose` (que solo registra mensajes) en el responsable de dejar PostgreSQL en un estado correcto y repetible, pase lo que pase con la entrega de mensajes.

### User Story 1 - Un evento y sus versiones quedan bien registrados (Priority: P1)

Quien verifica el sistema envía la secuencia de referencia de la FAQ 12 con mensajes sintéticos etiquetados: E1 (10:05, mag 4.2) → la misma versión repetida → E1 (10:09, mag 4.6) → la versión de las 10:05 repetida (llega tarde) → E2. Al terminar, la base de datos tiene 2 eventos actuales en `live.current_event` (E1 con magnitud 4.6 y E2) y 3 filas en `live.event_version` (2 de E1 y 1 de E2).

**Why this priority**: Es el criterio de cierre de la feature (roadmap F3) y cubre las pruebas 2, 3 y 4 de la tabla de aceptación. Sin esto no hay pipeline fiable para API, histórico ni replay.

**Independent Test**: Publicar los cinco mensajes sintéticos en `earthquakes.live` con el consumidor en marcha (o ejecutar las mismas decisiones desde un test automático) y consultar `live.current_event` y `live.event_version`.

**Acceptance Scenarios**:

1. **Given** una base sin el evento E1, **When** llega E1 (updated 10:05, mag 4.2), **Then** existe 1 fila actual de E1 con mag 4.2 y 1 fila de versión.
2. **Given** E1 ya guardado con ese `updated`, **When** llega exactamente la misma versión otra vez (prueba 2), **Then** el recuento de eventos actuales y de versiones no cambia y el estado actual queda igual.
3. **Given** E1 guardado con updated 10:05, **When** llega E1 con updated 10:09 y mag 4.6 (prueba 3), **Then** el estado actual de E1 pasa a mag 4.6 y el historial pasa a tener 2 versiones.
4. **Given** E1 actual con updated 10:09, **When** llega la versión de 10:05 de E1 (versión antigua tardía, prueba 4), **Then** el estado actual sigue en mag 4.6 con updated 10:09, y el historial conserva la versión de 10:05 sin duplicarla.
5. **Given** la secuencia completa, **When** llega E2 (10:12, mag 3.1, FAQ 12), **Then** el resultado final es: 2 eventos actuales (E1 con mag 4.6 y E2 con mag 3.1) y 3 filas de versión en total (2 de E1, las de 10:05 y 10:09, y 1 de E2). La versión de 10:05 repetida no añade filas porque la clave del historial es (`event_id`, `updated`).
6. **Given** dos versiones del mismo evento con el mismo `updated` pero contenido distinto, **When** llega la segunda, **Then** no cambia ni el estado actual ni el historial (se conserva la primera recibida), se anota en el registro con el `event_id` y se cuenta en los contadores de transformaciones (decisión de `kafka-message.md` §5).

---

### User Story 2 - Reiniciar o fallar sin duplicar efectos ni perder mensajes (Priority: P1)

Quien verifica el sistema detiene el consumidor en mitad del procesamiento, lo vuelve a arrancar y comprueba que reanuda donde debía: nada se duplica, nada se pierde. Si la base de datos falla, el consumidor no da por bueno ningún mensaje que no esté guardado.

**Why this priority**: Es la garantía de entrega al menos una vez con escritura idempotente (C2, C3, constitución §1) y la prueba 8.

**Independent Test**: Procesar un lote de mensajes, reiniciar el consumidor (también tras forzar un corte entre el guardado y la confirmación del offset) y comparar recuentos y contenido antes y después con SQL.

**Acceptance Scenarios**:

1. **Given** un mensaje ya guardado en la base pero cuyo offset no llegó a confirmarse (el consumidor se detuvo justo entre ambos pasos), **When** el consumidor reinicia, **Then** el mensaje se procesa de nuevo y la base queda idéntica (prueba 8).
2. **Given** un consumidor reiniciado, **When** retoma el consumo, **Then** continúa desde el último offset confirmado, sin releer todo el tema ni saltarse mensajes.
3. **Given** la base de datos no disponible, **When** llega un mensaje, **Then** el consumidor reintenta con espera, no confirma el offset de ese mensaje, no lo envía a cuarentena por ese motivo y, cuando la base vuelve, lo procesa y lo guarda.
4. **Given** el orden de operaciones de un mensaje válido, **When** se examina, **Then** el offset se confirma siempre después de que la transacción de PostgreSQL haya hecho commit, nunca antes.
5. *(Diferido: no se probó con Kafka real caído; cubierto con dobles)* **Given** que Kafka no está disponible, **When** el consumidor lo detecta, **Then** reintenta la conexión y retoma el consumo al recuperarse, sin perder ni duplicar efectos en la base. Si falla el commit del offset y el mensaje se reentrega en la misma sesión, los contadores lo cuentan como un mensaje nuevo recibido (limitación documentada, FR-023).
6. **Given** un error de base que no es de integridad ni de datos (conexión, `08*`, `40*`, `53*`, `57*`...) al procesar un mensaje válido, **When** ocurre, **Then** el consumidor reintenta con espera, no envía el mensaje a cuarentena, no confirma su offset y lo guarda cuando el error desaparece.

---

### User Story 3 - Los datos inválidos van a cuarentena sin bloquear la cola (Priority: P1)

Quien verifica el sistema envía mensajes con problemas (coordenadas fuera de rango, sin `id`, JSON roto, `mode` que no corresponde al tema…) y comprueba que cada uno queda en la tabla de cuarentena con su motivo y una referencia al original, y que los mensajes siguientes se procesan con normalidad.

**Why this priority**: Es obligatorio (C5, constitución §6) y cubre la prueba 6 (coordenadas inválidas: cuarentena con motivo, ningún punto inventado).

**Independent Test**: Publicar un mensaje con latitud 145 seguido de un mensaje válido; comprobar una fila en `live.quarantine` con motivo `coordinates_out_of_range`, ninguna fila en las tablas de evento para el inválido y el válido guardado.

**Acceptance Scenarios**:

1. **Given** un mensaje cuyo evento tiene latitud 145 (prueba 6), **When** se procesa, **Then** hay una fila en cuarentena con motivo `coordinates_out_of_range`, el valor original y la referencia al tema, partición y offset del mensaje; no se crea ningún evento actual ni versión para él; y su offset se confirma.
2. **Given** un mensaje que incumple varias reglas a la vez, **When** se procesa, **Then** se registra una sola fila de cuarentena, con el primer motivo según el orden de prevalencia de `kafka-message.md` §6.
3. **Given** un valor que no es JSON válido, **When** llega, **Then** queda en cuarentena con `raw_text`, motivo `invalid_json`, y no detiene el consumo.
4. **Given** un mensaje con `mode = replay` en `earthquakes.live`, **When** llega, **Then** no se escribe en ninguna tabla de eventos y va a cuarentena del esquema `live` con motivo `mode_topic_mismatch`.
5. **Given** que el mismo original inválido llega dos veces por el mismo motivo, **When** se procesa la segunda vez, **Then** no se duplica la fila de cuarentena (unicidad por hash del original y motivo).
6. *(Diferido, 6–8: endurecimiento de FR-014 con base real; la ruta feliz de la cuarentena sí está probada)* **Given** un mensaje que pasa todas las validaciones pero que la base rechaza, en el `INSERT` o en el `COMMIT`, con un error de SQLSTATE clase 23 (integridad) o clase 22 (data exception), **When** ocurre, **Then** se hace rollback de ese mensaje, queda en cuarentena con motivo `db_constraint_violation` y se confirma su offset.
7. *(Diferido, ver 6)* **Given** un mensaje válido y un error de base de otra clase (conexión, `08*`, `40*`, `53*`, `57*`...), **When** ocurre, **Then** no hay cuarentena ni commit de offset: se reintenta con espera hasta que la base responde.
8. *(Diferido, ver 6)* **Given** que falla el `INSERT` en cuarentena (con el contenido ya saneado y con la regla de copia de FR-011 aplicada, o con un contenido que no necesitaba saneado) por un error de base (conexión, permisos, cualquier SQLSTATE), **When** ocurre, **Then** se trata como error de base: reintento con espera, sin commit de offset y sin intentar otra cuarentena (sin recursión). Si el intento saneado también falla, es este mismo caso: reintento sin recursión.
9. **Given** un mensaje de cualquier motivo de cuarentena cuyo contenido no puede almacenarse tal cual (un `\u0000` o bytes que no son UTF-8 válido en el valor, en `event_id` o en `source`), **When** se procesa, **Then** el consumidor lo detecta antes del `INSERT`, inspeccionando el contenido (no por el SQLSTATE devuelto), y escribe una fila de cuarentena con todos los textos saneados o escapados (o `event_id`/`source` a `NULL`, que `db-schema.md` §3.5 permite), `original` a `NULL` y `raw_text` saneado, aplicando además la regla de copia de FR-011 (`source` fuera de `usgs_feed`/`usgs_historical`/`replay_demo` a `NULL`, `event_id` que no es cadena a `NULL`, `is_synthetic` no booleano a `false`), el `original_sha256` calculado sobre los bytes originales recibidos y el motivo que corresponda (cualquiera de la lista); su offset se confirma y los mensajes siguientes se procesan con normalidad.
10. **Given** un mensaje con valor Kafka nulo (tombstone) o vacío, **When** llega, **Then** se trata como un valor que no es JSON válido: cuarentena con motivo `invalid_json` (el contrato no define motivo específico y este es el que corresponde a un mensaje no parseable, sin cambiar el contrato), `raw_text` vacío (cumple el `CHECK` de `db-schema.md` §3.5) y `original_sha256` = SHA-256 de cero bytes; el nulo y el vacío comparten hash y motivo, así que generan una sola fila (consecuencia aceptada). Su offset se confirma.
11. **Given** (regla general de FR-014) mensajes cuyo contenido podría hacer fallar una escritura por sí mismo: `event.id` numérico o `bool`, `time` o `sig` booleano, `place` numérico, `mag` `NaN`, `dmin` `NaN`, `place` con `\u0000`, un entero de más de 4300 dígitos, un `event.id` de 600 caracteres o bytes que no son UTF-8, **When** se procesa cada uno, **Then** ninguno llega a provocar un fallo de la base ni bloquea la partición: cada uno acaba en una fila de cuarentena con el motivo que corresponde (`invalid_field_type`, `missing_time`, `mag_out_of_range`, `db_constraint_violation` para el válido por contrato pero no almacenable como `jsonb`, `invalid_json`, `value_out_of_range`), con `original` a `NULL` y `raw_text` saneado cuando el original no es almacenable, `event_id` a `NULL` si no es cadena o supera 512 caracteres, el `original_sha256` de los bytes recibidos, y su offset confirmado; los mensajes siguientes se procesan con normalidad.
12. **Given** un mensaje válido de contenido normal con `event.id` de exactamente 512 caracteres, **When** se procesa, **Then** se guarda con normalidad (el tope no rechaza lo que cabe en el índice).

---

### User Story 4 - Nulos, negativos y tiempos se tratan con criterio (Priority: P2)

Quien revisa la calidad comprueba que los valores ausentes no se inventan, que los negativos legítimos se conservan y que los tiempos se guardan en UTC junto con su valor original en milisegundos.

**Why this priority**: Obligatorio (C6, C7, constitución §3 y §5), pero se verifica sobre el mismo recorrido de las historias anteriores.

**Independent Test**: Procesar un evento con `mag` nula, otro con magnitud −0,06 y profundidad −0,18, y uno normal; comparar con los valores guardados.

**Acceptance Scenarios**:

1. **Given** un evento con `mag` nula, **When** se guarda, **Then** `mag` queda `NULL` (nunca 0) y el evento se conserva como actual.
2. **Given** un evento con magnitud −0,06 y profundidad −0,18, **When** se guarda, **Then** se conservan tal cual; no van a cuarentena por ser negativos.
3. **Given** un evento con `time` y `updated` en milisegundos Unix, **When** se guarda, **Then** se guardan el instante en UTC y el valor original en milisegundos, coherentes entre sí, y `ingested_at` queda separado del tiempo del evento.
4. **Given** cualquier evento guardado, **When** se consulta, **Then** su `date_id` corresponde al día UTC del instante del evento y ese día existe en la tabla de fechas.
5. **Given** un evento válido, **When** se guarda, **Then** `country_id` queda `NULL` (la asignación de país es de otra feature) y el original completo queda íntegro en la versión.

---

### User Story 5 - Datos sintéticos separados y contadores de transformaciones (Priority: P2)

Quien audita el pipeline comprueba que los datos de prueba están marcados como sintéticos en todas las tablas, y que el consumidor deja constancia de qué transformaciones cambian datos y a cuántos registros afectan.

**Why this priority**: Obligatorio (C13 y C8; constitución §7). No bloquea el recorrido funcional.

**Independent Test**: Procesar la secuencia de la historia 1 y un mensaje inválido, y revisar las filas (`is_synthetic`) y el resumen de contadores del registro del consumidor.

**Acceptance Scenarios**:

1. **Given** mensajes con `is_synthetic = true`, **When** se guardan o se llevan a cuarentena, **Then** la marca se copia a `current_event`, `event_version` y `quarantine`, y los reales conservan `false`.
2. **Given** el consumidor procesando mensajes, **When** se consultan sus contadores, **Then** existen, al menos, los de: mensajes recibidos, eventos nuevos, versiones más recientes aplicadas, versiones antiguas tardías, reenvíos ignorados, conflictos «mismo `updated`, contenido distinto», conversiones de milisegundos a UTC, valores nulos conservados como `NULL`, cuarentenas por motivo y cuarentenas duplicadas (mismo original y motivo, sin fila nueva).
3. **Given** los contadores, **When** se compara con el estado de la base tras una secuencia conocida, **Then** son coherentes con ella (por ejemplo, tras la secuencia de la FAQ 12: 5 recibidos, 2 eventos nuevos, 1 versión más reciente aplicada, 2 reenvíos ignorados, 5 conversiones de milisegundos a UTC (una por mensaje válido transformado, ver FR-023) y 0 antiguas tardías no vistas, porque la versión de 10:05 repetida ya estaba en el historial; la prueba 4 con una antigua tardía no vista se añade como caso aparte).
4. **Given** los contadores, **When** se interpretan, **Then** sirven solo como registro de transformaciones del pipeline (C8): las estadísticas de la API se calculan siempre desde el estado actual (constitución §8).

---

### User Story 6 - Base lista y lógica reutilizable (Priority: P2) — Diferido (parcial)

> **Diferido**: escenarios 6.1 (catálogo de países; se retoma en geografia-pais) y 6.3 (paridad `live`/`replay`; el replay queda fuera de alcance). Los escenarios 6.2 y 6.4 sí están implementados y probados. Resuelto en 005-geografia-pais (6.1, catálogo).

Quien arranca el sistema desde cero obtiene la base preparada para el consumidor (esquemas, catálogo de países, tabla de fechas) sin pasos manuales, y quien construya el histórico o el replay puede reutilizar exactamente la misma lógica de procesamiento.

**Why this priority**: Es la base de las historias anteriores (países y fechas son claves foráneas) y evita duplicar lógica en `historico-2025` y `replay` (constitución §14).

**Independent Test**: Arrancar con un volumen limpio, comprobar los 177 países cargados y que la tabla de fechas se rellena con eventos; ejecutar las funciones puras de procesamiento en un test sin Kafka ni PostgreSQL.

**Acceptance Scenarios**:

1. **Given** una base nueva, **When** arranca el consumidor, **Then** el catálogo `data/catalogo/paises.geojson` queda cargado en `public.country` (177 entidades, `ADM0_A3` único) y repetir el arranque no duplica ni falla.
2. **Given** el procesamiento de un mensaje, **When** se separa su lógica, **Then** validar y transformar son funciones puras (entra un dato, sale un dato, sin red ni base de datos) que cualquier otro servicio Python puede importar desde el código compartido; la escritura en PostgreSQL y la lectura de Kafka son adaptadores aparte.
3. **Given** los esquemas `live` y `replay`, **When** se comparan sus columnas y restricciones, **Then** son idénticas (nota (a) de `db-schema.md` §8).
4. **Given** el consumidor, **When** se examinan sus credenciales, **Then** se conecta con su propio rol de base de datos (no el administrador) y solo con los permisos que fija `db-schema.md` §1.1.

---

### Edge Cases

- **Reenvío dentro de la misma sesión y tras un reinicio**: el resultado es idéntico (el estado vive en PostgreSQL, no en memoria).
- **Mensajes fuera de orden en el tema**: el orden no sustituye la comparación de `updated` (`kafka-message.md` §1); una versión antigua tardía no pisa a la reciente.
- **Evento con `updated` mayor que llega antes que otro con `updated` menor del mismo evento**: ambas versiones se conservan, gana la mayor.
- **Evento con `mag` nula y luego con `mag` presente (o a la inversa)**: la versión con `updated` mayor manda; nunca se rellena con 0.
- **Base de datos caída a mitad de lote**: ningún offset de un mensaje no guardado queda confirmado; al volver, el lote se reprocesa sin duplicar.
- **Fallo al escribir en cuarentena** (por ejemplo base caída o permisos): no se confirma el offset; se trata igual que un fallo de base de datos (reintento, sin recursión a otra cuarentena). El saneado no depende de este fallo: se aplica antes del `INSERT` (ver el caso siguiente).
- **Contenido con `\u0000` o bytes no UTF-8** (ni `jsonb` ni `text` los admiten) en el valor, en `event_id` o en `source`, para cualquier motivo de cuarentena: se detecta antes del `INSERT` inspeccionando el contenido, y la cuarentena guarda todos los textos saneados/escapados (o `event_id`/`source` a `NULL`), `original` a `NULL` y el hash de los bytes originales; nunca bloquea la partición. Si el intento saneado aun así falla, es un error de base: reintento sin recursión.
- **Copia a cuarentena con sobre defectuoso** (`source` fuera de los tres valores del `CHECK`, `event.id` o `source` que no son cadena, `is_synthetic` ausente o no booleano): la fila se escribe con `source` a `NULL`, `event_id` a `NULL` o `is_synthetic` a `false` según corresponda (FR-011), de modo que el `INSERT` nunca viola el `CHECK` ni el `NOT NULL`; no se trata como error de base ni bloquea la partición.
- **JSON válido con sustituto suelto (`\ud800`)**: su texto no se puede codificar a UTF-8; entra por la vía de saneado (FR-011). **JSON demasiado anidado** (`RecursionError`): se trata como `invalid_json`. Ninguno tumba al consumidor.
- **JSON válido que no es objeto** (`null`, `[]`, `123`): `invalid_envelope`.
- **Valor Kafka nulo (tombstone) o vacío**: cuarentena `invalid_json`, `raw_text` vacío, hash de cero bytes (US3.10).
- **Regla general de no fallo por contenido** (FR-014): ningún contenido de mensaje hace fallar una escritura (versión, evento actual o cuarentena) por una causa que dependa del contenido. Tipos erróneos o `bool` como número (`invalid_field_type`, `missing_time`, `missing_updated`, `invalid_envelope`), `NaN`/`Infinity`/números enormes/`\u0000`/sustitutos sueltos/bytes no UTF-8 (motivo del contrato; `original` a `NULL` y `raw_text` saneado si no es almacenable; `db_constraint_violation` si es válido por contrato pero no cabe en `jsonb`), enteros de más de 4300 dígitos (`invalid_json`) y `event.id` de más de 512 caracteres (`value_out_of_range`; `event_id` a `NULL` en cuarentena) se resuelven antes del `INSERT`.
- **Error persistente de otra clase NO dependiente del contenido** (p. ej. `54*` por entorno o configuración): bloquea la partición por diseño (reintento sin límite, registro por intento). Es un límite conocido aceptado por el alumno, sin cola de mensajes muertos. No aplica a fallos que dependan del contenido del mensaje: esos son un defecto de la validación previa.
- **Mismo original inválido repetido**: una sola fila de cuarentena por (hash del original, motivo).
- **Mensaje sin clave Kafka**: se trata como `missing_id` si además falta `event.id`; se va a cuarentena sin bloquear.
- **Día UTC nuevo**: la tabla de fechas lo recibe en el mismo flujo antes de escribir el evento; varios mensajes del mismo día no fallan por duplicado.
- **Mensaje muy grande o campos desconocidos de primer nivel**: se ignoran los desconocidos del sobre; los de `event` se conservan en el original.
- **Valores de `mag` o profundidad en el límite** (−10, 15, −100, 1000): válidos; fuera de ellos, cuarentena con su motivo.
- **Reinicio con grupo de consumo nuevo (sin offset guardado)**: se lee desde el principio del tema; la idempotencia hace seguro releer.

## Requirements *(mandatory)*

### Functional Requirements

**Procesamiento de cada mensaje (C1, C2)**

- **FR-001**: El consumidor MUST procesar cada mensaje de `earthquakes.live` en este orden: validar → transformar (milisegundos a UTC) → una transacción en PostgreSQL → commit en PostgreSQL → commit del offset de Kafka.
- **FR-002**: El offset MUST confirmarse manualmente y solo después del commit en PostgreSQL (o, en el caso de un mensaje a cuarentena, después de que la fila de cuarentena esté guardada). Si la base de datos falla, el offset de ese mensaje MUST NOT confirmarse.
- **FR-003**: Las reglas de validación, limpieza y enriquecimiento MUST estar explícitas y documentadas (lista en `kafka-message.md` §6 y en la memoria), y cada decisión relevante (guardado, reenvío, cuarentena, conflicto, error) MUST dejar una línea de registro con el `event_id`.
- **FR-004**: El consumidor MUST validar usando únicamente las reglas y los motivos de `kafka-message.md` §6, en el orden de prevalencia allí fijado, antes de intentar escribir. Esa validación incluye la regla general de FR-014 (tipo, almacenabilidad y longitud de todo lo que se escribe).

**Idempotencia y versiones (C3, C4)**

- **FR-005**: Dentro de la transacción de un mensaje válido, el consumidor MUST insertar la versión en el historial ignorando el conflicto por (`event_id`, `updated_ms`), y MUST actualizar el estado actual solo si el `updated` entrante es estrictamente mayor que el guardado (`db-schema.md` §5).
- **FR-006**: Repetir un mensaje ya procesado MUST NOT cambiar el estado actual, el historial ni los recuentos de ninguna tabla.
- **FR-007**: Una versión con `updated` menor y no vista antes MUST conservarse en el historial sin sustituir al estado actual; con `updated` menor o igual NUNCA se sustituye una versión mayor (constitución §2).
- **FR-008**: Un evento MUST corresponder a una única fila actual.
- **FR-009**: El consumidor MUST distinguir «versión nueva» de «reenvío» a partir del resultado de la inserción en el historial (cero filas = ya existía), y ante «mismo `updated`, contenido distinto» MUST conservar la primera versión recibida, anotarlo en el registro con el `event_id` y contarlo (C8), sin cambiar contratos.
- **FR-010**: El estado actual y la versión de un mensaje MUST escribirse en la misma transacción: nunca queda una sin la otra.

**Cuarentena (C5, prueba 6)**

- **FR-011**: Todo mensaje inválido MUST ir a la tabla de cuarentena del esquema `live` con su motivo, el valor original (o `raw_text` si no es JSON), su hash, la marca de sintético si procede y la referencia al mensaje (tema, partición, offset); su offset MUST confirmarse para no bloquear la cola. El hash (`original_sha256`) MUST ser el SHA-256 en hexadecimal en minúsculas (64 caracteres, exigido por el `CHECK` `^[0-9a-f]{64}$`) de los bytes del valor tal como se recibió de Kafka, sin deserializar ni re-serializar, y se calcula igual para `invalid_json`. Si el contenido no puede almacenarse tal cual (carácter nulo `\u0000` o bytes que no son UTF-8 válido en el valor, en `event_id` o en `source`), el consumidor MUST, para CUALQUIER motivo de cuarentena, guardar una representación saneada o escapada de todos los campos de texto que escribe (`raw_text` con el nulo escapado y los bytes inválidos sustituidos o escapados, `original` a `NULL`; `event_id` y `source` saneados o a `NULL`, que `db-schema.md` §3.5 permite; cumple el `CHECK` de al menos uno de `original`/`raw_text`) y SIEMPRE el `original_sha256` calculado sobre los bytes originales recibidos. Este saneado se decide ANTES del `INSERT` inspeccionando el contenido (NUL o bytes no UTF-8), no por el SQLSTATE devuelto. Si el intento saneado falla, es un error de base (FR-014), sin recursión. Un valor Kafka nulo o vacío se trata como no parseable: motivo `invalid_json`, `raw_text` vacío y hash de cero bytes. El detalle exacto del saneado se fija en el plan. (Decisión confirmada por el alumno.) **Copia a cuarentena** (decisión provisional del orquestador, pendiente de confirmar por el alumno; cabe en la nulabilidad de `db-schema.md` §3.5 y no cambia ningún contrato): para que el `INSERT` de cuarentena nunca viole un `CHECK` ni un `NOT NULL` por el contenido del mensaje, en la fila de `quarantine` `source` solo se copia si es exactamente uno de los valores que admite el `CHECK` del DDL (`usgs_feed`, `usgs_historical`, `replay_demo`) y si no va a `NULL`; `event_id` solo se copia si es una cadena (saneada si procede) y si no va a `NULL`; `is_synthetic` solo se copia si es booleano y si no va a `false`. **Casos que no pueden tumbar al consumidor**: un JSON válido con un sustituto suelto (p. ej. `\ud800`), cuyo texto no se puede codificar a UTF-8, entra por la vía de saneado; un JSON demasiado anidado (`RecursionError` al deserializar) se trata como `invalid_json`; un JSON válido que no es un objeto (`null`, `[]`, `123`) se trata como `invalid_envelope` (`kafka-message.md` §6: carece de los campos de primer nivel obligatorios). Ninguno bloquea la partición. **Regla general**: además de lo anterior, la copia a cuarentena respeta las tres comprobaciones previas de FR-014 (tipo, almacenabilidad, longitud): `event_id` a `NULL` si no es cadena o supera el tope de longitud, y `original` a `NULL` con `raw_text` saneado si el original no es almacenable como `jsonb` (p. ej. contiene `NaN`, `Infinity`, `-Infinity`), conservando siempre el `original_sha256` de los bytes recibidos. (Decisión provisional del orquestador, pendiente de confirmar.)
- **FR-012**: Un mensaje MUST generar como máximo una fila de cuarentena, con el primer motivo que falle en el orden de prevalencia del contrato; reprocesar el mismo original (mismos bytes, mismo `original_sha256`) por el mismo motivo MUST NOT duplicar la fila.
- **FR-013**: Un mensaje inválido MUST NOT crear ni modificar filas en `current_event` ni en `event_version`, y MUST NOT inventarse coordenadas ni otros valores.
- **FR-014**: Si la base rechaza con un error de SQLSTATE clase 23 (integridad) o clase 22 (data exception), o con la excepción equivalente del cliente de datos cuando no trae SQLSTATE (p. ej. un `DataError` por un `\u0000`), el `INSERT` o el `COMMIT` de un mensaje que ya pasó todas las validaciones, el consumidor MUST hacer rollback de ese mensaje, llevarlo a cuarentena con motivo `db_constraint_violation` y confirmar su offset. Cualquier otro error de base (conexión, `08*`, `40*`, `53*`, `57*`, indisponibilidad, timeout, permisos) MUST tratarse como fallo transitorio: reintento con espera creciente acotada por un tope máximo (el valor del tope y la tasa de registro se fijan en el plan), sin límite de intentos, offset sin confirmar y sin cuarentena. Cada intento fallido deja un registro con `event_id`, tema, partición y offset (tasa limitada por la espera acotada, sin crecimiento ilimitado de contenido). Un fallo del `INSERT` en cuarentena MUST tratarse como error de base transitorio (reintento sin commit de offset), sin recursión a otra cuarentena. La fila de cuarentena se construye siempre con la regla de copia de FR-011 (`source` solo si es un valor admitido por el `CHECK`, si no `NULL`; `event_id` solo si es cadena; `is_synthetic` solo si es booleano, si no `false`), de modo que un `source` inválido o un `is_synthetic` no booleano nunca provocan un fallo del `INSERT` de cuarentena. La excepción del saneado (confirmada por el alumno) no se decide por el SQLSTATE: FR-011 obliga a detectar el contenido no almacenable (NUL, bytes no UTF-8) antes del `INSERT` y a escribir ya la representación saneada con el hash de los bytes originales, para que la cuarentena nunca bloquee la partición (constitución §6). Si ese intento saneado aun así falla, se aplica la regla general: error de base, reintento sin recursión. Límite conocido aceptado por el alumno, solo para errores de entorno o persistentes NO dependientes del contenido del mensaje (p. ej. `54*` por configuración, disco, memoria, permisos): bloquean la partición, sin cola de mensajes muertos.
  - **Regla general (decisión provisional del orquestador, a confirmar por el alumno, no bloqueante)**: ningún contenido de mensaje puede hacer fallar una escritura del consumidor (versión, evento actual o cuarentena) por una causa que dependa del contenido. Se garantiza con tres comprobaciones previas al `INSERT`, antes de tocar la base, y un fallo por contenido que se escape de ellas es un defecto de la validación, no un «límite aceptado»:
    1. **Validación de tipo de TODAS las columnas que se escriben.** Cadenas (`event.id`, `place`, `url`, `status`, `magType`, `source`, `mode`, `ingested_at`, `replay_at`) = `str` (o `null` donde la columna admite `NULL`); numéricos (`time`, `updated`, `sig` enteros; `mag`, profundidad, `lon`, `lat` entero o decimal reales) = `int`/`float` reales y NUNCA `bool` (en Python `bool` es subclase de `int`; se comprueba por tipo exacto); `is_synthetic` = `bool` exacto. Motivos, todos ya existentes en `kafka-message.md` §6 y en su orden de prevalencia: `event.id` que no es cadena, y `place`/`url`/`status`/`magType`/`sig`/`mag`/profundidad/coordenadas con tipo incorrecto → `invalid_field_type`; `time`/`updated` ausentes o no enteros (incluido `bool`) → `missing_time`/`missing_updated`; `source`/`mode`/`ingested_at`/`replay_at`/`is_synthetic` con tipo o formato no permitido (incluido `ingested_at` fuera del rango de `timestamptz`) → `invalid_envelope`. No hace falta cambiar el contrato.
    2. **Almacenabilidad.** Antes del `INSERT` se detectan `NaN`, `Infinity`, `-Infinity` (tras deserializar, también los que vienen de números como `1e999999`), números fuera del rango representable por `numeric`/`jsonb`/`bigint`/`integer`, `\u0000`, sustitutos sueltos y bytes que no son UTF-8, tanto en las columnas escritas como en cualquier parte del `original` (que va a `jsonb`). Si el contenido invalida el mensaje por contrato, rige su motivo (p. ej. `mag` `NaN` → `mag_out_of_range`; `lat` infinita → `coordinates_out_of_range`; `sig` o `time`/`updated` fuera de rango → `value_out_of_range`, incluyendo los instantes que `timestamptz` admite pero `date_dim` no, porque `year` es `smallint`; el plan fija el rango admitido, que es un subconjunto del de `timestamptz`) y la cuarentena guarda `original` a `NULL` y `raw_text` saneado cuando el original no es almacenable como `jsonb`, con el `original_sha256` de los bytes recibidos. Si el mensaje es válido por contrato pero su original no es almacenable como `jsonb` (p. ej. `NaN` en `dmin`, o `\u0000` en `place`), se trata sin tocar la base como `db_constraint_violation` (último recurso del contrato: es exactamente el rechazo que haría `event_version.original`), con la misma forma de fila de cuarentena, sin reintentos y con offset confirmado. Bytes que no son UTF-8, `ValueError` de `json.loads` por enteros demasiado largos (límite de dígitos de Python) y cualquier excepción de deserialización equivalente (`RecursionError`, etc.) → `invalid_json`.
    3. **Límite de longitud** de `event.id` y de toda columna indexada. Tope documentado: 512 caracteres para `event.id` (valor provisional; el plan lo fija definitivamente), compatible con el límite de fila de índice de PostgreSQL (unos 2700 bytes; 512 caracteres de hasta 4 bytes UTF-8 son 2048 bytes, más `updated_ms` en la clave primaria). Un `event.id` que lo supera en un mensaje → `value_out_of_range` (el motivo más cercano del contrato; ninguno cubre la longitud sin cambiarlo), y en la copia a cuarentena `event_id` se pone a `NULL` si supera el tope (el índice parcial `ix_quarantine_event_id` no admite filas más largas). El resto de columnas indexadas tiene tamaño acotado (`updated_ms`, `event_time`, `mag`, `country_id` `NULL`, `original_sha256` de 64, `reason` de la lista).

    Clasificación de excepciones del cliente: qué excepción equivale a SQLSTATE clase 22/23 (psycopg2 `ValueError` por `\u0000` frente a psycopg3 `DataError`/`IntegrityError`) la fija el plan según el cliente elegido; no cambia las reglas anteriores, porque estas comprobaciones van antes del cliente.
- **FR-015**: El consumidor MUST comprobar que `mode` coincide con el modo del tema leído; si no coincide, MUST llevar el mensaje a la cuarentena del esquema que corresponde al tema con motivo `mode_topic_mismatch`.

**Nulos, negativos, tiempos y enriquecimiento (C6, C7)**

- **FR-016**: Los valores ausentes (`mag`, profundidad, `place`, `status`, `url`, `sig`, `mag_type`) MUST guardarse como `NULL`, nunca como 0 (constitución §5).
- **FR-017**: Una magnitud o profundidad negativa MUST NOT rechazarse por ser negativa; solo se rechaza lo que sale de los límites de cordura del contrato.
- **FR-018**: El consumidor MUST convertir `time` y `updated` de milisegundos Unix a UTC conservando el valor original en milisegundos, y los dos MUST ser coherentes entre sí. El tiempo del evento y el tiempo de procesamiento (`ingested_at`, `received_at`) MUST guardarse en campos distintos.
- **FR-019**: El consumidor MUST rellenar `date_id` con el día UTC del instante del evento, asegurando antes que ese día existe en la tabla de fechas sin fallar si ya existe.
- **FR-020**: El consumidor MUST copiar `source`, `is_synthetic`, `ingested_at` y `replay_at` del sobre a las tablas, y guardar el feature original íntegro y sin modificar en el historial.
- **FR-021**: `country_id` MUST quedar `NULL` en todos los eventos de esta feature; no se asigna país ni se infiere del texto `place`.

**Datos sintéticos y contadores (C13, C8)**

- **FR-022**: La marca `is_synthetic` MUST propagarse a `current_event`, `event_version` y `quarantine`, de modo que cualquier consulta pueda separar sintéticos de reales.
- **FR-023**: El consumidor MUST llevar contadores de las transformaciones que cambian datos y de las decisiones del pipeline (mínimo: los de la Historia 5, escenario 2), exponerlos en el registro en un resumen periódico y al detenerse, y reconciliarlos con lo que hay en la base en la verificación (partiendo de una base y un grupo de consumo limpios, y de una sesión sin reinicios, ya que los contadores viven en memoria). Cada contador se incrementa una sola vez por mensaje y sesión, tras el commit del offset de Kafka (que sigue al commit en PostgreSQL o a la fila de cuarentena guardada); los reintentos por fallo de base o de Kafka no incrementan "recibidos" ni ningún otro contador, y solo se registran en el log. Limitación: si el commit del offset falla y hay redelivery en la misma sesión, el mensaje reentregado se cuenta como un mensaje nuevo recibido (reenvío); esto se documenta y SC-009 se verifica sin fallos inyectados. La unidad del contador de conversiones de milisegundos a UTC es un incremento por mensaje válido transformado (se convierten `time` y `updated` juntos), incluidos los reenvíos y los conflictos, porque la conversión ocurre antes de saber si la versión es nueva. Los mensajes en cuarentena por validación (todos los motivos salvo `db_constraint_violation`) no cuentan la conversión; los de `db_constraint_violation` sí, porque se transforman antes de fallar en la base. Se concilia así, donde "cuarentenas por validación" y `db_constraint_violation` INCLUYEN los duplicados (es decir, = filas nuevas + filas duplicadas de ese grupo de motivos): conversiones = recibidos − cuarentenas por validación (nuevas + duplicadas); además, conversiones = eventos nuevos + versiones más recientes aplicadas + antiguas tardías + reenvíos ignorados + conflictos + `db_constraint_violation` (nuevas + duplicadas). Un duplicado de cuarentena (`ON CONFLICT DO NOTHING` sin fila nueva) se cuenta en el contador aparte "cuarentenas duplicadas" (desglosado por motivo) y no en "cuarentenas por motivo", de modo que "cuarentenas por motivo" coincide con el recuento SQL de `live.quarantine`; el duplicado cuenta como recibido y, si era de validación, no cuenta conversión (si era `db_constraint_violation`, sí). Comprobaciones: secuencia FAQ 12 (sin cuarentenas): 5 recibidos − 0 = 5 conversiones y 2 + 1 + 0 + 2 + 0 + 0 = 5; secuencia FAQ 12 más un inválido repetido dos veces (1 fila nueva + 1 duplicada): 7 recibidos − (1 + 1) = 5 conversiones.
- **FR-024**: Los contadores MUST NOT usarse para calcular estadísticas de la API ni sustituir a las agregaciones desde el estado actual (constitución §8).
- **FR-036**: La verificación de SC-009 (contadores contra SQL, FR-023) MUST cubrir, como mínimo, estos casos concretos: (1) la secuencia de la FAQ 12 sin cuarentenas (5 recibidos → 5 conversiones); (2) la FAQ 12 más un inválido repetido (US3.5: 1 fila nueva + 1 duplicada, contador "cuarentenas duplicadas"; 7 recibidos → 5 conversiones); (3) la FAQ 12 más un `db_constraint_violation` repetido (1 fila nueva + 1 duplicada, que sí cuenta conversión; 7 recibidos → 7 conversiones: 7 − 0 cuarentenas por validación, y 2 + 1 + 0 + 2 + 0 + (1 + 1) = 7). En cada caso se aplican las fórmulas de FR-023. (La numeración FR-036 se mantiene fuera de secuencia para no romper referencias externas.)

**Preparación de la base y catálogos**

- **FR-025** *(Diferido: no hace falta para C1–C8, C13 ni las pruebas 2, 3, 4, 6 y 8; `country_id` queda `NULL`; se retoma en geografia-pais)*: El consumidor MUST cargar el catálogo `data/catalogo/paises.geojson` (sin modificarlo) en `public.country` al arrancar, de forma repetible sin duplicar ni fallar. Resuelto en 005-geografia-pais.
- **FR-026** *(Diferido: endurecimiento del arranque; el esquema ya lo crea `sql/001_schema.sql`)*: El esquema (`sql/001_schema.sql`) y los roles (`sql/002_roles.sql`) ya los aplica `infra-compose`; el consumidor MUST asumirlos, esperar a que la base esté lista con reintentos y fallar con un mensaje claro si falta una tabla esperada. Resuelto en 005-geografia-pais.
- **FR-027**: El consumidor MUST usar su propio rol de base de datos (`observatory_consumer`) y solo los permisos que le asigna `db-schema.md` §1.1; cualquier permiso adicional que resulte necesario se anota como escalado, no se concede en silencio.
- **FR-028**: El consumidor MUST consumir `earthquakes.live` con un grupo de consumo propio y MUST leer desde el principio del tema cuando el grupo no tiene offset guardado.
- **FR-029**: Los reintentos de conexión a Kafka y a PostgreSQL, el latido y el healthcheck del consumidor MUST seguir cumpliendo A4 (`infra-compose`), y «saludable» MUST seguir significando que el consumidor sigue procesando. El latido NO se renueva durante el reintento por error de base o mensaje venenoso, por lo que el contenedor puede quedar `unhealthy`; es consecuencia aceptada y su detalle, junto con el valor del tope de espera y de la tasa de registro, se fija en el plan.

**Estructura del código y pruebas (constitución §14)**

- **FR-030**: Las funciones puras de procesamiento (validar y transformar) MUST estar separadas de la E/S (Kafka, PostgreSQL) y alojadas en el código compartido, de modo que `historico-2025` y `replay` puedan reutilizarlas sin copiarlas.
- **FR-031**: MUST existir una prueba automática que reproduzca la secuencia de la FAQ 12 y compruebe 2 eventos actuales, E1 con mag 4.6 y 3 filas de versión en total (SC-001), y una consulta SQL que sirva de evidencia. Debe incluir además un caso de versión antigua tardía no vista previamente (prueba 4) que se conserva en el historial sin pisar el estado actual.
- **FR-032** *(Diferido: el consumidor solo escribe en `live`; el replay queda fuera de alcance)*: MUST existir una prueba automática que compare las columnas y restricciones de los esquemas `live` y `replay` (`db-schema.md` §8 (a)).
- **FR-033**: Las pruebas de la lógica pura MUST ejecutarse sin Kafka ni PostgreSQL; las de integración, contra PostgreSQL 16.

**Documentación y cierre (constitución §16)**

- **FR-034**: La feature MUST dejar documentadas las reglas de calidad, la transacción y el orden de commits, la cuarentena y la secuencia de la FAQ 12, y guardar las evidencias en `docs/evidencias/consumidor-idempotente/` (SQL antes/después, logs del reinicio, fila de cuarentena).
- **FR-035**: Al cerrar la feature, `README.md` y `CODEMAP.md` MUST estar actualizados; esta feature MUST NOT modificar `kafka-message.md`, `db-schema.md` ni `api.md`.

### Fuera de alcance

Asignación de país por punto en polígono (`country_id` queda `NULL`), productor real y consultas a USGS, histórico 2025, replay (el consumo de `earthquakes.replay` y la escritura en el esquema `replay`), endpoints de la API y frontend. El enrutado por `mode` solo se ejercita para rechazar (`mode_topic_mismatch`); el consumo real de `earthquakes.replay` lo aporta la feature `replay`, que reutilizará la misma lógica.

### Key Entities *(include if feature involves data)*

- **Mensaje de evento**: sobre del contrato `kafka-message.md` (`source`, `mode`, `ingested_at`, `replay_at`, `is_synthetic`, `event`), clave `event.id`. Entra por `earthquakes.live`.
- **Evento actual** (`live.current_event`): la versión más reciente de cada evento; una fila por `event_id`. Es la base de todas las agregaciones.
- **Versión de evento** (`live.event_version`): una fila por (`event_id`, `updated_ms`) recibido; guarda el original íntegro y la referencia al mensaje.
- **Cuarentena** (`live.quarantine`): original inválido con motivo, hash y referencia (tema, partición, offset).
- **País** (`public.country`): catálogo de 177 entidades cargado por el consumidor; no se asigna aún a los eventos.
- **Fecha** (`public.date_dim`): un día UTC por fila, creado al llegar el primer evento de ese día.
- **Contadores de transformaciones**: registro de cuántos registros cambia cada transformación (C8); no son agregaciones de negocio.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras la secuencia de la FAQ 12 (5 mensajes: E1 10:05 mag 4.2, repetición, E1 10:09 mag 4.6, E1 10:05 repetida, E2), la base contiene exactamente 2 eventos actuales, E1 con mag 4.6 y updated 10:09, y 3 filas de versión en total (E1: 10:05 y 10:09; E2: 1). Es la lectura del «3 versiones» del roadmap F3 y de la FAQ 12 («tres versiones distintas observadas en total»: E1×2 + E2×1), compatible con la clave (`event_id`, `updated_ms`). E2 tiene updated 10:12 y mag 3.1.
- **SC-002**: Reenviar 100 veces cualquier mensaje ya procesado deja el recuento de filas de todas las tablas de evento y versión en 0 cambios (prueba 2).
- **SC-003**: Una versión antigua tardía deja el estado actual del evento sin cambios en el 100 % de los casos de prueba y conserva su versión en el historial (prueba 4); una versión posterior cambia el estado actual en el 100 % (prueba 3).
- **SC-004**: Un mensaje con coordenadas inválidas (latitud 145) produce 1 fila de cuarentena con su motivo y referencia, 0 filas en las tablas de evento y 0 mensajes posteriores bloqueados (prueba 6).
- **SC-005**: Tras detener y reiniciar el consumidor en el punto más desfavorable (después del commit en PostgreSQL y antes del commit del offset), las tablas quedan con 0 duplicados y 0 mensajes perdidos respecto a la ejecución sin reinicio (prueba 8).
- **SC-006** *(Diferido: la prueba con PostgreSQL parado en Docker real no se ejecutó; el comportamiento está cubierto con dobles en pruebas unitarias)*: Con la base de datos parada durante una prueba, 0 offsets de mensajes no guardados quedan confirmados, y tras restablecerla el 100 % de los mensajes pendientes se procesa sin intervención manual.
- **SC-007**: 0 valores `NULL` sustituidos por 0 y 0 valores negativos válidos rechazados en el conjunto de casos de prueba; el 100 % de los tiempos guardados tiene su par UTC/milisegundos coherente.
- **SC-008**: El 100 % de las filas procedentes de mensajes sintéticos lleva la marca de sintético en las tres tablas (actual, versión, cuarentena), y 0 filas reales la llevan.
- **SC-009** *(Se verifica con `process_record` y una base temporal, no con el consumidor en Docker)*: Partiendo de una base y un grupo de consumo limpios, y en una sola sesión del consumidor, tras los casos concretos de FR-036 (FAQ 12, inválido repetido y `db_constraint_violation` repetido) los contadores del consumidor coinciden en el 100 % con las cifras obtenidas por consulta SQL sobre la base.
- **SC-010**: Las funciones puras de validación y transformación se ejecutan en una suite de tests sin Kafka ni PostgreSQL y se reutilizan sin copias desde otro punto de entrada.
- **SC-011** *(Diferido: depende del catálogo de países; se retoma en geografia-pais)*: Tras `docker compose up --build -d` desde un volumen limpio, el consumidor llega a estado saludable, `public.country` contiene 177 filas y repetir el arranque no cambia ese número. Resuelto en 005-geografia-pais.
- **SC-012**: Una persona ajena al desarrollo puede reproducir la secuencia de la FAQ 12 y comprobar el resultado siguiendo solo la documentación de la feature.

## Assumptions

- La feature parte de `002-infra-compose`: Compose, Kafka, PostgreSQL 16, imagen Python compartida, reintentos, latido y roles ya existen; el consumidor mínimo se sustituye por el real.
- El rol `observatory_consumer` ya existe con los permisos de `db-schema.md` §1.1 (`sql/002_roles.sql`). Esta feature no necesita más permisos para guardar versiones, estado actual, fechas y cuarentena; si el plan descubre que falta alguno, se escala sin tocar el contrato.
- El tema que se consume es solo `earthquakes.live`; el modo de la lógica compartida se parametriza por tema para que el replay la reutilice, pero el consumo de `earthquakes.replay` queda fuera.
- El productor mínimo de `002` publica eventos sintéticos (`source = replay_demo`, `mode = live`, `is_synthetic = true`); por tanto la cadena productor → consumidor → base se puede ejercitar con ellos. Sus ids (`synthetic-N`) no chocan con ids reales.
- La referencia al original en cuarentena se identifica por el hash y por (tema, partición, offset). El hash (`original_sha256`) es el SHA-256 hex (minúsculas, 64 caracteres) de los bytes del valor tal como se recibió, sin re-serializar; vale igual para `invalid_json`. Es coherente con `db-schema.md` §3.5 (SHA-256 hex del original, clave de idempotencia con `reason`), que no impone otra forma de cálculo.
- Los contadores de C8 se mantienen en memoria y se vuelcan al registro; no se persisten en la base (persistirlos añadiría tablas fuera del contrato). Tras un reinicio empiezan de cero y la verificación usa el registro de cada sesión más SQL.
- La verificación de los contadores de C8 parte de una base y un grupo de consumo limpios; solo así la conciliación con SQL es exacta.

### Notas para el plan (sin diseñar)

- El rol `observatory_consumer` no tiene `SELECT` sobre la cuarentena: no se puede usar `RETURNING` ni `ON CONFLICT DO UPDATE` en ella, solo `ON CONFLICT DO NOTHING` simple **sin destino de conflicto**: un destino con columnas exigiría `SELECT` (`42501`). Una prueba con el rol real lo demuestra. Las pruebas que lean la cuarentena usan otro rol.
- `db_constraint_violation` puede saltar en el `COMMIT` (la FK de `event_version` es diferida) y no solo en el `INSERT`, y cubre SQLSTATE clase 23 y clase 22 (o la excepción equivalente del cliente de datos cuando no trae SQLSTATE); el manejo del rollback debe cubrir ambos momentos y ambas clases.
- El latido no se renueva durante el reintento por error de base; el plan fija el detalle (p. ej. impacto en el healthcheck).
- El mecanismo para forzar el corte entre el commit de PostgreSQL y el commit del offset (prueba 8) es decisión del plan.
- La conversión de milisegundos a UTC es la única transformación que altera valores; limpiar espacios en `place` u otras normalizaciones no entran, para no ampliar el alcance ni alterar el original.
- Las pruebas de aceptación 2, 3, 4, 6 y 8 se demuestran con mensajes sintéticos etiquetados; la prueba 2 completa (con productor real) se cierra en `productor-live`.
- El catálogo `paises.geojson` es el entregado (177 entidades, `ADM0_A3` único) y no se modifica.
- La numeración `003` de la carpeta difiere de la `004` de `03-procedimiento-ejecucion.md` §4; se mantiene la carpeta y el slug como referencia.

## Preguntas para el alumno

Decisiones confirmadas por el alumno (ya incorporadas a la spec; ninguna cambia un contrato):

- **Confirmada: SQLSTATE clase 22 y clase 23 van a `db_constraint_violation`** (FR-014); el resto de errores se reintenta sin límite.
- **Confirmada: saneado del contenido que no cabe en la cuarentena** (FR-011, FR-014, US3.9): se aplica a todos los campos de texto que se escriben (`raw_text`, `event_id`, `source`), para cualquier motivo, y se detecta antes del `INSERT` inspeccionando el contenido; `original_sha256` siempre sobre los bytes originales; si el intento saneado falla, error de base sin recursión.
- **Confirmada: límite conocido** de que un error persistente de otra clase NO dependiente del contenido (p. ej. `54*` por entorno) bloquea la partición, sin cola de mensajes muertos; el latido no se renueva y el contenedor puede quedar `unhealthy`. (Los fallos dependientes del contenido ya no entran en este límite: ver pregunta 1.)
- **Confirmadas en clarify**: contadores por mensaje y no por intento, incrementados tras el commit del offset (con la limitación de redelivery documentada); cuarentena deduplicada por bytes; duplicados de cuarentena contados aparte.
Pendientes de confirmar (no bloqueantes; decisiones provisionales del orquestador, ninguna cambia un contrato ni el DDL):

1. **Regla general de no fallo por contenido** (FR-011, FR-014, US3.11-12) y sus tres comprobaciones previas al `INSERT`:
   - (a) Validación de tipo de todas las columnas escritas, `bool` excluido como número, con los motivos existentes del contrato.
   - (b) Almacenabilidad: `NaN`/infinitos/NUL/sustitutos/bytes no UTF-8/enteros enormes detectados antes del `INSERT`; `original` a `NULL` y `raw_text` saneado; mensaje válido por contrato pero no almacenable como `jsonb` → `db_constraint_violation` (el contrato no tiene motivo más específico); bytes no UTF-8 y enteros demasiado largos → `invalid_json`.
   - (c) Tope de 512 caracteres para `event.id` (el plan puede ajustar el valor), `value_out_of_range` en mensajes y `event_id` a `NULL` en cuarentena (el contrato no tiene un motivo de longitud; `value_out_of_range` es el más cercano). Alternativa: ampliar el contrato con un motivo propio, lo que exigiría decisión del alumno.
2. **Regla de copia a cuarentena** (FR-011, FR-014, US3.8, US3.9). Decisión provisional del orquestador: `source` solo si es `usgs_feed`, `usgs_historical` o `replay_demo` (si no `NULL`); `event_id` solo si es cadena (si no `NULL`); `is_synthetic` solo si es booleano (si no `false`). Cabe en db-schema.md §3.5 y en el DDL sin cambiar contratos. La alternativa sería dejar el bloqueo de la partición como otro límite documentado, difícil de defender para un caso común de `invalid_envelope`. Incluye el tratamiento de `\ud800` (saneado), JSON demasiado anidado (`invalid_json`) y JSON que no es objeto (`invalid_envelope`).
- **Cerrada: «3 versiones» de la FAQ 12.** La FAQ 12 y la clave (`event_id`, `updated_ms`) dan 2 versiones de E1 y 1 de E2; se interpreta como el total.

Siguen abiertas (recomendación: mantenerlas):

3. **Contadores de C8 solo en memoria y registro**, sin tabla propia. Recomendación: mantenerlo así para no ampliar el esquema; la evidencia se completa con SQL.
4. **Solo se consume `earthquakes.live`.** El consumo de `earthquakes.replay` queda para `replay`. Recomendación: mantenerlo, para no ampliar el alcance.
