# Feature Specification: Replay — reproducción acelerada de una selección histórica de 2025

**Feature Branch**: `009-replay` (en `docs/planificacion/03-procedimiento-ejecucion.md` §4 figura como `013-replay`; se usa el nombre `replay`, el número es orientativo)

**Created**: 2026-11-12

**Status**: Planned (specify, clarify, plan, tasks y analyze hechos; implementación no iniciada; pendiente la revisión del alumno)

**Input**: Feature `replay` (F9): reproducción acelerada de una selección histórica de 2025 por Kafka, aislada de `live` y etiquetada «REPRODUCCIÓN». Un productor de replay lee de `data/historical/` unos 20 eventos de una zona, ordenados por fecha, y los publica en `earthquakes.replay` con `mode = "replay"`, el tiempo original y `replay_at`, a velocidad configurable. Incluye duplicados y revisiones controlados (secuencia de la FAQ 12). El consumidor enruta por `mode` al esquema `replay` reutilizando `common/`. La API devuelve los datos de replay con `metadata.mode = "replay"`; el panel los muestra con el banner.

> Contratos de referencia, **sin modificar**: `specs/001-contratos-y-modelo/contracts/kafka-message.md` (topics §1, mensaje §3, versiones §5, cuarentena §6), `db-schema.md` (esquema `replay`) y `api.md` (§3 `mode`, `metadata.mode`; §5 `comparison: null` en replay). Esta spec no repite sus tablas: las cita.

## Cobertura de requisitos

| ID | Qué cubre `replay` | Dónde se comprueba |
|---|---|---|
| J1 | Reproducción acelerada de una selección histórica ordenada por fecha | US1, FR-001 a FR-004, SC-001 |
| J2 | Se conserva el tiempo original y se añade `replay_at` | FR-005, SC-004 |
| J3 | Topic y esquema separados de `live` | FR-007, FR-008, SC-002 |
| J4 | Etiqueta «REPRODUCCIÓN» (datos y panel) | FR-011, FR-016, SC-005 |
| J5 | El replay reutiliza el procesamiento del consumidor (`common/`) | FR-009, FR-010 |
| J6 | Duplicados y revisiones controlados (secuencia de la FAQ 12) | US2, FR-012 a FR-014, SC-001 |
| J7 | Fechas originales intactas; la vista de replay consulta el intervalo de 2025 | FR-005, FR-015, SC-003 |
| J8 | Documentar selección, cómo iniciar, velocidad, aislamiento, cómo se ve el modo y resultado observado | US4, FR-019, SC-007 |
| G10 | Modo «REPRODUCCIÓN» claramente etiquetado en el panel (el banner ya existe en `008-panel-base-mock`; aquí se cierra con datos reproducidos reales) | US3, FR-016, SC-005 |
| F12 | La API sirve los datos aislados de replay con `metadata.mode = "replay"` | US3, FR-015, SC-003 |
| G12 (parte `metadata.mode`) | El panel condiciona la vista a `metadata.mode` | FR-016, SC-005 |
| Prueba 11 | «Va por Kafka, aislada de live, etiquetada, con duplicados y revisiones controlados» (demo + SQL) | SC-001 a SC-006 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducir una selección histórica por Kafka, aislada de live (Priority: P1)

Quien hace la demostración lanza un único comando y, en unos segundos, el panel dispone de actividad sísmica real de 2025 sin esperar a que ocurra un terremoto. La selección son unos 20 eventos de una zona, ordenados por su fecha original, publicados uno tras otro a un ritmo configurable (p. ej. un evento cada 2 s) en el topic de replay. Los datos acaban en las tablas de replay y no tocan nada de `live`.

**Why this priority**: es el núcleo de J1–J3 y de la prueba 11. Sin esto no hay replay.

**Independent Test**: con el stack levantado y el esquema `replay` vacío, ejecutar el replay completo y consultar SQL: los recuentos de `replay` salen los esperados y los de `live` no cambian (con el productor live parado durante la comprobación).

