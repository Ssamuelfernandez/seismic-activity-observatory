# Feature Specification: Geografía y país

**Feature Branch**: `005-geografia-pais`

**Created**: 2026-11-05

**Status**: Implemented (2026-11-05). 25/25 tareas. Evidencias: `docs/evidencias/geografia-pais/` (534 unitarias y 73 de integración sin fallos; `verify_consumer.py geo` 16/16). Tareas diferidas: ninguna. Pendiente del alumno: revisar y pasar `docs/borradores/geografia-pais.md` a la memoria (C9–C12).

**Input**: User description: "Asignar país a cada evento por punto en polígono y aplicar las reglas de validez completas en el consumidor. Retoma lo diferido de consumidor-idempotente (catálogo de países en `public.country` y comprobación del esquema al arrancar). Cubre C9-C12. Pruebas de aceptación 5 (magnitud nula) y 7 (evento marítimo)."

> Nota de numeración: `03-procedimiento-ejecucion.md` §4 llama a esta feature `005-geografia-pais` (F5). El nombre (slug) es el estable.

## Clarifications

### Session 2026-11-05

Respuestas con la opción recomendada (la herramienta no puede preguntar al alumno). Lo que toca contratos, alcance o dependencias está en "Preguntas para el alumno" con decisión provisional.

- Q: ¿Un punto exactamente sobre una frontera cuenta como dentro del país? → A: Sí. Se usa la relación «cubre» (el borde pertenece al polígono), no «contiene». Evita que un punto en el borde caiga en «sin país» y es lo que fija el roadmap §1 (C11).
- Q: ¿Qué país se asigna si el punto cae en varios polígonos del catálogo (territorios solapados)? → A: El de `ADM0_A3` menor en orden alfabético. Es determinista (el mismo punto da siempre el mismo país, también en un reinicio o en el histórico) y no depende del orden del archivo. Se anota una línea de log con el evento y los candidatos (C11).
- Q: ¿Qué pasa con un punto que no cae en ningún polígono (mar, territorios pequeños que el catálogo no incluye)? → A: `country_id = NULL` («Sin país asignado»). No se asigna el país más cercano. El evento se guarda y cuenta en el análisis (C12, constitución §4).
- Q: ¿En qué momento se calcula el país? → A: Después de validar y antes de escribir, solo para mensajes válidos, a partir de `lon`/`lat` de esa versión. Un mensaje a cuarentena no tiene país (la cuarentena no guarda país). Cuando una versión más reciente sustituye a la actual, el país se recalcula con sus coordenadas; una versión antigua tardía no cambia el estado actual, así que tampoco su país (constitución §2).
- Q: ¿Se corrigen los eventos ya guardados con `country_id` nulo antes de esta feature? → A: No. Las filas anteriores solo cambian si llega una versión con `updated` mayor. Límite conocido: no hay recálculo retroactivo; en el entorno de la clase se parte de una base limpia (`down -v`) o de eventos nuevos. Un recálculo masivo quedaría para el histórico (`historico-2025`).
- Q: ¿Qué hace el consumidor si el catálogo no se puede cargar o tiene `ADM0_A3` duplicados? → A: No empieza a consumir: termina con error claro y Compose lo reinicia (mismo criterio que la comprobación de esquema). Sin catálogo no hay país fiable y no se debe escribir con país silenciosamente vacío (C10).
- Q: ¿Qué hace el consumidor si le llega un mensaje con `type` distinto de `earthquake`? → A: Ver "Preguntas para el alumno" (el contrato dice que el productor no lo publica y no define motivo de cuarentena para ello). Provisional: el productor lo excluye (ya implementado en `productor-live`) y el caso sintético se demuestra ahí.
- Q: ¿Cómo se demuestra el tipo no-earthquake? → A: Con un evento sintético etiquetado enviado al productor de pruebas (mock de USGS), comprobando la fila en `exclusion`. No se toca el consumidor.
- Q: ¿Hay contadores nuevos (C8) para el país? → A: No. La asignación es un dato derivado, no una conversión que cambie datos del mensaje; los recuentos «con país» y «sin país» se obtienen con una consulta SQL sobre `current_event` (constitución §8) y quedan como evidencia. Evita ampliar el contrato de contadores de `consumidor-idempotente`.

## User Scenarios & Testing *(mandatory)*

Los «usuarios» son quien evalúa el pipeline (profesor y alumno que lo defiende) y los servicios que leerán `country_id` más adelante (API, panel, histórico). Esta feature no añade pantallas ni endpoints.

