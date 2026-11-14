# Feature Specification: Pruebas de aceptación

**Feature Branch**: `012-pruebas-aceptacion` (en `docs/planificacion/03-procedimiento-ejecucion.md` figura con otro número; el número es orientativo)

**Created**: 2026-11-14

**Status**: Draft (fase A: specify + clarify; fase B: plan, tasks y analyze hechos con las decisiones provisionales; falta la revisión del alumno antes de implementar)

**Input**: Formalizar las 11 pruebas de aceptación del enunciado: cada una con procedimiento repetible, resultado esperado, resultado observado, evidencia y cómo repetirla. Reutilizar las evidencias y las pruebas que ya existen; añadir solo lo que falte.

> Contratos de referencia, **sin modificar**: `specs/001-contratos-y-modelo/contracts/db-schema.md` (versionado por `updated`, cuarentena, nulos), `kafka-message.md` (`mode`, `is_synthetic`) y `api.md` (`/api/eventos`, `/api/estadisticas`, `/api/salud`, `metadata.mode`). Esta spec los cita, no los repite. `docs/enunciado/`, `sql/001_schema.sql`, la constitución y el checklist no se tocan (el checklist lo marca el alumno).

## Cobertura de requisitos

| ID | Qué cubre `pruebas-aceptacion` | Dónde se comprueba |
|---|---|---|
| Tabla I, pruebas 1 a 11 | Cada prueba tiene ficha propia con procedimiento, esperado, observado, evidencia y cómo repetirla | US1 a US4, FR-001 a FR-010, SC-001 |
| I-resumen (fila 8 de entregables) | Un resumen único de las 11 pruebas con enlace a su evidencia | FR-011, SC-002 |
| G9 (pruebas 9 y 10) | El panel muestra el fallo y conserva la última lectura; se recupera solo. Revisión del código y plantilla de evidencia del alumno | US3, FR-007 a FR-009, SC-004 |
| M-evidencias | Evidencias guardadas, enlazadas y con la forma de repetirlas | FR-010, FR-011, SC-002, SC-006 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pruebas de datos 1 a 8 repetibles sin tocar los datos reales (Priority: P1)

El alumno (o un revisor) puede repetir las pruebas 1 a 8 con un comando y ver el resultado esperado y el observado, sin que ningún dato inyectado llegue a `live`.

**Why this priority**: son obligatorias y la mayoría ya está probada de forma dispersa en las features 003, 004, 005; falta reunirlas con un procedimiento común.

**Independent Test**: ejecutar el procedimiento de una prueba (por ejemplo la 4) desde un clon con el stack levantado y obtener la misma conclusión que la ficha, con 0 filas sintéticas nuevas en `live`.

**Acceptance Scenarios**:

1. **Given** un evento nuevo (prueba 1), **Then** hay exactamente 1 fila actual para su `event_id` y es visible en `/api/eventos`, en `/api/estadisticas` (recuento) y en el panel (mapa y análisis). La parte real reutiliza `docs/evidencias/productor-live/prueba1_evento_nuevo.out`; la parte API se repite con un evento sintético en base temporal.
2. **Given** la misma versión reenviada (prueba 2), **Then** el recuento de `current_event` y de `event_version` no cambia (SQL antes y después).
3. **Given** una versión con `updated` posterior (prueba 3), **Then** cambian los datos actuales y las agregaciones afectadas (recuento por país o por hora) y se conserva la versión anterior en el historial.
4. **Given** una versión con `updated` menor llegada tarde (prueba 4), **Then** la fila actual no cambia y la versión tardía queda en el historial.
5. **Given** una magnitud nula (prueba 5), **Then** se conserva como NULL (no 0), la API la devuelve como `null` y el panel la muestra como **ND**. No hay nulos en los datos reales: el caso es sintético, etiquetado (`is_synthetic = true`, `id` `synthetic-…`) y aislado.
6. **Given** coordenadas inválidas (prueba 6), **Then** el mensaje va a cuarentena con el motivo y una referencia al original, no hay fila en `current_event` y ningún punto inventado.
7. **Given** un evento en el mar (prueba 7), **Then** `country_id` es NULL, la API y el panel lo muestran como «Sin país asignado» y el evento sigue contado en el análisis (totales y por hora).
8. **Given** un consumidor detenido y reiniciado (prueba 8), **Then** reanuda desde el último offset confirmado y la base resultante es idéntica a la de una ejecución sin corte (sin duplicar efectos); logs y SQL guardados.