**Acceptance Scenarios**:

1. **Given** el stack levantado, el esquema `replay` vacío y los archivos de `data/historical/` íntegros, **When** se lanza el replay con la selección por defecto, **Then** se publican los eventos de la selección en `earthquakes.replay` ordenados por `time` ascendente, a un ritmo medible de un mensaje cada intervalo configurado.
2. **Given** el replay en curso, **When** el consumidor procesa un mensaje, **Then** el evento queda en `replay.current_event` y `replay.event_version` con su `time` original y su `replay_at` no nulo, y no se escribe nada en `live`.
3. **Given** los recuentos de `live.current_event`, `live.event_version` y `live.quarantine` antes del replay (con el productor live parado), **When** termina el replay y el consumidor procesa todo, **Then** esos recuentos y la huella de las tablas `live` son idénticos.
4. **Given** un mensaje en `earthquakes.replay` con `mode = "live"` (caso de contrato ya cubierto por el consumidor), **When** se consume, **Then** va a `replay.quarantine` con `mode_topic_mismatch` y no a una tabla de eventos.

---

### User Story 2 - Duplicados y revisiones controlados (Priority: P1)

El replay incluye, dentro del flujo, la secuencia de la FAQ 12 sobre eventos fabricados y etiquetados como sintéticos: reenvío de la misma versión, versión posterior, y versión antigua tardía. Así se demuestra por Kafka real, en el esquema `replay`, que el procesamiento es idempotente y respeta `updated`.

**Why this priority**: J6 es obligatorio y es lo que distingue una demo de un volcado. Se verifica con recuentos exactos.

**Independent Test**: tras el replay, SQL sobre `replay.*` da los recuentos de SC-001 y el evento revisado conserva la versión con `updated` mayor.

**Acceptance Scenarios**:

1. **Given** el bloque controlado (6 mensajes sobre dos eventos sintéticos E1 y E2: E1 v1, E1 v1 repetido, E1 v2 con `updated` mayor, E1 v1 repetido tarde, E2, E1 versión intermedia con `updated` entre v1 y v2 y no vista antes), **When** se reproduce, **Then** hay 2 filas actuales (E1 con la versión de `updated` mayor, E2), 4 versiones en el historial (3 de E1 y 1 de E2) y 2 reenvíos ignorados, sin cuarentena.
2. **Given** los eventos del bloque controlado, **When** se consultan en SQL y en la API, **Then** tienen `is_synthetic = true`, ids con prefijo `synthetic-replay-` y ningún evento real queda marcado como sintético ni al revés.
3. **Given** un replay ya ejecutado, **When** se repite sin vaciar el esquema, **Then** los recuentos son los mismos (todo son reenvíos) y `replay_at` de las filas existentes no cambia.

---

### User Story 3 - Ver el replay en la API y en el panel, etiquetado (Priority: P1)

Quien mira el panel en modo «Reproducción» ve los eventos reproducidos de 2025 con sus fechas originales y el banner «REPRODUCCIÓN»; en modo en vivo no ve ni rastro de ellos.

**Why this priority**: G10, F12 y J7 son obligatorios o de contrato; sin esto el replay no se «ve».

**Independent Test**: con el replay terminado, `GET /api/eventos?mode=replay&start=2025-01-01&end=2026-01-01` devuelve los eventos reproducidos con `metadata.mode = "replay"`; el panel con `config.mode = "api"` en modo Reproducción muestra el banner y los puntos.

**Acceptance Scenarios**:

