REVISIÓN DE TASKS, VUELTA 2: consumidor-idempotente (specs/003-consumidor-idempotente/tasks.md). No he modificado nada. Solo he leído archivos y no he ejecutado comandos. El `git diff --stat` vacío sobre contratos y enunciado me lo dio el orquestador.

## Veredicto: Listo para tu revisión
No hay bloqueantes ni importantes. Los 5 importantes, el aislamiento de tests y los 15 menores del informe previo están resueltos. Solo quedan 6 menores de redacción.

## Verificación de los hallazgos previos

| Hallazgo | Estado | Dónde se resuelve |
|---|---|---|
| I-1 (FR-020 sin prueba) | Resuelto | T021 comprueba que `source`, `ingested_at` y `replay_at` coinciden con el sobre y que `json.loads(rows.original) == message["event"]`. T041 hace lo mismo contra la base. La trazabilidad dice "FR-020: T021, T041". |
| I-2 (T074 se contradecía) | Resuelto | Hay tres lecturas definidas (L1, L2, L3). Las cifras se recalculan abajo y cuadran. |
| I-3 (evidencias sin generar) | Resuelto | T036 define `tests/support/evidence.py` y T007 monta el directorio de evidencias en escritura. T037, T039, T040 y T042 escriben con él. T044 recoge y verifica los 7 archivos `bloque3_*` y afines. |
| I-4 (T041 mal definida) | Resuelto | T093 comprueba el rango solo con SQL antes de T021/T023. T041, "Escalados" (b), research §6 y plan §13.2 coinciden: detener y escalar, sin reducir el rango, y la lista de tareas a rehacer es la misma. |
| I-5 (`updated_ms` en `ProcessingResult`) | Resuelto | Está en data-model §1 (ya figura), T001a, T013, T047, T053 y T054. |
| Aislamiento T040, T042, T058 | Resuelto | Cada una pide `finally` con `DROP` o `GRANT`. T036 añade `schema_guard`, que comprueba tras cada prueba. |
| M-1 a M-15 | Resueltos | M-1: T083. M-2: T008. M-3: T007. M-4: dependencia T035 antes de T037. M-5: T037. M-6: T064 con 8 tablas, T086 y T087 sin repetición, y T089 trata el `print` heredado. M-7: T034 y T047. M-8: decisión (6). M-9: `--yes` en T071 y T073. M-10: T076. M-11: nota de Git Bash. M-12: T088 con `git diff HEAD` más `git status`. M-13: T023. M-14: subtareas T001a–d. M-15: T056 usa `grep`, no una prueba. |

## Comprobaciones independientes
- **Estado de la lista:** hay 93 líneas `- [ ] T###` y ninguna `[x]`. La cabecera dice 93 tareas y T092 como parada. Las referencias cruzadas T0xx de plan, research, data-model, quickstart y consumer-runtime solo citan T093, T041 y T021-T025, y las tres existen. Los "92" que quedan están en la bitácora, que es histórica.
- **FAQ 12:** los ms Unix cuadran: 10:00 es 1793786400000, 10:05 es 1793786700000, 10:07 es 1793786820000, 10:09 es 1793786940000 y 10:12 es 1793787120000. El 4 de noviembre de 2026 es miércoles, dow 3.
- **Rango de tiempos:** `MIN_EPOCH_MS` = -30610224000000 y `MAX_EPOCH_MS` = 32503680000000 son 1000-01-01 y 3000-01-01. Los `CHECK` de `sql/001_schema.sql` (líneas 92-95, 134, 210-213 y 246) usan la expresión que T093 copia. Con `MAX-1` son 3,25e16 µs, múltiplo de 8, así que la multiplicación `interval * bigint` en doble es exacta. T093 es una comprobación legítima.
- **Cifras de T074** (secuencia FAQ 12, luego 100 repeticiones del mensaje 1, luego la versión tardía):

  | Lectura | received | new | newer | late | redeliv. | conversiones |
  |---|---|---|---|---|---|---|
  | L1 (sesión 1) | 5 | 2 | 1 | 0 | 2 | 5 |
  | L3 (sesión 2: 100 + 1) | 101 | 0 | 0 | 1 | 100 | 101 |

  Ambas cuadran con data-model §4 y con la semántica de FR-023 (los contadores viven en memoria y se pierden al reiniciar). En L1 el estado final son 2 filas actuales y 3 versiones. Tras L3 son 4 versiones, 3 de ellas de E1, y E1 sigue en 4.6 / 1793786940000. Los casos 2 y 3 de T049 y T060 también cuadran: 5 = 7−2, y 7 = 2+1+0+2+0+2.