---

### User Story 2 - Reproducción histórica (prueba 11) (Priority: P1)

Se formaliza la reproducción como prueba de aceptación reutilizando la evidencia de `replay`.

**Why this priority**: obligatoria (J1 a J8) y ya demostrada; solo falta la ficha común.

**Independent Test**: repetir la secuencia de replay y obtener 26 mensajes → 22 eventos actuales, 24 versiones y 0 cuarentena en `replay`, con `live` idéntico antes y después.

**Acceptance Scenarios**:

1. **Given** el replay de la selección de 2025, **Then** los mensajes van por el topic de replay, se escriben solo en el esquema `replay`, el recuento y la huella de `live` no cambian, y los duplicados y revisiones controlados dan 22 / 24 / 0.
2. **Given** la API con `mode=replay` y el panel, **Then** aparecen etiquetados como «REPRODUCCIÓN» con el tiempo original y `replay_at`.

---

### User Story 3 - Pruebas 9 y 10: cerrar y reabrir el túnel (Priority: P1)

Se entrega el procedimiento paso a paso y la plantilla de evidencia, y se comprueba en el código del panel que ambos comportamientos existen. La ejecución la hace el alumno.

**Why this priority**: obligatorias (G9); solo se pueden demostrar apagando y encendiendo el túnel real con el panel público abierto, lo que no puede hacer el agente.

**Independent Test**: seguir la ficha con el panel abierto, cerrar el túnel, ver el aviso con la hora de la última lectura, reabrirlo y ver la recuperación sin recargar; rellenar los huecos de la plantilla.

**Acceptance Scenarios**:

1. **Given** el panel con datos y el túnel cerrado, **Then** en el siguiente refresco aparece un aviso de fallo con la hora de la última lectura correcta, y los datos anteriores siguen visibles (el panel no queda en blanco ni muestra «0 eventos»).
2. **Given** el túnel reabierto, **Then** en el siguiente refresco el aviso desaparece y los datos se actualizan sin recargar la página.
3. **Given** el código del panel, **Then** la ficha cita el archivo y la línea que implementa cada comportamiento y lista los huecos encontrados (sin corregir código en esta feature).
4. **Given** la plantilla, **Then** tiene huecos para dos capturas (o un clip) con la URL pública, la hora del cierre, la hora del aviso, la hora de la reapertura y la hora de la recuperación; hasta que el alumno los rellene, las pruebas figuran como «pendiente de la demostración del alumno», nunca como verificadas.

---

### User Story 4 - Resumen y corrección de afirmaciones (Priority: P2)

Un único `README.md` resume las 11 pruebas y la documentación de `despliegue-tunel` deja de afirmar que 9 y 10 están verificadas en vivo.

**Independent Test**: abrir `docs/evidencias/pruebas/README.md` y comprobar 11 filas con esperado, observado, evidencia y cómo repetir, y que `grep` de «verifica en vivo» en `docs/evidencias/despliegue-tunel/` no afirma nada sobre 9 y 10.

**Acceptance Scenarios**:

1. **Given** el resumen, **Then** cada fila enlaza una evidencia que existe en el repositorio y marca el estado: «Observada», «Observada (sintética)» o «Pendiente del alumno».
2. **Given** `docs/evidencias/despliegue-tunel/README.md` y las plantillas de las pruebas 9 y 10, **Then** el texto dice que quedan pendientes de la demostración del alumno.

---

### Edge Cases

