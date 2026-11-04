# Verificación bloques 4 y 5 (T015–T022), productor-live

- T015/T016 VERIFICADA: borrador con B2, B11, B12; cifras (223 ms, 150724 bytes, 210 eventos, api 2.8.2) están en explore_usgs_salida.txt; sin lenguaje de predicción; README con POLL_SECONDS y RAW_RETENTION_DAYS.
- T017 VERIFICADA: ejecuté `pytest -m "not integration"`: 487 passed, 53 deselected. Los 3 archivos de evidencia: 487 passed / 53 passed / PASS check_env, 0 fallos.
- T018 VERIFICADA: ciclo1.log (191 publicados, luego 1, 0) cuadra con 192 reales + 2 replay_demo, 3 ingest_run, 2 raw_response (dedupe por hash), 12 exclusiones (5+7).
- T019 VERIFICADA: tras kill el primer ciclo dio published=0 skipped=192, sin duplicados (current_event 194 estable).
- T020 VERIFICADA: prueba 1 con evento real ok2026vqse (192→193, is_synthetic=f); prueba 2 respaldada por 4 tests de integración (reenvío tras corte ack/marca) más el hecho real del reinicio. Límite: el reenvío no se provocó en vivo, solo en test.
- Base viva ahora: current_event usgs_feed is_synthetic=f = 194, ingest_run 12 (todas 200), raw_response 8, event_version 199; logs del productor con ciclos ok y published 0/1, coherente con la evidencia.
- T021 VERIFICADA: los 19 archivos nuevos aparecen en CODEMAP. Las 3 rutas que no existen (common/geo.py, api/routers/events.py, routers/health.py) ya estaban en CODEMAP antes (futuras features), no son de este bloque. B1, B3–B10 marcadas con evidencia real; B2, B11, B12 sin marcar aunque el borrador las cubre: es defendible, pero podrían marcarse como "borrador listo" al integrarse.
- T022 VERIFICADA: `git diff --stat` sobre contratos 001, sql/001_schema.sql y docs/enunciado vacío; sin .env ni claves en git status; sin contraseñas con valor en las evidencias nuevas.
- Hallazgos: ninguno bloqueante ni importante.
