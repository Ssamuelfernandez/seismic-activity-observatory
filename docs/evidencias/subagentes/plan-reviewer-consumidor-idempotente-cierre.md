## Revisión de CIERRE: consumidor-idempotente (rama 003-consumidor-idempotente)

Alcance de lo que he mirado:
- Constitución, spec y plan completos. De tasks.md, la sección «Diferidas» y los bloques relacionados.
- Código de `consumer/` (loop, pipeline, writer, queries, resilience, counters, db_errors, main) y de `common/` (validation, quarantine_row, processing).
- La bitácora, README, CODEMAP y las evidencias clave.
- No he releído línea a línea `storable`, `decode`, `transform` ni `validation_envelope`, ni los tests. Me apoyo en que los verificadores de cada bloque los revisaron (bitácora, filas de implementar) y en las salidas guardadas.

### 1. Hallazgos

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| **Las reglas de calidad del consumidor no están en `docs/memoria.md`.** La memoria no recoge las reglas de validación, la transacción y orden de commits, la cuarentena ni la secuencia FAQ 12. T084 está diferida. Ejemplo: el evaluador abre la memoria buscando las reglas de C1 y su §4 «Calidad» no las trae. Hoy solo están en `specs/` (que no debe copiarse a `docs/`) y en `kafka-message.md` §6. Afecta a C1, cuya columna de verificación dice «Reglas listadas en memoria». | Importante | `tasks.md` «Diferidas» (T084); `docs/memoria.md` §4; spec FR-034 | C1 (OBL), FR-034, constitución §16, procedimiento §6 paso 9 |
| **Spec y plan no reflejan el recorte de tareas.** El ejemplo más claro es el catálogo de países. La spec sigue exigiendo con MUST el catálogo de países (FR-025, US6.1, SC-011), la comprobación de esquema (FR-026) y la paridad `live`/`replay` (FR-032, US6.3). Tampoco quedan reflejados SC-006 y US2.5 con Docker real, ni US3.6–3.8 con base real. Para todo esto no hay código, test ni evidencia (el catálogo ni siquiera existe en `common/` ni en `consumer/`), y la spec dice «Status: Draft» y no los marca como diferidos. Además, la bitácora no registra ninguna decisión del alumno sobre el recorte (solo el commit «recorte de tareas… 26 diferidas»). El alumno no podría defender qué prometía la spec y qué entrega. Ninguno de esos puntos es un ID OBL de esta feature (C1–C8, C13) ni una prueba 2/3/4/6/8, así que la gravedad viene de la incoherencia, no de un fallo funcional. | Importante | `spec.md` FR-025, FR-026, FR-032, SC-006, SC-011, US2.5, US6; `plan.md` §3 y §8; `tasks.md` «Diferidas»; `bitacora.md` | Constitución Governance («corregir en spec, plan o tareas»), §19; coherencia spec↔tasks↔código |
| **Evidencias de fallo de PostgreSQL y de Kafka con el stack real: no existen.** SC-006 (PG parado) y US2.5 (Kafka caído) están cubiertos solo con dobles (T045/T053/T055). El comportamiento «no confirma offset si falla la BD» está en el código (`resilience.py`, `loop.py`) y probado en unitarias, así que C2 se sostiene. Falta la evidencia de integración y debería quedar como límite conocido en la spec (va dentro del mismo arreglo del hallazgo anterior). | Menor | `tasks.md` T077, T078, T079 diferidas | SC-006, US2.5 |
| **README dice que el consumidor lee `earthquakes.live` y `earthquakes.replay`.** El código consume solo `KAFKA_TOPIC` (live) y la spec deja replay fuera de alcance. | Menor | `README.md` línea 123 | Spec «Fuera de alcance»; precisión de documentación |
| **SC-009 (contadores contra SQL) se concilia con `process_record` y contadores reales sobre una base temporal**, no con el consumidor en Docker. Las cifras de FR-036 coinciden: 5/5, 7/5 y 7/7 en `bloque4_contadores_integracion.out`. Es una desviación razonable; basta anotarla en la spec. | Menor | `bloque4_contadores_integracion.out`; spec SC-009 | C8, SC-009 |
| **Discrepancias ya anotadas: siguen ABIERTAS las cuatro, no se cuentan como nuevas.** (a) `build_quarantine_row(decoded, reason, ref, now)` tiene 4 parámetros; plan y tasks dicen 5. (b) Research §5 dice que `RecursionError` salta a 1500 niveles; la prueba usa 200000 niveles. (c) El criterio de T075 dice `is_synthetic=true` en toda la cuarentena, pero las filas 3 y 4 de `prueba6_cuarentena.out` (bytes no UTF-8 y tombstone) tienen `f` por FR-011. (d) `is_synthetic=false` en filas ilegibles, que es lo mismo que (c). | Menor | plan §2; research §5; tasks T075; evidencia prueba 6 | — |
| **Otras notas menores.** Código de prueba de fallo (`fault_hook`) y la variable `CONSUMER_FAULT_CRASH_AT_OFFSET` en producción: inactivos con la variable vacía y solo disparan con `is_synthetic=true`, así que quedan bien acotados. Evidencias con codificación mixta, ya anotadas por los verificadores. | Menor | `consumer/fault_hook.py`, `compose.yaml` | — |

