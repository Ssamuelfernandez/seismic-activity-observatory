# Verificación bloque 1 (T001–T004) historico-2025

Ejecutado por mí: `pytest tests/historical -q` = 20 passed; `pytest -m "not integration" -q` = 554 passed, 73 deselected. `git diff --stat` sobre contratos, sql/001_schema.sql y docs/enunciado: vacío. Solo cambia CODEMAP.md (fila nueva con historical/, tests y B13–B16) más archivos nuevos en historical/, tests/historical/ y evidencias.

| Tarea | Veredicto | Comprobación |
|---|---|---|
| T001 intervals | VERIFICADA | 12 meses contiguos UTC, el último termina en 2026-01-01; split por punto medio; la URL lleva minmagnitude=4, eventtype, orderby, format, starttime y endtime |
| T002 dedup | VERIFICADA | Mayor `updated` gana, empate conserva la primera, sin id o updated no entero pasa sin agrupar, vacío da vacío; `discarded` cuenta bien |
| T003 manifest | VERIFICADA | Estructuras de data-model §3, sha256, escritura atómica (tmp + os.replace), lectura, `verify_file` con error que nombra el archivo |
| T004 envelope | VERIFICADA | Campos del contrato, bytes deterministas, `ingested_at` con Z; la prueba usa `common.validation.validate_message` real con `earthquakes.live` |

CC-DOC/CC-14/CC-MAP: docstrings en español con plantilla, constantes con nombre, CODEMAP.md actualizado, evidencia en docs/evidencias/historico-2025/ (falla antes + pasa). No hay secretos.

Hallazgos bloqueantes o importantes: ninguno.
Límite conocido: `month_intervals` formatea sin milisegundos, suficiente para los meses; los intervalos de 1 ms de T005 deberán tratarse en ese bloque.