### User Story 1 - Cada evento recibe su país por geometría (Priority: P1)

Un evento válido cuyas coordenadas caen dentro de un país del catálogo se guarda con su código `ADM0_A3`. El país nunca sale del texto `place`.

**Why this priority**: Es C9, la parte central de F5 y la base de los recuentos por país de la API.

**Independent Test**: Escribir un evento sintético en Madrid (lon -3,70, lat 40,42) y comprobar `country_id = 'ESP'`; repetir el procesamiento y comprobar que no cambia.

**Acceptance Scenarios**:

1. **Given** el catálogo cargado y un evento válido en Madrid cuyo `place` dice otra cosa, **When** se procesa, **Then** `current_event.country_id = 'ESP'` (el texto `place` no interviene).
2. **Given** un punto exactamente sobre una frontera entre dos países, **When** se asigna país, **Then** se obtiene uno de los dos (nunca `NULL`) y siempre el mismo (C11).
3. **Given** un punto que pertenece a varios polígonos del catálogo, **When** se asigna país, **Then** se elige el `ADM0_A3` menor en orden alfabético y queda una línea de log con el evento y los candidatos (C11).
4. **Given** un evento con una versión posterior cuyas coordenadas caen en otro país, **When** la versión nueva gana por `updated`, **Then** `country_id` pasa al país de la versión nueva; si llega una versión antigua tardía, `country_id` no cambia.
5. **Given** el catálogo real (`data/catalogo/paises.geojson`) y los eventos reales de USGS de un día (una descarga del feed `all_day` guardada en `docs/evidencias/geografia-pais/`), **When** se asigna país a cada uno en memoria (sin Kafka ni base), **Then** ninguno falla, y cada código asignado existe en el catálogo o el resultado es `NULL`; el cumplimiento de la clave foránea en la base lo demuestran los casos sintéticos.

---

### User Story 2 - Evento marítimo: «Sin país asignado» que sigue en el análisis (Priority: P1)

Un evento en mar abierto se guarda con `country_id = NULL`. No se le atribuye el país más cercano, no va a cuarentena y se cuenta en los totales.

**Why this priority**: Es la prueba de aceptación 7 y C12 (obligatorios).

**Independent Test**: Escribir un evento sintético en el Atlántico (lon -30, lat 35) y consultar `current_event`: fila presente, `country_id` nulo, mismo recuento total que si tuviera país.

**Acceptance Scenarios**:

1. **Given** un evento sintético válido en el Atlántico, **When** se procesa, **Then** hay una fila en `current_event` con `country_id IS NULL`, ninguna fila en `quarantine` y `place` no se usa para inferir nada.
2. **Given** eventos con y sin país, **When** se cuenta el total de `current_event`, **Then** el total incluye los de `country_id` nulo; la suma de «con país» y «sin país» es igual al total (la etiqueta «Sin país asignado» la pone la API, no esta feature).
3. **Given** un evento ya guardado con país, **When** llega una versión más reciente cuyas coordenadas caen en el mar, **Then** `country_id` pasa a `NULL` (no se conserva el país anterior).

---

### User Story 3 - Magnitud nula, negativos y coordenadas inválidas (Priority: P1)

Las reglas de validez del contrato se aplican completas: la magnitud nula se conserva como nula, magnitudes y profundidades negativas son válidas, y las coordenadas inválidas van a cuarentena con motivo y referencia al original, sin inventar punto ni país.

**Why this priority**: Prueba 5 (magnitud nula) y refuerzo de la prueba 6 con el país en juego (constitución §5 y §6).

**Independent Test**: Mensajes sintéticos etiquetados: mag nula en Madrid, mag `-0.06` con profundidad `-0.18`, lat 145 y un punto con longitud NaN; comprobar la base.

**Acceptance Scenarios**:

1. **Given** un evento sintético con `mag` nula en un país, **When** se procesa, **Then** `mag` es `NULL` (nunca 0) en `current_event` y `event_version`, `country_id` se asigna con normalidad y el evento cuenta en el análisis (prueba 5).
2. **Given** un evento con `mag = -0.06` y profundidad `-0.18`, **When** se procesa, **Then** se guarda con esos valores y con país.
3. **Given** un evento sintético con latitud 145, **When** se procesa, **Then** hay una fila de cuarentena con `reason = coordinates_out_of_range`, referencia al mensaje de Kafka, y no hay fila en `current_event` ni país asignado.
4. **Given** una geometría que no es `Point`, con menos de dos coordenadas o con longitud/latitud no finita, **When** se procesa, **Then** va a cuarentena (`invalid_geometry` o `coordinates_out_of_range`) y nunca llega al cálculo de país.
5. **Given** un mensaje sin `time` o `updated`, o con ellos no enteros, **When** se procesa, **Then** va a cuarentena (`missing_time` / `missing_updated`).