- **Capturas del panel sin cuentas**: las de 1, 5 y 7 se toman con una herramienta de navegador sobre la URL pública; si no es posible, se entrega una plantilla con huecos.
- **Prueba 5 en el panel público**: los datos reales no tienen magnitud nula, así que el panel público no puede mostrar ND con datos reales; la captura de ND sale del modo mock (sintético, etiquetado) o queda como plantilla. Nunca se inyecta un nulo en la base real.
- **Prueba 1 real**: depende de que USGS publique un evento nuevo en la ventana de observación; si no llega, se usa la evidencia ya guardada y la repetición con evento sintético en base temporal.
- **Suite de integración y evidencias versionadas**: ejecutar la suite de `consumidor-idempotente` reescribe archivos de `docs/evidencias/consumidor-idempotente/`; se restauran con `git checkout` al terminar.
- **`compose.override.yaml` del alumno** publica PostgreSQL en 5433; no afecta a estas pruebas (ver `despliegue-tunel` Hallazgos).
- **Pestaña en segundo plano**: el refresco del panel puede detenerse con la pestaña oculta; la ficha de 9 y 10 pide mantenerla visible.

### Límites conocidos (una línea cada uno)

- Es un trabajo de clase: se formalizan las 11 pruebas del enunciado, sin más casos ni pruebas de carga.
- Las pruebas 9 y 10 no las ejecuta el agente; su estado final depende de las capturas del alumno.
- Las pruebas 5 y 7 con datos sintéticos demuestran el comportamiento, no que haya nulos en USGS real.

## Requirements *(mandatory)*

### Functional Requirements

**Fichas y evidencias**

- **FR-001**: Cada una de las 11 pruebas tiene un archivo `docs/evidencias/pruebas/NN-<nombre>.md` con: objetivo y requisito, precondiciones, procedimiento numerado, resultado esperado, resultado observado, evidencia (enlaces) y cómo repetirla (comando exacto).
- **FR-002**: Las fichas reutilizan las evidencias y las pruebas automáticas existentes (`consumidor-idempotente`, `productor-live`, `geografia-pais`, `replay`, `despliegue-tunel`); solo se añade una prueba o una evidencia donde falte.
- **FR-003**: Cada ficha declara su estado: Observada, Observada (sintética) o Pendiente del alumno; el observado solo recoge lo realmente ejecutado y con fecha.

**Automatización y aislamiento (pruebas 1 a 8 y 11)**

- **FR-004**: Las pruebas 1 a 8 y 11 se automatizan con `pytest` o scripts existentes; las que falten (por ejemplo, la visibilidad en API de la prueba 1 y la vista ND y «Sin país asignado» en la API) se añaden en `tests/integration/` reutilizando `tests/support/`.
- **FR-005**: Todo dato inyectado es sintético (`is_synthetic = true`, `id` `synthetic-…`) y se aísla en una base o esquema temporal, o en el esquema `replay`, o en una transacción revertida. Nunca se escribe en `live` real (constitución §7).
- **FR-006**: Al final de la ejecución se comprueba con SQL que `live` no contiene filas sintéticas nuevas y, si se usó replay, que el recuento y la huella de `live` coinciden con los iniciales (no se compara el total bruto mientras el productor sigue ingiriendo).

**Pruebas 9 y 10**

- **FR-007**: La ficha de la prueba 9 y la de la 10 dan el procedimiento paso a paso (apagar y encender `cloudflared` con el panel público abierto), qué debe verse y la hora a anotar en cada paso.
- **FR-008**: Se revisa el código del panel y se documenta, con archivo y línea, que (a) tras un fallo del refresco se muestra un aviso con la hora de la última lectura correcta y se conservan los datos anteriores, y (b) el refresco siguiente recupera el estado normal sin recargar. Los huecos o límites se reportan, no se corrigen aquí.
- **FR-009**: Cada ficha incluye una plantilla de evidencia con huecos para dos capturas (o un clip), con URL pública y horas, y el estado «pendiente de la demostración del alumno».

**Capturas, resumen y cierre**