1. **Given** el replay terminado, **When** se pide a la API `mode=replay` con el intervalo de 2025, **Then** `metadata.mode = "replay"`, `total` es el número de filas de `replay.current_event`, `properties.time` de cada evento real coincide con el `time` del archivo del histórico y `is_synthetic` refleja el origen.
2. **Given** el replay terminado, **When** se pide a la API sin `mode` o con `mode=live`, **Then** no aparece ningún evento reproducido y `metadata.mode = "live"`.
3. **Given** `mode=replay`, **When** se pide `/api/estadisticas`, **Then** `comparison` es `null` (api.md §5.1) y `by_hour`, `by_country` e histogramas se calculan sobre los eventos de replay.
4. **Given** el panel conectado a la API real, **When** el usuario elige «Reproducción», **Then** se pide el intervalo de 2025, se muestra el banner «REPRODUCCIÓN» con los eventos reproducidos y, al volver a «En vivo», el banner desaparece.
5. **Given** el esquema `replay` vacío, **When** el panel pide `mode=replay`, **Then** muestra el estado vacío, no un error.

---

### User Story 4 - Documentar y dejar evidencia de la prueba 11 (Priority: P2)

Cualquiera puede repetir la demo leyendo el README y la evidencia: qué selección, cómo iniciar, a qué velocidad, cómo se aísla, cómo se ve el modo y qué resultado se observó.

**Why this priority**: J8 y el cierre de la feature (constitución §16), pero depende de que lo anterior funcione.

**Independent Test**: seguir el README desde un stack limpio reproduce los recuentos de SC-001.

**Acceptance Scenarios**:

1. **Given** el README, **When** se siguen sus pasos, **Then** se obtienen los mismos recuentos y se ve el banner.
2. **Given** la carpeta de evidencias, **When** se revisa, **Then** contiene la salida del replay, el SQL antes/después de `live` y `replay`, la respuesta de la API y la captura del panel.

---

### Edge Cases

- Falta un archivo de `data/historical/` o su `sha256` no coincide con el manifiesto: el replay se detiene antes de publicar nada, con un mensaje que nombra el archivo.
- La selección tiene menos eventos de los pedidos: se reproducen los que hay y se informa del número real; si no hay ninguno, error claro y sin publicar.
- Kafka no está disponible al lanzar el replay: se reintenta con la misma política que el productor live (A4); no se pierde ni se duplica nada porque el consumidor es idempotente.
- Se interrumpe el replay a medias: lo ya publicado queda; relanzarlo reenvía todo y los reenvíos se ignoran (US2.3).
- Magnitud o profundidad nula/negativa en la selección: se conservan tal cual (constitución §5); el histórico de 2025 es M ≥ 4, así que se espera que no ocurra y no se trata aparte.
- Un mensaje de replay inválido (p. ej. sin `replay_at`) va a `replay.quarantine` con su motivo; el replay propio nunca lo genera.
- El panel en «Reproducción» sin datos de replay: estado vacío (ya implementado en `008`).

### Límites conocidos (una línea cada uno)

- No hay borrado de las tablas de replay (ningún rol tiene `DELETE`); repetir «desde cero» exige recrear el volumen de PostgreSQL.
- La velocidad es un intervalo fijo entre mensajes, no una compresión proporcional del tiempo original.
- El replay no reproduce la ingesta real de USGS: usa los archivos descargados en `historico-2025`.
- Con el replay y el productor live activos a la vez, `live` sigue cambiando por la actividad real de USGS; la comprobación «live no cambia» exige parar el productor live.

## Requirements *(mandatory)*

### Functional Requirements

**Selección y publicación (J1, J2, J3)**