---

### User Story 4 - Catálogo cargado y esquema comprobado al arrancar (Priority: P2)

Al arrancar sobre una base nueva, el consumidor comprueba que el esquema está listo y carga las 177 entidades del catálogo en `public.country`; repetir el arranque no duplica ni cambia nada.

**Why this priority**: Sin filas en `public.country` no se puede guardar un `country_id` (clave foránea). Retoma lo diferido de `consumidor-idempotente` (FR-025, FR-026, SC-011). Incluye la comprobación de unicidad de `ADM0_A3` (C10).

**Independent Test**: Base limpia, arrancar el consumidor, contar `public.country` (177); reiniciar y volver a contar.

**Acceptance Scenarios**:

1. **Given** una base nueva con el esquema aplicado, **When** arranca el consumidor, **Then** `public.country` tiene 177 filas y una línea de log resume el total, las insertadas y las actualizadas.
2. **Given** el catálogo ya cargado, **When** se reinicia el consumidor, **Then** no se inserta ni se actualiza ninguna fila.
3. **Given** una tabla del esquema que falta, **When** arranca el consumidor, **Then** termina con un error que nombra la tabla y no consume mensajes.
4. **Given** el archivo real del catálogo, **When** se comprueba, **Then** los `ADM0_A3` son únicos (177 distintos) y el archivo no se modifica; **Given** un catálogo de prueba con un `ADM0_A3` repetido, **When** se intenta cargar, **Then** se rechaza con un error que nombra el código repetido (C10).

---

### User Story 5 - Casos sintéticos etiquetados y separados (Priority: P3)

Los casos de prueba de F5 (mag nula, lat 145, punto marítimo, tipo no-earthquake, Madrid) están marcados como sintéticos (`is_synthetic = true`) con identificadores reconocibles, y los reales conservan `false`.

**Why this priority**: C13 y constitución §7; permite capturar las pruebas 5 y 7 sin mezclar con datos reales.

**Independent Test**: Tras ejecutar los casos, `SELECT count(*) ... WHERE is_synthetic` coincide con los casos sintéticos enviados y ningún evento real queda marcado.

**Acceptance Scenarios**:

1. **Given** los casos sintéticos de esta feature, **When** se guardan o se llevan a cuarentena, **Then** llevan `is_synthetic = true` e `id` con prefijo `synthetic-`.
2. **Given** el evento sintético de tipo no-earthquake enviado al productor de pruebas, **When** el productor lo procesa, **Then** no se publica y queda una fila en `exclusion` con `observed_type` (comportamiento ya existente en `productor-live`; aquí solo se demuestra).

---

### Edge Cases

- **Puntos en la antimeridiana (lon ±180)**: el catálogo parte algunos países; se usa el punto tal cual está en [-180, 180] y se acepta el resultado del catálogo. Límite conocido.
- **Costa y pequeños territorios**: el catálogo está simplificado y no incluye todos los territorios pequeños; un evento costero puede quedar sin país. No se afirma precisión cartográfica (`FUENTES-Y-LICENCIAS.md`, FAQ 19). Límite conocido.
- **Reenvío o repetición**: asignar país es determinista; reprocesar un mensaje da el mismo `country_id` (idempotencia, constitución §1).
- **Evento válido que antes tenía país y ahora no (o a la inversa)**: se aplica la regla de versiones; solo la versión ganadora fija el país.
- **Catálogo con geometría inválida o propiedad ausente**: el consumidor no arranca y el error nombra el campo y la posición de la entidad.
- **Eventos antiguos sin país por haberse guardado antes de esta feature**: no hay recálculo retroactivo (límite conocido).

## Requirements *(mandatory)*

### Functional Requirements

**País por geometría (C9-C12)**

