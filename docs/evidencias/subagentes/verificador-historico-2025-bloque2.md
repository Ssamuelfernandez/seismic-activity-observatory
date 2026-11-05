# Verificación historico-2025 bloque 2 (T005-T009)

Pruebas ejecutadas: `pytest tests/historical` 46 passed; `pytest -m "not integration"` 580 passed; `--help` de download_main OK. `git diff --stat` sobre contratos, sql/001_schema.sql y docs/enunciado vacío.
USGS real (1 count y 1 query con ms en starttime/endtime): count devuelve `{"count":17,"maxAllowed":20000}` y el parser lo lee bien; el formato `...T00:00:00.000` lo acepta (query 200 con FeatureCollection).
Tamaños: todos los archivos <=131 líneas; funciones cortas y con docstring. CODEMAP actualizado (línea 88).

| Tarea | Veredicto | Prueba / resultado |
|---|---|---|
| T005 | verificada | división recursiva (45000 sintético), registros != count lanza con ambas cifras, 1 ms lanza; tests pasan |
| T006 | verificada | 5 intentos (MAX_ATTEMPTS), backoff común, sleep inyectado, error nombra intervalo |
| T007 | verificada | manifiesto parcial por mes, dedup en frontera, CountMismatchError, 2ª ejecución 0 peticiones, force |
| T008 | verificada | gap guardado en `gaps` sin tocar totals, end<=start es ValueError |
| T009 | verificada | CLI con doble sin red, --start sin --end sale con código != 0 |

Hallazgos bloqueantes/importantes: ninguno.
Límite conocido: sin validación en red real del año completo (solo 1 count y 1 query reales).
