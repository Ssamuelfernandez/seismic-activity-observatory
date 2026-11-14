# Investigación: Pruebas de aceptación (012)

Fase B. Resuelve cómo se reutiliza lo existente y qué falta. Todas las rutas se comprobaron con `ls` y `grep` en el repositorio el 2026-11-14. Los archivos de `docs/evidencias/consumidor-idempotente/` se abrevian `CI/`, los de `productor-live/` como `PL/` y los de `geografia-pais/` como `GP/` (todos bajo `docs/evidencias/`).

## 1. Qué existe para cada prueba

| Prueba | Pruebas automáticas existentes (`tests/integration/`) | Evidencia existente | Hueco real |
|---|---|---|---|
| 1 Evento nuevo | `test_producer_cycles.py::test_only_a_greater_updated_is_published`; `test_api_events.py` y `test_api_coherence.py` (API con eventos sembrados, no procesados por el consumidor) | `PL/prueba1_evento_nuevo.out` (real, hasta PostgreSQL: 192 a 193 filas, evento `ok2026vqse`) | Ninguna prueba recorre consumidor a API con un evento nuevo; falta la captura del panel |
| 2 Reenvío | `test_idempotence.py::test_hundred_resends_change_nothing`; `test_producer_cycles.py::test_second_cycle_with_same_response_publishes_nothing`, `test_restart_on_same_database_publishes_nothing` | `CI/bloque3_prueba2_reenvio.out/.sql`, `CI/prueba2_reenvio.out`, `PL/prueba2_reenvio.out` | Ninguno |
| 3 Versión posterior | `test_faq12.py::test_faq12_sequence_gives_two_current_and_three_versions`; `test_idempotence.py::test_null_then_value_and_reverse_follow_updated`; `test_geography.py::test_later_version_at_sea_clears_country` | `CI/bloque3_prueba3_4_versiones.out/.sql`, `CI/faq12_antes_despues.out/.sql`, `CI/bloque3_faq12.out` | Las agregaciones afectadas (por país y por hora) solo se miran en SQL; falta verlas por API |
| 4 Versión antigua tardía | `test_faq12.py::test_late_old_version_is_kept_in_history_but_not_current`; `test_geography.py::test_late_old_version_in_another_country_does_not_change_country` | `CI/bloque3_prueba3_4_versiones.out/.sql`, `CI/faq12_antes_despues.out` | La API no cambia con la versión tardía (un caso) |
| 5 Magnitud nula | `test_nulls_times.py::test_null_magnitude_is_null_and_negatives_are_kept`; `test_api_events.py::test_event_with_null_mag_depth_and_country`, `test_min_mag_zero_excludes_negative_and_null_and_counts_the_null` | `GP/geografia_prueba5.out/.sql` (y copia en `CI/`) | Un caso que una BD, API y recuentos; la captura de ND (solo mock) |
| 6 Coordenadas inválidas | `test_quarantine.py::test_latitude_145_goes_to_quarantine_only`, `test_one_case_per_contract_reason` | `CI/bloque3_prueba6_cuarentena.out/.sql`, `CI/prueba6_cuarentena.out`, `GP/geografia_prueba6_cuarentena.out/.sql` | Ninguno |
| 7 Evento marítimo | `test_geography.py::test_atlantic_event_is_stored_without_country_and_not_quarantined`, `test_with_country_plus_without_country_equals_total`; `test_api_events.py::test_country_none_selects_events_without_country` | `GP/geografia_prueba7.out/.sql`, `GP/geo_real_day.out`, `GP/geografia_pruebas5_7_kafka.out` | El recuento total y por hora en la API del evento sin país; la captura |
| 8 Reinicio | `test_restart_crash.py::test_crash_after_the_postgres_commit_leaves_the_same_database_as_a_run_without_crash`; `test_producer_cycles.py::test_cut_between_ack_and_mark_resends_once_and_consumer_is_idempotent` | `CI/prueba8_reinicio.log/.out` (real), `CI/bloque4_prueba8_corte_simulado.out/.sql`, `CI/bloque6_restart_consola.txt` | Ninguno |
| 9, 10 Túnel | Vitest `frontend/tests/dataState.test.ts` (estado derivado) | `despliegue-tunel/prueba-09_cierre-tunel.md`, `prueba-10_reapertura-tunel.md` (plantillas); `panel-base-mock/T036_*` (API local parada, no túnel) | La demostración del alumno |
| 11 Reproducción | `test_replay_consumer.py::test_26_messages_give_22_24_0_in_replay_and_nothing_in_live`, `test_repeating_the_26_messages_keeps_counts_and_replay_at`; `test_api_replay_real.py::test_replay_mode_returns_22_events_with_original_times_and_synthetic_flags` | `replay/README.md`, `replay/T052_antes.out`, `T053_despues.out`, `T054_repeticion.out`, `T055_*.json`, `T056_reproduccion.png`, `T056_en_vivo.png` | Ninguno |

