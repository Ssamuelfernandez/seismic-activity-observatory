# Informe del agente plan-reviewer — pasada final

- **Feature:** 001-contratos-y-modelo (`specs/001-contratos-y-modelo/`)
- **Agente:** plan-reviewer
- **Fecha:** 2026-11-02

El informe que sigue es el devuelto por el agente, sin resumir ni modificar.

---

## Revisión final de `001-contratos-y-modelo`

No he modificado nada. Cobertura, contratos y constitución están bien. Lo que queda son un hueco en el orden de prevalencia, tareas sin actualizar y un cierre anticipado.

**Cobertura.** Todos los IDs asignados a la feature (E1–E5, E7, C4) están en «Criterios de aceptación» de `spec.md` y tienen tarea y evidencia. Las sumas de los ejemplos de `api.md` §5.2 cuadran: 210 en `by_hour`, `by_country` e histogramas, y 24 en `n_recent`. Con 12 410 / 365 = 34,0 y diff −10, `variation_pct` sale −29,41.

**Contratos.** `plan.md` no los duplica ni propone cambiarlos. `api.md` §7 no contradice el contrato del profesor.

**Constitución.** Sin violaciones. El cierre es incompleto solo por lo descrito abajo (§16, §19).

**DDL.** `sql/001_schema.sql` coincide con `db-schema.md`: 13 tablas, 11 índices, `live` idéntico a `replay`. La evidencia lo confirma: 13 tablas y 11 índices.

### 1. Hallazgos

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| El orden de prevalencia de motivos de cuarentena omite `replay_at_missing`. La tabla tiene 14 motivos y la lista ordenada solo 13. No está claro qué gana si un mensaje tiene `replay_at_missing` y otro fallo, por ejemplo `invalid_envelope`. | importante | `kafka-message.md` §6 (frase «Un mensaje, una fila de cuarentena»); también `spec.md` Clarifications («de `invalid_json` a `db_constraint_violation`») | Constitución §6, §15; P21; C8 |
| `tasks.md` está desactualizado. T021 (CODEMAP) y T022 (README) siguen sin marcar, pero `CODEMAP.md` y `README.md` ya tienen el contenido. «Para cerrar» lista T008, T016 y T018 como pendientes y están `[x]`. El bloque «Parallel Opportunities» los llama «pendientes». «Implementation Strategy» dice «salvo T008». «Polish» dice que T021 y T022 están por hacer. | importante | `tasks.md`: Fase 7 (T021, T022), «Dependencies & Execution Order», «Parallel Opportunities», «Implementation Strategy» | Constitución §16 (trazabilidad del cierre) |
| El cierre se declara antes de tiempo. `CODEMAP.md` ya tiene la fila de «Historial de features cerradas» y `README.md` dice «Cerrada a falta de revisión», pero T024 (`/speckit-analyze`), T025 (este informe) y T026 siguen sin hacer. T026 pide añadir esa fila «al cerrar, tras la aprobación del alumno». | importante | `CODEMAP.md` «Historial de features cerradas»; `README.md` tabla «Estado actual»; `tasks.md` T024–T026 | Constitución §19 |
| La evidencia no prueba el caso 5 de SC-004 («mismo `updated`, contenido distinto → se conserva la primera»). T11 solo ejecuta `DO NOTHING` con otro `mag` en un `updated` ya existente. La comparación `original <> :nuevo` y el log los hace el consumidor y no están en el DDL. | menor | `spec.md` SC-004 y «Criterios de aceptación» C4; `prueba_esquema_001.sql` T11; `db-schema.md` §5 | C4; SC-004 |
| La salida de T11 es confusa. La fila de `updated` 1793528420510 muestra `mag` 9.0, mientras que `current_event` conserva −0,06. La etiqueta «inicial no existe» da a entender que la versión inicial nunca se insertó en `event_version`. Así no se ve el caso «evento nuevo» (versión y estado). | menor | `docs/evidencias/contratos-y-modelo/prueba_esquema_001_salida.txt` (T11); `prueba_esquema_001.sql` | C4; SC-004 |
| `plan.md` está desfasado. Dice «P15–P19 son decisiones tras el `plan-reviewer`», pero la tabla llega a P21. Además, «Cierre (tareas T018–T026)» incluye T018, que es de la historia US4. | menor | `plan.md` intro de «Decisiones aprobadas» y sección «Cierre» | coherencia documental |
| `CODEMAP.md` cita C5 en la fila del contrato Kafka, pero C5 no es un ID de esta feature. Además, la cabecera sigue diciendo «andamiaje inicial. Las rutas son previstas», aunque ya hay entregables reales. | menor | `CODEMAP.md` líneas 3 y 9 | CLAUDE.md (CODEMAP al día) |
| `spec.md` sigue con `Status: Clarified` aunque la feature está hecha y pendiente de revisión. | menor | `spec.md` cabecera | coherencia documental |
| `plan.md` declara Python 3.12 «fijada aquí», pero no existe `.python-version` ni lock. Está aplazado a `infra-compose` con justificación en `research.md` R2. Es aceptable si el alumno lo da por bueno. | menor | `plan.md` Technical Context; Constitution Check §11 | Constitución §11 |

### 2. Decisiones que el alumno debe tomar

1. ¿Dónde va `replay_at_missing` en el orden de prevalencia de `kafka-message.md` §6? Hay que decidirlo porque cambia el contrato, no solo la redacción. Una opción coherente es justo después de `invalid_envelope`, o antes de `mode_topic_mismatch`, porque es un fallo del sobre.
2. ¿Quiere añadir ahora a la evidencia una prueba del caso 5 y de «evento nuevo», o dejarla para la prueba de integración de `consumidor-idempotente`? Si repite T11, habrá que repetir T011/T012 y volver a comprobar que el DDL no cambia.
3. ¿Mantiene la fila de «Historial de features cerradas» y el «Cerrada» del README antes de su aprobación, o prefiere retirarlas hasta que T026 se ejecute?
4. Sobre T025: este informe ya está en tu mano. Falta guardarlo en `docs/evidencias/subagentes/`, y yo no puedo escribir ahí.

### 3. Veredicto

Corregir antes de revisar: el hueco del orden de prevalencia (§6) y las tareas desactualizadas (`tasks.md`). Ninguno toca el DDL ni la API, así que la evidencia sigue vigente.
