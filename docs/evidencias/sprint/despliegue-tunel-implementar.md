# Resumen fase implementar — despliegue-tunel (rama 010-despliegue-tunel)

Tareas T059–T071 verificadas por el verificador (T072, cierre y CODEMAP, se hace en la fase cierre). Contratos, sql/001 y enunciado sin cambios.

## Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Búsqueda de secretos (T066.3) | por patrones genéricos, sin leer .env (desviación de la tarea) | el alumno prohíbe manejar .env reales; el clasificador bloqueó la lectura | sí |
| limit>5000 | 400 invalid_parameter (no recorte) | lo dice contracts/api.md §3.1; F5 es el máximo de 5000 | sí |
| httpx en .venv | instalado en el venv local (uv pip install httpx==0.28.1); no cambia el repo | faltaba para tests/api; uv sync no encuentra Python 3.12.16 | límite |
| Corrección de docs | 02 y 03 §8.4: publish=dist con base=frontend; 03 §4 nota carpeta real 010; README "Sin CORS" actualizado | coherencia | sí |

## Hallazgos de exposición (T066/T067)
Sin rutas de administración ni escritura (12 combinaciones → 405); /docs, /redoc, /openapi.json → 404; 0 coincidencias de secretos por patrones; sin limit → 5000 con truncated y next_cursor; compose publica solo 127.0.0.1:8000. Hallazgo local: compose.override.yaml publica Postgres en 127.0.0.1:5433 (ignorado por git; retirar antes de abrir el túnel).

## Tareas
Verificadas: T059–T071. Pendiente: T072 (cierre). Pasos manuales P1–P9 del alumno.
Pruebas: 776 sin Docker, 73 vitest, 121 integración API, check_env_example PASS, 5 servicios healthy.
Límites: 500 sin cabeceras CORS; preflight POST 400; check-dist solo mira .js.

Fase terminada.