- **Coherencia de rutas y módulos:** coinciden con plan, data-model y consumer-runtime.
  - Quién emite cada línea de registro: `validation_gap` en `pipeline`, `inconsistent_state` en `writer`, `FAULT` en el hook, `catalog loaded` en `catalog_loader`, `retry` en `resilience` con `OpContext`, y `same_updated_conflict` como única línea WARNING en `reporting`.
  - El orden `write → hook → decisión → commit → contadores` es el mismo en T054, T055, T056 y T059.
  - Hay 7 subcomandos en T073 y 9 ejecuciones en T081.
  - 15 variables pasan a 16 en T010, y el `.env.example` actual tiene 15.
- **CLAUDE.md y alcance:**
  - Los tests, la evidencia y `CODEMAP` van por bloque (T012, T031, T044, T061, T070 y T081). La desviación está declarada como decisión (6).
  - El servicio `tests` y la etapa `test` son infraestructura de pruebas ya justificada en plan §13.1, y no hay nada fuera del brief.
  - T088 vigila contratos, enunciado y `sql/`.
- **¿T093 fuera de orden es defecto real?** No. Está colocado físicamente entre T011 y T012, figura en "Bloque 1 (T001-T012, T093)", y su dependencia (T011→T093, y T093 antes de T021, T023 y T012) está en la sección de dependencias. T012 recoge su evidencia, así que un ejecutor secuencial lo detectaría. Es solo cosmético (ver M-6).

## Hallazgos nuevos (todos MENORES)

| # | Hallazgo | Dónde | Regla o ID |
|---|---|---|---|
| M-1 | El criterio de T001 pide que la búsqueda de `inconsistent_state` en `data-model.md` nombre a `writer.py`. Ese archivo solo dice "estado inconsistente" (§3, línea 72) y T001 no lo edita. Añadir en T001a o T001c la edición de data-model §3, o quitar `data-model.md` del criterio. | tasks.md T001 | FR-003, C2 |
| M-2 | `evidence.record_query` y `record_text` no dicen si sobrescriben o añaden. T039 y T037 llaman varias veces con el mismo nombre (antes y después, una aserción por línea), y T044 espera ambos contenidos. Conviene fijar "añadir, con cabecera por llamada". | T036, T037, T039, T044 | SC-001, FR-034 |
| M-3 | Los tests de integración usan `common/` y `consumer/`, que están copiados en la imagen (`COPY common`, `COPY consumer`). Hay que reconstruir la imagen tras cada cambio en ellos. Solo los "Comandos de referencia" incluyen `build tests`, y los criterios de T043, T058-T060, T066 y T068 no lo repiten. Basta una frase en el criterio común. | tasks.md "Comandos de referencia" y T043 | FR-033 |
| M-4 | Dos tareas dependen de datos que T002 no pide registrar. T007 compara `published:` "respecto a T002", y T086 usa "los mismos archivos de prueba que T002 registró". Añadir a T002 el recuento de `published:` (debería ser 1, solo la API) y la lista de archivos de prueba. | T002, T007, T086 | A1–A12 |
| M-5 | El criterio de T012 dice "7 resultados (más `rango_tiempos_check.txt`)", pero T093 ya es uno de los 7 y ese archivo es su evidencia. Redactar como "7 resultados; T093 aporta además `rango_tiempos_check.txt`". | T012 | FR-034 |
| M-6 | El número 93 fuera de secuencia se mantiene "para no renumerar". El ahorro es mínimo: solo research y plan citan T093, y se puede renumerar con una búsqueda y sustitución. Es válido tal cual, y lo dejo a elección del alumno. Además, CC-DOC prohíbe `print` en `common/` y existe uno heredado de 002 en `common/health.py:86,90` (CLI). T089 lo cubre como "excepción heredada", pero convendría que CC-DOC lo diga. | tasks.md cabecera, CC-DOC, T089 | CC-DOC |

## Decisiones que debe tomar el alumno
1. **Decisión (6) de "Escalados":** confirmar que tests, evidencia y `CODEMAP` se aplican por bloque y no por tarea. Es una desviación literal de CLAUDE.md.
2. **Plan §13.1:** confirmar el servicio `tests` en el perfil `test` y la etapa `test` del `Dockerfile` (el montaje de evidencias en escritura incluido).
3. **T093:** decidir si lo dejas con el número 93 o lo renumeras (M-6).
4. **Comprobaciones de T093 y T037:** son opcionales de confirmar, y se activan solo si fallan. Si el `CHECK` rechaza los extremos del rango, o si la sentencia de cuarentena sin destino exige `SELECT`, se detiene el trabajo y se te escala. No se propone cambiar ningún contrato ni la constitución.
