# Verificación productor-live, bloque 2 (T006-T009)

| Tarea | Veredicto | Prueba ejecutada |
|---|---|---|
| T006 | VERIFICADA | GRANT SELECT, INSERT, DELETE en sql/002_roles.sql; build tests y test_roles.py pasan en Docker; `git diff` de specs/001, 001_schema.sql y docs/enunciado vacío |
| T007 | VERIFICADA | tests/producer/test_usgs_client.py (200, 500/429, lento status=None, servidor apagado) incluido en 475 unitarias OK |
| T008 | VERIFICADA | Integración: 9 passed (roles + producer_store: mismo hash 2 runs/1 raw, exclusión repetida 1 fila, mark_published no retrocede, purga conserva la última, fallo con status/sha nulos). SQL solo en producer/ingest_queries.py |
| T009 | VERIFICADA | check_env_example.py rc=0 (19 vars, 17 leídas); `docker compose --env-file .env.example config -q` rc=0; grep PRODUCER_INTERVAL_SECONDS en .env.example/compose/common/producer/scripts vacío |

Unitarias: 475 passed, 43 deselected. Restaurado docs/evidencias/consumidor-idempotente tras la integración.
config.md (specs/002): no es contrato prohibido; CLAUDE.md protege solo specs/001-.../contracts/ y T009 pide expresamente editarlo. Cambio coherente (A, B, D, E).
Hallazgos bloqueantes/importantes: ninguno. Límite conocido: el GRANT nuevo requiere reaplicar roles en bases ya creadas (quickstart §0).
