# Bitácora — 005-geografia-pais

| fase | paso | hallazgos | corrección | estado |
|---|---|---|---|---|
| diseno | specify + clarify (disenador A) | 3 preguntas abiertas con decisión provisional (Shapely 2 sin GeoPandas; sin motivo nuevo para `type != earthquake` en el consumidor; catálogo cargado por el consumidor al arrancar) | — | cerrado |
| diseno | plan + tasks + analyze (disenador B) | plan, research, data-model y quickstart; 25 tareas activas en 5 bloques; retoma T062–T067, T069 y T080 de `003`. Analyze: la escena SC-007 de la spec (US1.5) pedía procesar eventos reales con base y Kafka; criterio de una tarea con una tautología; wording de `down -v` | spec US1.5 reformulado a asignación en memoria con feed guardado; T016 y T021 corregidos; estado de la spec actualizado; sin preguntas nuevas | cerrado |
| diseno | decisiones pendientes del alumno | las 3 preguntas de la spec siguen abiertas con su decisión provisional aplicada en el plan; ninguna toca contratos salvo que se cambie la 2 | — | a la espera del alumno |
| implementar | T001–T022 (bloques 1 a 5) | 534 unitarias y 73 de integración sin fallos; `verify_consumer.py geo` 16/16; muestra real de un día: 181 eventos, 153 con país, 28 sin país, 177 `ADM0_A3` únicos en el catálogo | `uv` necesita `UV_PYTHON=3.12` y `uv.lock` pasó a revision 5; el servicio `tests` monta `docs/evidencias/consumidor-idempotente` y la evidencia de geografía se movió a mano | cerrado |
| cierre | T023–T025 (documentación) | `CODEMAP.md`, README, spec (Implemented) y `docs/borradores/geografia-pais.md` actualizados; contratos, `sql/001_schema.sql` y `docs/enunciado` sin cambios; `check_env_example.py` código 0; el grep de atribuciones solo coincide con el texto de T025 en `tasks.md` | — | a la espera de la revisión del alumno |