- **FR-010**: Las capturas del panel de las pruebas 1, 5 y 7 se toman con una herramienta de navegador sobre la URL pública (sin cuentas) o, si no es posible, se dejan como plantilla con huecos; cada captura indica fecha, URL y si los datos son reales o sintéticos. La prueba 3 (versión posterior) también tiene captura, pero sus datos son sintéticos (TempDatabase) y no se inyectan en la base real: solo se toma si el panel puede mostrar esos datos sin tocar producción; si no, es plantilla con huecos que lo declara explícitamente, y la evidencia principal es el SQL.
- **FR-011**: `docs/evidencias/pruebas/README.md` resume las 11 pruebas en una tabla con esperado, observado, evidencia, cómo repetir y estado.
- **FR-012**: Se corrige `docs/evidencias/despliegue-tunel/README.md` (y las plantillas `prueba-09_cierre-tunel.md` y `prueba-10_reapertura-tunel.md` si repiten la afirmación): las pruebas 9 y 10 están pendientes de la demostración del alumno, no «verificadas en vivo».
- **FR-013**: La feature no modifica contratos, `sql/001_schema.sql`, `docs/enunciado/`, la constitución ni el checklist; no cambia el código de aplicación ni añade servicios; no hace commit, merge ni push.
- **FR-014**: Cierre (constitución §16): pruebas ejecutadas, evidencias guardadas y `CODEMAP.md` actualizado con los archivos nuevos de código (tests). Si se ejecuta la suite de integración, se restaura `docs/evidencias/consumidor-idempotente/` con `git checkout`.

### Key Entities

- **Prueba de aceptación**: una de las 11 del enunciado, con procedimiento, esperado, observado, evidencia y estado.
- **Evidencia**: salida de SQL o de `pytest`, log, captura o clip, con fecha y origen (real o sintético).
- **Caso sintético controlado**: evento etiquetado y aislado que reproduce un caso que los datos reales no ofrecen (magnitud nula) o no se pueden provocar a voluntad (versión tardía).
- **Plantilla del alumno**: ficha con huecos para capturas y horas de las pruebas 9 y 10.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Existen 11 fichas, una por prueba, y cada una tiene sus 6 apartados (procedimiento, esperado, observado, evidencia, cómo repetir, estado) sin apartados vacíos, salvo los huecos explícitos de 9 y 10.
- **SC-002**: `docs/evidencias/pruebas/README.md` tiene 11 filas y el 100 % de los enlaces de evidencia apuntan a archivos existentes.
- **SC-003**: Las pruebas 1 a 8 y 11 pasan con un comando cada una en una repetición desde el stack levantado, con 0 filas sintéticas nuevas en `live` y 0 diferencias en la huella de `live` en la prueba 11.
- **SC-004**: Las pruebas 9 y 10 tienen procedimiento, plantilla y revisión del código con 2 comportamientos comprobados (aviso con última lectura; recuperación en el siguiente refresco) y 0 afirmaciones de «verificada» sin captura del alumno.
- **SC-005**: Las capturas de 1, 5 y 7 existen con fecha, URL y tipo de dato, o su plantilla con huecos, y las de datos sintéticos llevan la etiqueta correspondiente.
- **SC-006**: Tests ejecutados y guardados en `docs/evidencias/pruebas/`, `CODEMAP.md` actualizado, `docs/evidencias/consumidor-idempotente/` restaurado y 0 cambios en contratos, `docs/enunciado/` y checklist.

## Assumptions

- Las features 003 a 010 están cerradas y su evidencia existe; esta feature las reúne y solo añade lo que falte.
- El stack está levantado para repetir las pruebas con base real o temporal (`tests/integration/` crea su propia base temporal).
- El panel público está en `https://observatorio.ssamuelfernandez.net/` y su API en `https://observatorio-api.ssamuelfernandez.net/` (según `despliegue-tunel`).
- Fuera de alcance: nuevas funciones, cambios de código del panel o de la API, pruebas de carga, panel o informes de calidad, ejecución de las pruebas 9 y 10 por el agente y marcar el checklist.

## Clarifications

### Session 2026-11-14

