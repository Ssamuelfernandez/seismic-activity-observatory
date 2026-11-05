# Verificación bloque 4 api (T017-T020)
- Unitarios: `pytest -m "not integration" -x -q` -> 731 passed.
- Integración (solo 4 archivos): 54 passed.
- `git diff --stat` sobre contracts/, docs/enunciado/, sql/001_schema.sql: vacío.
- Código de /api/salud y errores coincide con api.md §4 y §6 (status/last_ingestion/generated; 400/404/405+Allow/503/500 con cuerpo común, sin detail). El 500 solo registra el tipo de excepción; tests comprueban ausencia de traza/SQL en cuerpos.

| Tarea | Veredicto | Motivo |
|---|---|---|
| T017 | VERIFICADA | tests de salud pasan: null sin ingestas, ms, sin conexión, ignora mode |
| T018 | VERIFICADA | 503 database_unavailable en los 3 endpoints < 10 s, recuperación sin reinicio |
| T019 | VERIFICADA | 400/404/405 sin 422, rutas = 3 GET, 500 sin traza ni SQL |
| T020 | VERIFICADA | INSERT/UPDATE/DELETE denegados con rol real; prueba estática de SQL pasa |

Sin hallazgos bloqueantes ni importantes. Límite conocido: no se ejecutó la suite completa de integración (por indicación).
