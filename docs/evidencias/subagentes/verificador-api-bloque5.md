# Verificador api, bloque 5 (T021-T025)
- Unitarias: 731 passed, 202 deselected. T025_integracion.txt revisada: 202 passed.
- curl real (8000): eventos, estadisticas, salud, mode=replay (0 eventos, mode=replay), 404 y 405 (Allow: GET) correctos.
- SQL admin independiente: 2025-03 jpn mag>=4: 16 = API (eventos y estadisticas). Ultimas 24 h mag>=2: 62 = API.
- postgres stop: los tres endpoints 503 database_unavailable en ~4 s; tras start, 200 sin reiniciar la API. Stack arriba y healthy.
- git diff --stat de contratos, enunciado y sql/001_schema.sql: vacio. Evidencias api/ presentes, sin secretos.
- CODEMAP recoge todos los archivos nuevos; README tiene la seccion "API de consulta".
- Hallazgos: ninguno bloqueante ni importante. Limite: checklist F1-F11 sigue con casilla vacia (no verificado que T025 las marque).
T021-T025: VERIFICADAS.
