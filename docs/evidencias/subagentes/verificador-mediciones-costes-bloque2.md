# Verificación bloque 2 (T079-T083), mediciones-costes

Pruebas ejecutadas por mí: `.venv` pytest tests/scripts -k bench = 43 passed; servicio `tests` con test_bench_ops/storage/schema = 13 passed. Tras ellas `to_regnamespace('bench') is null` = true en la base real.
Diff: solo CODEMAP.md y tasks.md modificados; sql/, contratos, pyproject, uv.lock, compose.yaml y docs/enunciado sin cambios. Módulos <=187 líneas, docstrings en español. Escrituras solo en `bench.`.

| Tarea | Veredicto | Prueba y resultado |
|---|---|---|
| T079 | VERIFICADA | Índices leídos de `pg_indexes` y localizados por columnas, reescritos a `bench.event_N`; se crean/borran de uno en uno con ANALYZE; plan guardado; tabla sin restos |
| T080 | VERIFICADA | 16 mediciones + construcción del dict con planes; list/dict coinciden en presente y ausente |
| T081 | VERIFICADA | Ingenuo y STRtree: 0 puntos distintos en «mixto» y «océano», y en borde/solape (test puro) |
| T082 | VERIFICADA | 12 mediciones y 6 veredictos (Q4 día/todo, Q3 mag4/p99, Q2 mes/rango), un índice cada vez, ids citados |
| T083 | VERIFICADA | Transacción de solo lectura confirmada (`read_only`); índices, tamaño e idx_scan leídos |

Decisiones del implementador frente a FR-005/FR-019: ninguna incumple.
- Índices por columnas: cumple FR-005 («leídas del esquema real, no reescritas a mano»); más robusto que por nombre.
- No concluyente si N<3 o IQR solapados: criterio explicable, FR-005 solo pide un veredicto por índice citando su medición.
- replay.* «no disponible» salvo replay.current_event: coincide con sql/002_roles.sql (api solo tiene SELECT ahí); no escala privilegios. FR-019 (tamaños `pg_total_relation_size`) no es de T083, queda para el bloque de almacenamiento.
Sin hallazgos bloqueantes ni importantes. Límite conocido: con la semilla sintética el veredicto de Q3 mag4 será previsiblemente «no justificado».
