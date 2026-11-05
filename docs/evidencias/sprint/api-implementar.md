# Resumen fase implementar — api (rama 007-api)

a) Decisiones por defecto: `create_app()` en api/main.py (para pruebas); defectos `${VAR:-valor}` en compose para API_MAX_EVENTS/API_DB_TIMEOUT_SECONDS; comparación en una sola consulta con dos FILTER; `uv run` falla por Python 3.12.16 ausente, se usó el venv con 3.12.
b) Preguntas para el alumno: marcar F1–F8, F10, F11 en el checklist (no marcado por los agentes).
c) Hallazgos: 0 bloqueantes/importantes en los 5 bloques. Límites conocidos: cursor falsificado con t fuera de rango da 500 y con NUL en id da 503; by_hour sin tope en rangos enormes; OPTIONS 405 hasta despliegue; error SQL no previsto sale como 503.
d) Tareas: 25/25 verificadas. Unitarias 731 passed; integración 202 passed. curl real (histórico 18302 y live 173 en 24 h), coherencia en 7 combinaciones contra SQL independiente, 503 con Postgres parado y recuperación sin reiniciar, 404/405/400. Evidencia en docs/evidencias/api/ e informes docs/evidencias/subagentes/verificador-api-bloque{1..5}.md.
e) Efecto lateral conocido: la suite de integración reescribe docs/evidencias/consumidor-idempotente/ (se excluye del commit).
Fase terminada.
