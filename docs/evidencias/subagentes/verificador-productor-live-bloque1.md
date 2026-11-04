# Verificación bloque 1 (T001-T005), productor-live

Pruebas ejecutadas por mí: `pytest tests/common tests/producer` = 313 passed; `-m "not integration"` = 470 passed, 35 deselected.
Contratos, sql, 001_schema.sql y docs/enunciado: git diff vacío. Lo puro no importa asyncpg/aiokafka/urllib (grep vacío). config.py = 215 líneas.

| Tarea | Veredicto | Prueba y resultado |
|---|---|---|
| T001 | VERIFICADA | defaults 60/10/7, POLL_SECONDS=61 con latido 120 falla con "POLL_SECONDS", URL sin esquema y RAW_RETENTION_DAYS=0 fallan; MIN/MAX_PRODUCER_* eliminadas |
| T002 | VERIFICADA | JSON roto, [], {} sin features, features [] válido, hash estable ante orden de claves, cambia con `updated` |
| T003 | VERIFICADA | una prueba por fila de research §3; invalidez antes que tipo (coherente con kafka-message §3) |
| T004 | VERIFICADA | sobre exacto, ingested_at con Z, clave None sin id; ejemplo de §4 pasa por decode_value/validate_message sin Rejection |
| T005 | VERIFICADA | secuencia 2,4,8,16,32,60,60 con jitter 1; factor 0,5 con jitter 0; fallos 0 devuelve 0; tope 60 |

producer/loop.py y tests/producer/test_loop.py: cambio mínimo y aceptable (solo sustituye las constantes eliminadas por load_feed_settings/validate_poll_against_health; el test cambia ValueError por ConfigError y el nombre de variable). Es transitorio hasta T011.

Hallazgos bloqueantes/importantes: ninguno.
Límite conocido: el test de config antiguo aún usa el nombre PRODUCER_INTERVAL_SECONDS solo con read_int genérico (inocuo).