- **FR-001**: El replay MUST leer sus eventos de los archivos de `data/historical/`, verificando antes el `sha256` de cada archivo usado contra `manifest.json`.
- **FR-002**: La selección MUST ser un subconjunto de unos 20 eventos de una sola zona geográfica, configurable (zona y número), con un valor por defecto documentado. Los ids de la selección MUST ser únicos.
- **FR-003**: Los eventos de la selección MUST publicarse ordenados por `event.properties.time` ascendente (J1).
- **FR-004**: El replay MUST publicar con un intervalo configurable entre mensajes (por defecto 2 s) y confirmar cada envío al broker antes de pasar al siguiente.
- **FR-005**: Cada mensaje MUST cumplir el contrato `kafka-message.md` §3: `mode = "replay"`, `source = "replay_demo"`, `replay_at` = instante UTC de publicación (no nulo), `is_synthetic` según el origen del evento, y `event` tal como está en el archivo, sin cambiar `time`, `updated` ni ninguna fecha (J2, J7). La clave es `event.id`.
- **FR-006**: `ingested_at` MUST ser la fecha de extracción del archivo según el manifiesto (eventos reales) y el instante de arranque del replay (eventos sintéticos).
- **FR-007**: El replay MUST publicar solo en `earthquakes.replay`; nunca en `earthquakes.live` (J3).

**Consumo y aislamiento (J3, J5)**

- **FR-008**: El consumidor MUST procesar los mensajes de `earthquakes.replay` y escribirlos solo en el esquema `replay`; los de `earthquakes.live` siguen yendo solo a `live`. El modo sale del topic de origen y se comprueba contra el campo `mode` (kafka-message.md §1). Procesar replay MUST NOT alterar el comportamiento live (offsets, orden, idempotencia).
- **FR-009**: El replay MUST reutilizar el procesamiento existente de `common/` (decodificar, validar, versión, transformar y país por geometría) y el escritor del consumidor; no se duplica lógica de validación ni de versiones.
- **FR-010**: La lógica pura del replay (selección, orden, armado del mensaje, bloque controlado) MUST estar separada del I/O (Kafka, ficheros) y ser comprobable sin Docker (constitución §14).
- **FR-011**: Los eventos de replay MUST quedar identificables como tales en los datos: viven en el esquema `replay`, con `replay_at` no nulo y `source = replay_demo`.

**Duplicados y revisiones (J6)**

- **FR-012**: Tras los eventos de la selección, el replay MUST publicar el bloque controlado de la FAQ 12 sobre dos eventos fabricados `synthetic-replay-e1` y `synthetic-replay-e2` con `is_synthetic = true` (constitución §7), en este orden: E1 v1, E1 v1 repetido, E1 v2 (`updated` mayor), E1 v1 repetido tarde, E2, E1 versión intermedia (`updated` entre v1 y v2, no vista antes).
- **FR-013**: El `time` de los eventos sintéticos MUST caer dentro del intervalo de 2025 de la selección (no se alteran fechas reales; los sintéticos son eventos propios).
- **FR-014**: Las reglas de versión MUST dar el resultado de `kafka-message.md` §5 en cada caso: reenvío = sin cambio; versión posterior = sustituye el estado actual; versión antigua tardía = se conserva en el historial sin pisar la actual.

**API y panel (F12, G10, G12, J4, J7)**

- **FR-015**: `/api/eventos` y `/api/estadisticas` con `mode=replay` MUST devolver los datos de `replay.*` con `metadata.mode = "replay"`, `last_ingestion` del modo live y, en estadísticas, `comparison = null`. Sin `mode` o con `live`, los datos de replay MUST NOT aparecer. No se cambia el contrato; si algo no encaja con el contrato, se escala.
- **FR-016**: El panel en modo «Reproducción» MUST pedir el intervalo de 2025 y mostrar el banner «REPRODUCCIÓN» cuando `metadata.mode = "replay"`; el banner MUST NOT aparecer en modo en vivo. El frontend no calcula estadísticas (constitución §17). Se ajusta el panel solo si la verificación de extremo a extremo lo exige.

**Configuración, robustez y documentación**