### 2. Cumplimiento por requisito (resumen)

- **C2 y constitución §1.**
  - El orden es el correcto: `process_record` hace el commit en PG y el hook; luego `log_decision`, `commit_offset_with_retry` y `apply_result` (`loop.py::process_and_commit`).
  - `enable_auto_commit=False` y `auto_offset_reset="earliest"`.
  - Prueba 8 con Kafka real (`prueba8_reinicio.log` y `.out`): FAULT en el offset 2, reentrega como `redelivery_ignored`, SQL idéntico (2 actuales, 3 versiones, 0 duplicados) y 14/14 comprobaciones.
- **C3 y C4 (§2).**
  - `ON CONFLICT (event_id, updated_ms) DO NOTHING`.
  - Upsert con `WHERE EXCLUDED.updated_ms > current_event.updated_ms`.
  - `decide_version_outcome` es pura; el `FOR UPDATE` va dentro de la transacción de `write_event`.
  - Pruebas 2, 3 y 4 con evidencia SQL (`faq12_antes_despues`, `prueba2`, `prueba3_4`).
- **C5 y prueba 6 (§6).**
  - Fila de cuarentena `coordinates_out_of_range` con referencia al mensaje (tema, partición, offset) y sin fila en las tablas de evento.
  - Sentencia sin destino de conflicto, comprobada con el rol real.
  - Dedup por (hash, motivo).
- **C6 y C7 (§3 y §5).**
  - Tipos exactos; `bool` no cuenta como número.
  - Rangos sin umbral en 0; nulos conservados como `NULL`.
  - `ms_to_utc` con aritmética entera; `ingested_at` separado del tiempo del evento.
- **C8.**
  - Contadores en memoria, actualizados tras el commit del offset.
  - `check_identities` implementa las dos identidades de FR-023.
- **C13 (§7).**
  - `is_synthetic` se copia a las tres tablas.
  - Las filas ilegibles quedan en `false` por FR-011.
- **§14.**
  - Lo puro está en `common/`; el SQL, solo en `queries.py`.
  - No hay `except Exception` genérico: los defectos del programa se propagan.
- **§9, §11 y §12.**
  - Sin dependencias nuevas.
  - Sin puertos nuevos expuestos, sin país y sin replay.
  - Un servicio `tests` bajo perfil de Compose, aprobado en el diseño.
- **§13.** Identificadores en inglés; docstrings en español con la plantilla.
- **Contratos.** Sin cambios (`git diff` de contratos = 0, `bloque6_cierre_T081.txt`).
- **Frontend y API.** No he encontrado cambios en `api/` ni en `frontend/`; no tengo Bash para comprobar un diff.
- **Cierre (§16).**
  - README y CODEMAP actualizados.
  - Evidencias en `docs/evidencias/consumidor-idempotente/`.
  - Pruebas ejecutadas: 412 unitarias y 35 de integración en verde (`pytest_integracion.txt`).
- **Realismo.** No encuentro flujo realista de USGS (mag nula, `place` nulo, magnitudes y profundidades negativas, ids largos) que pierda o duplique datos o bloquee el consumo.

### 3. Decisiones que el alumno debe tomar

1. ¿Confirma el recorte de 26 tareas diferidas? Si sí, que la spec lo refleje: marcar FR-025, FR-026, FR-032, SC-006, SC-011, US2.5, US3.6–3.8 y US6 como «diferido/límite conocido», e indicar que el catálogo de países queda para otra feature. Si no, hay que reactivarlas.
2. ¿Escribe ahora el §4 «Calidad» de `docs/memoria.md` con las reglas del consumidor (reactivar T084) o lo deja para `017-memoria-defensa`? Lo segundo choca con C1 y con el procedimiento §6 paso 9.
3. ¿Acepta que SC-009 se verifique con integración (`process_record` + base temporal) y no con el contenedor?

### 4. Veredicto

Corregir antes de revisar (cambios solo documentales: memoria §4, marcar lo diferido en la spec y la línea de README). El código y las evidencias cumplen C1–C8, C13 y las pruebas 2, 3, 4, 6 y 8.