- Q: ¿Dónde se inyectan los casos sintéticos (nulos, versión tardía, coordenadas inválidas, evento marítimo)? → A: En la base temporal que ya crean las pruebas de integración (`TempDatabase`) o en el esquema `replay`; nunca en `live` real, porque la constitución §7 exige separar lo sintético y los datos reales del análisis.
- Q: ¿Se vuelve a ejecutar todo o se reutiliza? → A: Se reutilizan las evidencias y los tests existentes (`bloque3_prueba2_reenvio.out`, `bloque3_prueba3_4_versiones.out`, `bloque3_prueba6_cuarentena.out`, `bloque4_prueba8_corte_simulado.out`, `geografia_prueba5.out`, `geografia_prueba7.out`, `T053_*`); solo se añade la comprobación de la API y del panel donde la evidencia actual solo llega a PostgreSQL (pruebas 1, 5, 7).
- Q: ¿Cómo se prueba la 8 (reinicio)? → A: Con la evidencia real `prueba8_reinicio.log/.out` y `test_restart_crash.py` (corte tras el commit, base idéntica a la ejecución sin corte); no se añade un corte nuevo.
- Q: ¿Qué estado tienen 9 y 10 mientras falten las capturas? → A: «Pendiente de la demostración del alumno»; las capturas de la misma red del servidor no las sustituyen.
- Q: ¿Qué se hace si el código del panel no cumple 9 o 10? → A: Se reporta el hueco en la ficha y en el resumen; no se corrige (fuera de alcance, FR-013).
- Q: ¿Hay que marcar el checklist? → A: No; lo hace el alumno con las evidencias.
- Q: ¿Qué hallazgo previo hay sobre el código del panel? → A: `frontend/src/shared/hooks/useObservatory.ts` mantiene la última lectura (`keepPreviousData`, `retry: false`) y `frontend/src/components/StatusBanners.tsx` (líneas 82 a 89) muestra «Datos antiguos» con la edad y la hora UTC de la última lectura; al volver la API el error se limpia en el siguiente refresco. Límites a reportar: el refresco por defecto es de 60 s (`frontend/public/config.json`), así que el aviso y la recuperación tardan hasta ese tiempo más el timeout; y la opción `refetchIntervalInBackground` no se usa, por lo que con la pestaña oculta el navegador puede no refrescar.

### Preguntas para el alumno

Decisiones provisionales; ninguna toca contratos, pero afectan al alcance de la evidencia.

1. **Origen del caso de la prueba 5 (magnitud nula)** — RESUELTA (decidida por el supervisor, ver docs/evidencias/sprint/decisiones.md). Decisión: base temporal (`TempDatabase`) para SQL y API, y captura de ND con el panel en modo mock (sintético, etiquetado), porque el panel público solo tiene datos reales sin nulos. Recomendación: esa; alternativa (rechazada por la constitución §7): inyectar un evento nulo en `replay` y verlo en la URL pública, lo que exigiría subir un cambio de datos al despliegue real.
2. **Captura de la prueba 7 (marítimo)** — RESUELTA (decidida por el supervisor, ver docs/evidencias/sprint/decisiones.md). Decisión: captura del panel público filtrando «Sin país asignado» con datos reales (USGS tiene eventos oceánicos sin polígono). Recomendación: esa, porque es un caso real y no requiere inyectar nada.
3. **Prueba 1 con evento real** — RESUELTA (decidida por el supervisor, ver docs/evidencias/sprint/decisiones.md). Decisión: reutilizar `docs/evidencias/productor-live/prueba1_evento_nuevo.out` (evento real hasta PostgreSQL) y completar API y panel con una captura de un evento real reciente y con la comprobación sintética en base temporal. Recomendación: esa; no se espera a que USGS publique un evento nuevo.
4. **Corrección de `despliegue-tunel`** — RESUELTA (decidida por el supervisor, ver docs/evidencias/sprint/decisiones.md). Decisión: se edita `README.md` y las dos plantillas de 9 y 10 (solo texto de estado), aunque son de una feature cerrada. Recomendación: hacerlo, por exigencia del alumno y por honestidad de la evidencia.
5. **Límites del panel en 9 y 10 (60 s de refresco; pestaña en segundo plano)** — RESUELTA (decidida por el supervisor, ver docs/evidencias/sprint/decisiones.md). Decisión: se documentan en la ficha y se pide al alumno mantener la pestaña visible y esperar hasta 60 s más el timeout; si lo considera un hueco, decide si se abre una corrección en otra feature (por ejemplo, `refreshSeconds` más bajo en la demostración). No se cambia código aquí.
