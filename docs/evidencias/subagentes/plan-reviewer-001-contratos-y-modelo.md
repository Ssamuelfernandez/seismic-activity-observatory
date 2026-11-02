# Informe del subagente plan-reviewer

- **Feature:** `contratos-y-modelo` (`specs/001-contratos-y-modelo/`)
- **Agente:** `plan-reviewer` (definición en `.claude/skills/agents/plan-reviewer.md`), ejecutado como agente genérico de solo lectura con esas instrucciones
- **Fecha:** 2026-11-02
- **Nota:** el informe de debajo es el texto íntegro devuelto por el subagente, sin resumir ni modificar.

---

## Informe de plan-reviewer: feature `contratos-y-modelo` (specs/001-contratos-y-modelo)

Revisión solo lectura. Leí todos los archivos indicados y contrasté los números a mano:
- Las sumas de `by_hour`, `by_country` y los dos histogramas del ejemplo de `api.md` §5.2 dan 210.
- `n_2025/365` = 34,0, `diff_abs` = −10 y `variacion_pct` = −29,41 cuadran.
- Los límites de `period` y de `reference_period` son correctos.
- Hay 13 tablas y 11 índices `ix_*` en el DDL, en la evidencia y en tasks.
- Las columnas de `db-schema.md` §3 coinciden con `sql/001_schema.sql`.
- Los ejemplos de `api.md` y `kafka-message.md` coinciden con `explore_usgs_salida.txt`.
- Ninguna referencia a features con número (003-, 004-…) en `specs/001-contratos-y-modelo/`.

Cobertura de IDs: E1 (T017, T018), E2 (T010), E3 (T010, T017), E4 (T009, T017), E5 (T009, T011, T012), E7 (T009, T011) y C4 (T006, T012) tienen tarea. Falta el criterio de aceptación en la spec (hallazgo 1).

### 1) Hallazgos

| # | Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|---|
| 1 | La spec no tiene sección «Criterios de aceptación» con los IDs E1–E5, E7 y C4. La tabla 03 §4.2 exige que cada spec termine con ella. Solo existe la tarea pendiente T019. FR-014 contiene el criterio de E5, pero el resto de IDs no tiene criterio explícito. | importante | `spec.md` (final; no existe la sección); `tasks.md` T019 | E1–E5, E7, C4; 03 §4.2 |
| 2 | La spec sigue diciendo que las decisiones de `api.md` están abiertas, y eso contradice sus propias Clarifications del 2026-11-02. Afecta a: `Status: Draft` (línea 7), FR-010 («esta especificación no las da por resueltas»), Assumptions («hasta entonces permanecen abiertas») y SC-002 («antes de pasar a la planificación»). Ninguna tarea corrige este texto: T019 y T020 solo cubren el criterio de aceptación y la checklist. | importante | `spec.md` líneas 7, 155, 200 y SC-002 | Constitución §19 (spec revisada); ambigüedad |
| 3 | P14 sigue pendiente de aprobación (unicidad de cuarentena `(original_sha256, reason)` y de exclusión `(event_id, updated_ms, kind)`). Ya está implementada en el DDL y probada (T12 y T13 de la evidencia). `research.md` R7 la presenta como decidida, sin etiqueta. `db-schema.md` §3.5 y §3.6 la tratan como cerrada, mientras que `plan.md` línea 113 la marca como pendiente. | importante | `plan.md` líneas 113 y 130; `research.md` R7; `db-schema.md` §3.5–3.6; `tasks.md` T013 | Constitución §1 (idempotencia), §19 |
| 4 | `research.md` conserva etiquetas «PROPUESTA» en R5 (`is_synthetic`), R11 (nombres y sentido del cursor) y R12 (`max(min_mag, 4.0)`). La cabecera dice «pendiente de aprobación». Las tres figuran como aprobadas en `plan.md` (P11, P1/P2, P10) y en `spec.md` (Clarifications 2026-11-02). Es información contradictoria sobre qué está decidido. | importante | `research.md` línea 3, R5 (línea 29), R11 (línea 65), R12 (línea 68) | Ambigüedad |
| 5 | Ruta de evidencia incorrecta en el plan: `plan.md` dice `docs/evidencias/001-contratos-y-modelo/`. La carpeta real y la que usan tasks, spec y quickstart es `docs/evidencias/contratos-y-modelo/`. | menor | `plan.md` «Cierre de la feature» (línea 105) | Constitución §16 |
| 6 | Textos desactualizados sobre las tareas. `plan.md` línea 89 dice «tasks.md … no existe aún» y la línea 103 «pendiente para tasks». `data-model.md` línea 3 dice «En tasks se añadirá una tarea». La tarea ya existe (T018). | menor | `plan.md` líneas 89 y 103; `data-model.md` línea 3 | Consistencia |
| 7 | Hueco entre el DDL y los motivos de cuarentena. Los `CHECK` de cordura (`mag` −10…15, `depth_km` −100…1000, `lon`, `lat`) y los tipos (`sig` integer, `status` text) harían fallar el INSERT de un evento fuera de rango o mal tipado. `kafka-message.md` §6 solo cubre `lon`/`lat` (`coordinates_out_of_range`). No hay motivo para `mag` o `depth` fuera de rango, ni para `replay_at` nulo con `mode=replay`, que `kafka-message.md` §3 declara obligatorio. Un fallo de `CHECK` aborta la transacción y podría bloquear la cola (ver preguntas). | importante | `kafka-message.md` §3 y §6; `sql/001_schema.sql` (`current_event_mag_range` y `current_event_depth_range`); `db-schema.md` §2 | Constitución §6 y §5 |
| 8 | `api.md` §3.4 marca `place` como «no\*» (no nulo) con nota «si faltara, se serializa null». La Clarification de 2026-11-02 dice que `place`, `status`, `url` y `sig` pueden ser `null`. La columna `place` del DDL es nulable. La tabla contradice la decisión. | menor | `api.md` §3.4 (fila `place`) | FR-009.4; spec Clarifications |
| 9 | `quickstart.md` está desactualizado respecto a lo ya ejecutado. Dice que la validación completa del DDL «corresponde a `consumidor-idempotente`», cuando FR-014 y R13 indican que ya se probó en PG16. No cita `prueba_esquema_001.sql`. Su §5 describe una prueba más pobre que la real. | menor | `quickstart.md` párrafo inicial y §5 | FR-014, E5 |
| 10 | `checklists/requirements.md` tiene notas obsoletas: tipos de evento «confirmar en clarify», decisiones de `api.md` «las decide en `/speckit-clarify`» y un caso límite «queda abierto». T020 ya lo contempla (pendiente). | menor | `checklists/requirements.md` §Notes | Ambigüedad |
| 11 | Falta completar el cierre en dos puntos. T021 solo pide filas en CODEMAP para `contracts/` y `sql/001_schema.sql`. CODEMAP no tiene ninguna fila de esta feature (grep sin resultados). No menciona `docs/evidencias/contratos-y-modelo/`. T022 deja el README (que solo tiene el título) para el cierre. | menor | `tasks.md` T021–T022; `CODEMAP.md` | Constitución §16; CLAUDE.md |
| 12 | Posible choque con la constitución §13. `plan.md` justifica como «excepciones del contrato» los nombres en español `n_reciente`, `media_diaria_2025`, `variacion_pct` y `sin_valor`. Esos nombres no están en `CONTRATO-API.md`; solo aparecen en `02-roadmap-implementacion.md`, es decir, son propios del alumno. La excepción de §13 es solo para campos fijados por el profesor. | menor | `plan.md` fila §13 de Constitution Check; `api.md` §1 (convención de nombres) | Constitución §13 |
| 13 | Orden y dependencias razonables, con dos matices. T024 pide el `plan-reviewer` tras T019–T023, pero esta revisión se hace antes y ya señala trabajo previo. Además, el cambio del DDL por P14 obligaría a repetir T011 y T012 y a revisar el aislamiento live/replay (§Implementation Strategy lo recoge). | menor | `tasks.md` T013, T023, T024 | Orden |
| 14 | Detalles de redacción y trazabilidad. (a) `db-schema.md` §3.1 dice que «Consulta Q2 … usa» la PK de `country`, pero Q2 es la consulta de `current_event`. (b) `api.md` §8 dice «10 valores distintos» de país cuando son 9 países más `null`. (c) El roadmap F6 (línea 176) usa `source='historical'`, mientras que los contratos usan `usgs_historical`. (d) Los índices `replay` del DDL no repiten el comentario Qn (cosmético). | menor | `db-schema.md` §3.1; `api.md` §8; `02-roadmap-implementacion.md` línea 176 | Consistencia |
| 15 | Verificado, sin hallazgo: ningún contrato modifica `CONTRATO-API.md`. `api.md` §7 lo cubre línea a línea, aunque T016 lo deja pendiente por revisión manual. El tratamiento de nulos y negativos, los tiempos (`CHECK` de ms) y el país por geometría respetan la constitución. La tabla de conformidad cubre `metadata`, filtros y errores. | — | — | — |