- **FR-017**: Toda configuración nueva (intervalo, zona, número de eventos, temas que lee el consumidor) MUST ir a variables o argumentos con valores por defecto, estar en `.env.example` si es variable de entorno (constitución §10) y no contener secretos. Entre contenedores se usan nombres de servicio (constitución §9).
- **FR-018**: El replay MUST reintentar la conexión a Kafka como el productor live y terminar con código distinto de cero y un mensaje claro si falta o está alterado un archivo del histórico (edge cases).
- **FR-019**: MUST documentarse en el README y en `docs/borradores/replay.md`: selección, cómo iniciar, velocidad, aislamiento (topic + esquema + comprobación `mode` ↔ topic), cómo se ve el modo y el resultado observado (J8), más la evidencia de la prueba 11 en `docs/evidencias/replay/`.
- **FR-020**: Al cerrar la feature MUST actualizarse `CODEMAP.md` y el README (constitución §16). La feature MUST NOT añadir servicios nuevos a Compose ni tocar los contratos de `specs/001-contratos-y-modelo/`, `sql/001_schema.sql` ni `docs/enunciado/`.

### Key Entities

- **Selección de replay**: lista ordenada de eventos reales de 2025 de una zona (id, `time` original, `updated`), obtenida de `data/historical/`.
- **Bloque controlado**: seis mensajes sobre dos eventos sintéticos que reproducen la secuencia de la FAQ 12.
- **Mensaje de replay**: sobre del contrato con `mode = replay`, `replay_at` y el evento original.
- **Evento de replay**: fila de `replay.current_event` con su historial en `replay.event_version`; mismo modelo que `live`, otro esquema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

Sea `N` el número de eventos reales de la selección (unos 20; el valor real se fija en el plan). Con esquema `replay` vacío y un solo replay:

- **SC-001**: Se publican `N + 6` mensajes; `replay.current_event` tiene `N + 2` filas, `replay.event_version` tiene `N + 4` filas, `replay.quarantine` tiene 0 y el consumidor registra 2 reenvíos ignorados, 1 versión posterior y 1 versión antigua tardía. E1 conserva la versión de `updated` mayor.
- **SC-002**: Con el productor live parado, los recuentos de `live.current_event`, `live.event_version` y `live.quarantine` y la huella de las tablas `live` son idénticos antes y después del replay. Ningún mensaje de replay aparece en `live.*`.
- **SC-003**: `GET /api/eventos?mode=replay&start=2025-01-01&end=2026-01-01` devuelve `metadata.mode = "replay"` y `total = N + 2`; el `time` de los `N` eventos reales coincide al 100 % con el de los archivos de origen; con `mode=live` se devuelven 0 eventos de replay.
- **SC-004**: El 100 % de las filas de `replay.current_event` tiene `replay_at` no nulo y `source = replay_demo`; el 100 % de las de `live.current_event` tiene `replay_at` nulo. Los `N` eventos reales salen en orden de `time` ascendente en el orden de publicación (verificable por `replay_at` crecientes).
- **SC-005**: En el panel conectado a la API real, «Reproducción» muestra el banner «REPRODUCCIÓN» y los `N + 2` eventos; «En vivo» no muestra banner ni eventos de replay (captura o comprobación manual registrada en evidencias).
- **SC-006**: Repetir el replay sin vaciar el esquema deja los mismos recuentos de SC-001 (idempotencia).
- **SC-007**: Un lector que siga el README desde un stack limpio obtiene los recuentos de SC-001 sin consultar otra fuente; el replay completo con el intervalo por defecto dura menos de 90 s en total.

## Assumptions

- El histórico 2025 ya está descargado y verificado en `data/historical/` (`historico-2025`) y el consumidor ya escribe en `replay` con las mismas reglas que en `live` (feature `consumidor-idempotente`, FR-032).
- La API ya acepta `mode=replay` y el panel ya trae el banner y la petición del intervalo de 2025 (`007-api`, `008-panel-base-mock`); esta feature los verifica con datos reales.
- El replay usa el rol y la configuración del servicio `producer` de Compose, lanzado con `docker compose run --rm`, sin servicio nuevo.
- La zona por defecto la elige el plan inspeccionando los archivos reales (zona con al menos 20 eventos M ≥ 4 en 2025).
- Los datos reales reproducidos son reales (`is_synthetic = false`) y se etiquetan como replay por el esquema, el modo y `replay_at`; solo el bloque controlado es sintético.
- Fuera de alcance: despliegue, túnel, mediciones, panel de calidad, nuevos endpoints, cambios de contrato y de esquema SQL.