Soporte reutilizable: `tests/support/temp_database.py` (`TempDatabase`), `tests/support/db_helpers.py` (`process_message`), `tests/support/api_client.py` (`request_api`, `seed_database`), `tests/support/api_seed.py` (`synthetic_event`), `tests/support/evidence.py`.

## 2. Decisiones

**D1. Un solo archivo de pruebas nuevo.** Decisión: `tests/integration/test_acceptance_api.py` con 5 pruebas puente (1, 3, 4, 5, 7) que pasan un mensaje por el consumidor real (`process_message`) en `TempDatabase` y leen el resultado por la API (`request_api`). Motivo: es el único hueco automático real; el resto se reutiliza. Alternativa descartada: reescribir las pruebas de 2, 6, 8 y 11, que ya cubren su caso con evidencia real.

**D2. Aislamiento.** Decisión: base temporal (`TempDatabase`) para todo dato inyectado; el esquema `replay` solo en la prueba 11 existente. Motivo: constitución §7. Alternativa descartada: transacción revertida sobre `live` real (si el proceso muere se contamina, y el productor sigue escribiendo a la vez).

**D3. Comprobar que `live` no se contamina (FR-006).** Decisión: consulta SQL de solo lectura sobre `live` real antes y después (recuento de `is_synthetic = true`, recuento de `current_event`, md5 de los sintéticos); no se compara el total bruto porque el productor sigue ingiriendo. Los sintéticos que ya hubiera de features anteriores no cuentan: el criterio es que no cambien.

**D4. Prueba 5 sin nulos reales.** Decisión: caso sintético etiquetado en `TempDatabase` (BD y API) y captura de ND con el panel en modo mock (datos etiquetados como sintéticos); sin herramienta de navegador, plantilla con huecos. Motivo: el panel público solo tiene datos reales sin nulos (pregunta 1 de la spec, recomendación adoptada).

**D5. Capturas 1, 5 y 7.** Decisión: con navegador (Claude in Chrome o Edge headless por CDP, como en `docs/evidencias/replay/T056_panel.md`) sobre la URL pública; 1 y 7 con datos reales, 5 con mock local. Sin herramienta, plantilla `.md` con huecos. Sin cuentas ni credenciales.

**D6. Pruebas 9 y 10.** Decisión: no se ejecutan. Revisión del código con archivo y línea, y plantilla. Hallazgos ya verificados: `frontend/src/shared/hooks/useObservatory.ts` (líneas 43 a 56: `refetchInterval`, `retry: false`, `placeholderData: keepPreviousData`); `frontend/src/components/StatusBanners.tsx` (líneas 82 a 89: «Datos antiguos» con edad y hora UTC de la última lectura; sin datos previos, «Sin datos» sin afirmar 0 eventos); `frontend/src/main.tsx` línea 9 (`retry: false`, `refetchOnWindowFocus: false`). Límites a reportar: (a) `refreshSeconds = 60` y `timeoutMs = 15000` en `frontend/public/config.json`, así que el aviso y la recuperación tardan hasta unos 75 s; (b) `refetchIntervalInBackground` no se usa (comprobar con `grep`), por lo que con la pestaña oculta el refresco puede detenerse; (c) `refetchOnWindowFocus: false`, volver a la pestaña no fuerza un refresco; (d) `panel-base-mock/T036_*` probó la API local parada, no el túnel. No se corrige código (FR-013).

**D7. Corrección de `despliegue-tunel`.** Decisión: solo texto de estado en `docs/evidencias/despliegue-tunel/README.md` (línea 17) y la línea 3 de `prueba-09_cierre-tunel.md` y `prueba-10_reapertura-tunel.md`. Están fuera de `specs/012-pruebas-aceptacion/`, por eso las edita la fase de implementación (T108), no esta fase.

**D8. Evidencia de ejecución.** Decisión: la salida de `pytest` se redirige a `docs/evidencias/pruebas/NN_*.txt`. El servicio `tests` monta `docs/evidencias/consumidor-idempotente/` como `EVIDENCE_DIR` y las pruebas pueden reescribir sus `.out`/`.sql`; al terminar se restaura con `git checkout -- docs/evidencias/consumidor-idempotente`.

**D9. Estados.** Tres valores: «Observada» (datos reales ejecutados, con fecha), «Observada (sintética)» (caso etiquetado en base temporal o mock) y «Pendiente del alumno» (9 y 10). Las pruebas 1, 5 y 7 mezclan partes reales y sintéticas y declaran cada parte.

## 3. Sin NEEDS CLARIFICATION

Las cinco preguntas de la spec pasan a decisiones del plan; siguen listadas en `spec.md` para el alumno.