Notas de contraste con el feed (`explore_usgs_salida.txt`): 210 eventos, 0 nulos de `mag`, 1 magnitud negativa, 2 profundidades negativas, `updated − time` máximo 1125,1 min y 177 entidades en el catálogo. Todo coincide con lo que citan los contratos.

### 2) Decisiones que el alumno debe tomar

1. **P14:** ¿apruebas la unicidad de cuarentena `(original_sha256, reason)` y de exclusión `(event_id, updated_ms, kind)`? Consecuencia: dos mensajes distintos con el mismo contenido inválido comparten una fila y se guarda el offset del primero. Si no, habría que ajustar `db-schema.md` y el DDL, y repetir T011 y T012.
2. ¿Se amplía la lista de motivos de cuarentena (`kafka-message.md` §6) para cubrir `mag` o `depth` fuera de los `CHECK`, tipos incorrectos (`sig`, `status`) y `replay_at` nulo en `mode=replay`? ¿O prefieres que esa decisión quede para `consumidor-idempotente`? Para decidirlo, ¿el consumidor debe validar esos límites antes de insertar, de modo que un `CHECK` nunca aborte la transacción?
3. ¿Estás de acuerdo en que `n_reciente`, `media_diaria_2025`, `variacion_pct` y `sin_valor` se justifiquen como nombres tuyos en español y no como «contrato del profesor»? ¿O prefieres nombres en inglés?
4. `truncated` es `true` también en la última página de una consulta paginada (`count < total`). ¿Lo confirmas, o debería ser `true` solo si hay `next_cursor`? Esto no contradice `CONTRATO-API.md`, pero conviene que lo confirmes.
5. `country_id` acepta `^[A-Za-z]{3}$`: ¿se normaliza a mayúsculas o se rechaza el minúsculo? (Hoy no está especificado.)
6. ¿Una sola tabla `ingest.ingest_state` compartida entre live y replay es lo que quieres? El replay no tiene estado de ingesta propio, y el aislamiento J3 de `db-schema.md` §1 habla de las cuatro tablas de eventos, no de `ingest.*`.
7. Orden de cierre: ¿quieres reordenar para pasar `/speckit-analyze` (T023) tras corregir el texto obsoleto de los hallazgos 2–6?

### 3) Veredicto

**Corregir antes de revisar**: hay texto obsoleto en la spec, el plan y `research.md` que contradice las decisiones aprobadas, falta la sección de criterios de aceptación y queda P14 por decidir. Los contratos y el DDL son coherentes entre sí y con el feed real.