- **FR-001**: El consumidor MUST asignar a cada evento válido el `country_id` (`ADM0_A3`) del país cuyo polígono contiene su punto (`lon`, `lat`) en EPSG:4326, y MUST NOT usar el texto `place` (C9, constitución §4).
- **FR-002**: Un punto sobre el borde de un polígono MUST considerarse dentro de él (C11).
- **FR-003**: Si el punto está en varios polígonos, MUST elegirse el de `ADM0_A3` menor en orden alfabético y MUST registrarse una línea de log con el `event_id` y los candidatos (C11).
- **FR-004**: Si no hay ningún polígono que cubra el punto, `country_id` MUST ser `NULL`; el evento MUST guardarse, MUST NOT ir a cuarentena y MUST contarse en los totales (C12, prueba 7).
- **FR-005**: La asignación MUST ser una función pura y determinista (mismas coordenadas y mismo catálogo, mismo resultado), separada de la E/S, reutilizable por `historico-2025` y `replay` (constitución §14).
- **FR-006**: El país MUST calcularse solo para mensajes que superen la validación y MUST escribirse con el estado actual en la misma transacción que el resto de la fila; la regla de versiones (`updated` estrictamente mayor) decide si el país nuevo sustituye al anterior (constitución §2).
- **FR-007**: Los recuentos «con país» y «sin país» MUST poder obtenerse con una consulta sobre `current_event`, y su suma MUST ser igual al total de eventos actuales (constitución §8).

**Catálogo y arranque (C10, FR-025/FR-026 retomados)**

- **FR-008**: Al arrancar, el consumidor MUST comprobar que existen las tablas del esquema que necesita y, si falta alguna, terminar con un error que la nombre antes de consumir (FR-026 de `consumidor-idempotente`).
- **FR-009**: Al arrancar, el consumidor MUST cargar el catálogo `data/catalogo/paises.geojson` en `public.country` (`country_id` = `ADM0_A3`, `name_es`, `admin`, `continent`, `subregion`) sin modificar el archivo, de forma repetible: una segunda carga no inserta ni cambia filas, y una fila alterada a mano se corrige (FR-025, SC-011).
- **FR-010**: Antes de cargar, MUST comprobarse que `ADM0_A3` es único y que las propiedades usadas existen; si no, el consumidor MUST NOT arrancar y el error MUST nombrar el código o el campo y la entidad (C10).
- **FR-011**: El mismo catálogo MUST alimentar la carga de `public.country` y la asignación de país, de modo que todo `country_id` asignado exista en `public.country`.
- **FR-012**: Una línea de log por carga MUST resumir el total, las filas insertadas y las actualizadas.

**Reglas de validez (completar y demostrar, no duplicar)**

- **FR-013**: Se MUST reutilizar la validación de `common/validation.py` (ya implementada en `consumidor-idempotente`) sin duplicarla: geometría `Point`, `lon`/`lat` finitos y en rango, `time` y `updated` presentes y enteros, `mag` nula permitida, `mag` y profundidad negativas permitidas. Esta feature MUST añadir las pruebas de aceptación que faltan (mag nula, lat 145, geometría no `Point`, longitud no finita, sin `time`/`updated`) y MUST corregir cualquier hueco que descubran dentro de los motivos de cuarentena ya definidos.
- **FR-014**: Un mensaje inválido MUST ir a cuarentena con motivo y referencia al original, sin país, sin punto inventado y sin bloquear la cola (constitución §6). Esta feature MUST NOT añadir motivos nuevos a `kafka-message.md` §6.
- **FR-015**: `mag` nula MUST guardarse como `NULL` (nunca 0) y el evento MUST conservar país y presencia en el análisis (prueba 5, constitución §5).

**Sintéticos, contratos y documentación**

- **FR-016**: Los casos de prueba (Madrid, Atlántico, mag nula, lat 145, tipo no-earthquake) MUST ser sintéticos, con `is_synthetic = true` e `id` con prefijo `synthetic-`, y MUST estar separados de los datos reales (C13, constitución §7).
- **FR-017**: `kafka-message.md` y `db-schema.md` MUST NOT modificarse. La columna `country_id` y su clave foránea ya existen en el esquema.
- **FR-018**: La regla de frontera y de empates MUST documentarse en un párrafo (borrador para la memoria, C11) junto con la limitación de precisión del catálogo.
- **FR-019**: La asignación MUST NOT degradar el rendimiento del consumidor de forma apreciable: el índice espacial se construye una vez al arrancar, no por mensaje.
- **FR-020**: Al terminar, MUST existir evidencia en `docs/evidencias/geografia-pais/` (salida de pruebas y consultas SQL de las pruebas 5 y 7) y `CODEMAP.md` y `README` actualizados (constitución §16). El borrador de FR-018 va en `docs/borradores/geografia-pais.md`.

### Key Entities

