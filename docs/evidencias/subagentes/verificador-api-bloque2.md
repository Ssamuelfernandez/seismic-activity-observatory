# Verificación api, bloque 2 (T006-T011)
Pruebas ejecutadas por mí: `pytest -m "not integration" -x -q` -> 719 passed; integración de los 4 archivos del bloque -> 38 passed. `git diff --stat` sobre contracts/, docs/enunciado/, sql/001_schema.sql -> vacío.
Ataque contra BD real (script temporal en el scratchpad, fuera del repo): country_id `x' OR '1'='1`, `ESP'; DROP TABLE...`, NUL -> 400; mode/min_mag/limit maliciosos -> 400; cursor con `id="a' OR 1=1--"` -> 200 sin efecto (parámetro `$n`, tablas intactas). Paginación de 40 eventos con tiempos repetidos y limit 1,3,7,40,41 -> siempre 40 ids, 0 repetidos.

| Tarea | Veredicto | Motivo |
|---|---|---|
| T006 serializers | VERIFICADA | tests unitarios pasan; forma de feature/metadata según api.md |
| T007 sql_filters | VERIFICADA | solo `$n`; esquema de lista cerrada; sin inyección demostrada |
| T008 db_access/queries | VERIFICADA | REPEATABLE READ readonly; test_api_queries pasa ([start,end), nulos, revisión, orden) |
| T009 router eventos | VERIFICADA | 24 h por defecto, metadata de 8 campos, vacío, nulos, país: tests pasan |
| T010 paginación | VERIFICADA | 25 eventos en 10/10/5, sin pérdidas ni duplicados, 400 en limit/cursor mal formados |
| T011 replay | VERIFICADA | replay vacío 200 con features [], aislamiento live/replay, mode inválido 400 |

Hallazgos bloqueantes/importantes: ninguno.
Límite conocido (menor): un cursor falsificado con `t` fuera de rango (p. ej. 10^20) da 500 y con `\u0000` en `id` da 503; no afecta a cursores emitidos por la propia API.