## Clarifications

### Session 2026-11-12

- Q: ¿Cómo se fabrican los duplicados y revisiones controlados? → A: Con dos eventos propios `synthetic-replay-e1/e2` etiquetados `is_synthetic = true` (opción recomendada, constitución §7). Forzar dos versiones reales marcaría como sintético un evento real al sustituirse la fila actual.
- Q: ¿Qué significa «velocidad configurable»? → A: Intervalo fijo en segundos entre mensajes, por defecto 2 s, configurable; no es una compresión proporcional del tiempo original.
- Q: ¿Qué valores llevan `source`, `ingested_at` y `replay_at`? → A: `source = replay_demo` (el contrato lo define para «evento reproducido o fabricado»); `ingested_at` = fecha de extracción del archivo (reales) o arranque del replay (sintéticos); `replay_at` = instante UTC de publicación de cada mensaje.
- Q: ¿Cómo se comprueba que `live` no cambia si el productor live sigue consultando USGS? → A: Se para el productor live durante la comprobación y se comparan recuentos y huella de las tablas `live` antes y después.
- Q: ¿Qué pasa si se repite el replay? → A: Es idempotente: todo son reenvíos y los recuentos no cambian. No se añade borrado de tablas de replay; repetir desde cero se hace recreando el volumen de PostgreSQL.

### Preguntas para el alumno

Decisiones provisionales; el alumno las confirma o cambia antes de pasar a plan.

1. **¿Cómo lee el consumidor el topic de replay?** Hoy el consumidor se suscribe a un solo topic (`KAFKA_TOPIC`). Esto toca la configuración de `002-infra-compose` (`config.md`, `.env.example`, `compose.yaml`) y el código del consumidor.
   - Decisión provisional: un único consumidor suscrito a los dos topics del contrato; el esquema ya sale del topic de cada mensaje (`topic_mode`).
   - Recomendación: la provisional. Alternativa sin tocar código del consumidor: una segunda instancia lanzada con `docker compose run` y `KAFKA_TOPIC=earthquakes.replay` con otro `KAFKA_GROUP_ID`; es más frágil de operar en la demo.
2. **¿Se toca `compose.yaml` para montar `data/historical/` en el contenedor del productor?** La imagen no incluye los datos. Decisión provisional: volumen de solo lectura en el servicio `producer`, sin servicios nuevos. Recomendación: la provisional (alternativa: `-v` en cada `docker compose run`, peor para el README).
3. **Nombre del parámetro de velocidad.** `03-procedimiento-ejecucion.md` §8.5 muestra `python -m producer.replay --speed 2`; aquí se define como segundos entre mensajes. Decisión provisional: `--interval` (segundos, por defecto 2), y el alumno actualiza el ejemplo de §8.5 (esta feature no edita `docs/planificacion/`). Recomendación: la provisional, para que `2` no se lea como «el doble de rápido».
4. **Zona y número de eventos por defecto.** Decisión provisional: la propone el plan tras inspeccionar `data/historical/` (≥ 20 eventos M ≥ 4 en una zona con país reconocible). Recomendación: validar la zona en la revisión del plan.
5. **¿Se ajusta el panel?** Con `fadeByAge` activo, los puntos de 2025 se dibujan con la opacidad mínima (0,25) porque su antigüedad supera la ventana. Decisión provisional: no tocar el panel salvo que la comprobación visual muestre los puntos ilegibles; en ese caso, desactivar el atenuado por antigüedad solo en modo replay. Recomendación: la provisional.
