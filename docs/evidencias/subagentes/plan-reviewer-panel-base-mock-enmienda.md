# plan-reviewer — 008-panel-base-mock (enmienda del 2026-11-10)

Informe del subagente `plan-reviewer`, guardado tal cual lo entregó (solo lectura; no modificó nada). Una única revisión; la ronda de corrección está al final.

Límite declarado por el revisor: no leyó la constitución completa; contrastó §5, §7, §10, §11, §15, §16, §17 y §19 con lo que cita la spec. Los IDs G0 a G17 y SC-001 a SC-016 tienen criterio y tarea. Los contratos no se redefinen (cortes de profundidad, intervalo de 2025, `country_id`, ocho campos de `metadata` coinciden con `api.md`).

| # | Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|---|
| 1 | T025 borra `_import-front/`, pero T028 (`realistic`, parte de las zonas del mock en memoria) y T029 (`mock/backend.ts`, sale de `shared/api/mock.ts`) lo necesitan después; T028 se declara «independiente». | importante | `tasks.md` T025 frente a T028/T029 y Dependencias; `plan.md` mapa de portado | Orden y dependencias; G15 |
| 2 | Si P3 se resuelve como «lo da la API», el aviso de «desactualizado» sigue siendo un cálculo del cliente que T032 deja y T036 comprueba sin resolver. Decisión abierta sobre §17, no un error. | importante | `spec.md` P3 y FR-023; `tasks.md` T032 | §17; FR-029; G7 |
| 3 | D3 figura como «Vigente» pero P1 sigue abierta; T024 ya porta con esa estructura. | menor | `spec.md` D3 y P1 | Ambigüedad |
| 4 | FR-016, FR-020, FR-021, FR-022 y FR-023 no aparecen en ningún «Cubre». | menor | `tasks.md` Cubre T024–T040 | Cobertura de FR |
| 5 | Las «Prueba» de T026 y T028 remiten a T038 y al «validador de T038»; el validador es el de T004 y T038 depende de T028: referencia circular. | menor | `tasks.md` T026, T028, T038 | Orden |
| 6 | SC-003 («`mock-` en `dist/`») puede dar falsos positivos con código de terceros; acotar a los ids. | menor | `spec.md` SC-003; `tasks.md` T029 | SC-003; §7 |

Decisiones del alumno señaladas: P1 y P3 (P3 afecta a §17); P2 (G5b exige «panel lateral», el plan usa el cajón inferior); dónde guardar la copia de `globo-lab` que T028/T029 necesitan.

**Veredicto del revisor**: Corregir antes de revisar (solo el hallazgo 1; el resto, menores o decisiones abiertas).

## Ronda de corrección (única)

| # | Corrección aplicada |
|---|---|
| 1 | El borrado de `_import-front/` pasa de T025 a **T040** (cierre); T028 y T029 lo usan como fuente y las dependencias lo dicen. `spec.md` (Assumptions) y `tasks.md` (cabecera) alineados. |
| 2 | P3 ampliada: si el alumno decide que lo dé la API, es un cambio de contrato que se consulta antes y queda fuera de `008`; mientras tanto el panel lo calcula y lo rotula. Sin cambio de tareas. |
| 3 | D3 pasa a «vigente por defecto, a confirmar en P1». |
| 4 | «Cubre» ampliado: T024 (FR-016, FR-020), T035 (FR-021, FR-022) y T036 (FR-023). |
| 5 | T026 y T028 remiten a «las pruebas de T038» y al validador de T004 (ya hecho; T038 lo amplía). |
| 6 | SC-003, T029 y `quickstart.md` buscan `__MOCK_BACKEND__` y el texto «Sintético:» en `dist/`, no `mock-`. |
