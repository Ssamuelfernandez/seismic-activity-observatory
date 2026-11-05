# Verificación api bloque 3 (T012-T016)
- Unitarios: 731 passed (not integration). Integración (4 archivos): 24 passed.
- git diff --stat sobre contracts/, docs/enunciado/, sql/001_schema.sql: vacío.
- Coherencia contra la BD real (histórico 2025, API reconstruida): total estadísticas == metadata.total == suma by_hour == suma by_country en 6 combinaciones (409, 409 con min_mag, 207 none, 1 USA, 0 JPN M5, rango con horas parciales 93). Live 24 h está vacío en la BD; no se probó con datos vivos reales.
- Forma de /api/estadisticas revisada contra api.md §5.1: metadata, period, filters, total, by_hour, by_country, histograms, comparison; replay -> comparison null (comprobado en real).
- T012 VERIFICADA; T013 VERIFICADA; T014 VERIFICADA; T015 VERIFICADA; T016 VERIFICADA.
- Sin hallazgos bloqueantes ni importantes.
- Nota: la imagen `seismic-observatory-python` estaba obsoleta (el servicio api devolvía 404 en /api/estadisticas); la reconstruí con `docker compose build producer` y recreé `api`.