- **País** (`public.country`): 177 entidades del catálogo; clave `country_id` = `ADM0_A3`; nombre en español, subregión y continente. Referenciado por `current_event.country_id` (N:1, opcional).
- **Evento actual** (`live.current_event`): ya tiene `country_id` (nulo = «Sin país asignado»). Esta feature lo rellena.
- **Catálogo geográfico**: archivo `paises.geojson` (polígonos y multipolígonos, CRS84 = lon/lat WGS84). Solo lectura.
- **Regla de asignación**: punto → país: cubre el borde; varios candidatos → `ADM0_A3` menor; ninguno → nulo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un evento sintético en Madrid queda con `country_id = 'ESP'`; reprocesarlo 100 veces no cambia ninguna tabla (0 filas nuevas, mismo país).
- **SC-002**: Un evento sintético en el Atlántico queda con `country_id` nulo, 0 filas en cuarentena, y el total de `current_event` lo incluye (prueba 7): suma «con país» + «sin país» = total.
- **SC-003**: Un evento sintético con `mag` nula queda con `mag` nulo (0 casos con valor 0) y con país asignado (prueba 5); un evento con `mag = -0.06` y profundidad `-0.18` se guarda tal cual.
- **SC-004**: Un evento sintético con latitud 145 produce exactamente 1 fila de cuarentena con motivo `coordinates_out_of_range` y referencia al mensaje, y 0 filas en `current_event` y `event_version`.
- **SC-005**: Tras arrancar sobre una base limpia, `public.country` tiene exactamente 177 filas; un segundo arranque deja 177 filas con 0 insertadas y 0 actualizadas.
- **SC-006**: La comprobación de unicidad confirma 177 `ADM0_A3` distintos en el archivo real y rechaza un catálogo de prueba con un código repetido (2 pruebas).
- **SC-007**: Con los eventos reales de un día de USGS, el 100 % se procesa sin error: cada uno acaba con un `country_id` presente en `public.country` o nulo, y la evidencia recoge cuántos quedaron sin país.
- **SC-008**: Una prueba de frontera (punto sobre el borde) y una de empate (punto en dos polígonos) producen siempre el mismo país en 10 ejecuciones consecutivas.
- **SC-009**: `kafka-message.md`, `db-schema.md` y `docs/enunciado/` no cambian (`git diff` vacío sobre esas rutas).

## Assumptions

- La validación de `consumidor-idempotente` (`common/validation.py`) ya cubre las reglas de validez del brief; esta feature las comprueba con casos de aceptación y las reutiliza.
- El catálogo `paises.geojson` es el entregado (177 entidades, `ADM0_A3` único, CRS84) y no se modifica.
- Se necesita una librería de geometría fijada en `pyproject.toml`/`uv.lock` y en la imagen (constitución §11); la elección está en "Preguntas para el alumno".
- Los eventos de prueba son sintéticos; el ejemplo real (Anza, CA) y el feed real sirven para SC-007.
- La etiqueta «Sin país asignado» y la presentación de **ND** para magnitud nula son de la API y del panel; esta feature garantiza el dato (nulo) que las hace posibles.
- Se parte de una base limpia o se aceptan filas antiguas sin país (límite conocido).

## Fuera de alcance

Histórico 2025, replay, API, frontend, recálculo retroactivo de países, nuevos contadores, nuevos motivos de cuarentena, modificación de contratos, endurecimiento de casos raros (fuzz, auditorías) y precisión cartográfica por encima de la del catálogo.

## Preguntas para el alumno

1. **Dependencia de geometría (decisión provisional: Shapely 2, sin GeoPandas).** El enunciado admite GeoPandas/Shapely y el roadmap menciona GeoPandas + `STRtree`. Shapely 2 incluye `STRtree` y `covers`, y evita arrastrar pandas y sus ruedas a la imagen del consumidor. Recomendación: solo Shapely. Afecta a `pyproject.toml`, `uv.lock` y al tamaño de la imagen. Decídelo antes de `plan`.
2. **Evento de tipo no-earthquake que llegue al consumidor (decisión provisional: no se añade motivo ni regla).** `kafka-message.md` §3 dice que el productor no los publica y §6 no define motivo de cuarentena para ello. El brief lo incluye como caso sintético; se propone demostrarlo en el productor (`exclusion`). Si prefieres que el consumidor también lo rechace, hay que ampliar `kafka-message.md` §6 (cambio de contrato, tu aprobación). Recomendación: no tocar el contrato.
3. **Carga del catálogo en el consumidor (decisión provisional: sí, al arrancar).** `db-schema.md` §1.1 ya lo fija así; se mantiene. Si prefieres un script aparte, cambiaría el contrato. Recomendación: mantenerlo en el consumidor.
