# Verificación bloque 1 (T073-T078), mediciones-costes

Pruebas ejecutadas por el verificador (servicio `tests`, sin down -v ni --build):
- Unitarias test_bench_* (stats, measure, hardware, seed, synth, sql_static): 29 passed.
- Integración tests/integration/test_bench_schema.py: 8 passed.
- Tras los tests, to_regnamespace('bench') IS NULL = true en la base real.
- git: sin cambios en specs/, sql/, pyproject.toml, uv.lock ni docs/enunciado; solo CODEMAP.md (+1 línea) y archivos nuevos.
- bench_schema.py: toda escritura califica con `bench.`; DROP en `finally` (bench_session); SIGTERM -> cancelación; aborta sin marca o sin --clean. Archivos <=187 líneas.

| Tarea | Veredicto |
|---|---|
| T073 | VERIFICADA |
| T074 | VERIFICADA |
| T075 | VERIFICADA |
| T076 | VERIFICADA |
| T077 | VERIFICADA |
| T078 | VERIFICADA |

Hallazgos bloqueantes/importantes: ninguno.
Límite conocido: en Windows no hay manejador SIGTERM (solo corre en Docker/Linux, donde sí aplica).
