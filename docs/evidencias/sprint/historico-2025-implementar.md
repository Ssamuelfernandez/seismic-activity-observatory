# historico-2025 — fase implementar (resumen)

**a) Decisiones por defecto**
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Q en la verificación | `verify_load` toma Q (cuarentena) de los resultados de `process_record` de la misma carga | `observatory_consumer` solo tiene INSERT en `live.quarantine` (002_roles.sql); no se toca el rol | sí |
| Huella | la de producción cubre `current_event` y `event_version`; con `quarantine` la calcula el administrador | mismo permiso | sí |
| Milisegundos en URL | `build_query_url` los incluye solo si hay fracción; probado contra USGS real | intervalos de partición recursiva | sí |
| Versionado de datos | 13,9 MB < 50 MB → `data/historical/` versionado con manifest (incluye archivo de hueco del ensayo) | regla del brief | sí |
| `common.geo` en load_main | solo para cablear `PipelineDeps` como `consumer/loop.py` | excepción acotada en T017 | sí |

**b) Preguntas para el alumno**: GRANT SELECT sobre `live.quarantine` a `observatory_consumer` (daría verificación exacta de Q; cambia roles; recomendación: no, basta lo implementado).

**c) Hallazgos**: 0 importantes en los 5 bloques. Menores: `docker compose build consumer` no hace nada (usar `build producer`); en Git Bash hace falta `MSYS_NO_PATHCONV=1`; `carga1.out` sin `new=18302` (imagen vieja en la 1.ª carga real; idempotencia y recuento sí constan); evidencia TDD "falla antes" solo en T010–T011 y bloque 1–2 parcial. Accidente: 7 archivos de `docs/evidencias/consumidor-idempotente/` reescritos por ejecuciones del servicio `tests`; se excluyen del commit; restaurar con `git checkout -- docs/evidencias/consumidor-idempotente`.

**d) Tareas**: 25/25 verificadas (5 bloques, un verificador por bloque, 0 vueltas de corrección). 609 unitarias y 85 integración. Datos reales: 18302 eventos únicos = count USGS; en BD 18302 `usgs_historical`, cuarentena 0; recarga y reinicio sin cambios (md5 idéntico); ensayo de hueco 2025-12-30/31 sin cambios. Contratos, sql/001_schema.sql y enunciado sin diff.

**e) Comprobar**: informes en docs/evidencias/subagentes/verificador-historico-2025-bloque{1..5}.md; evidencias en docs/evidencias/historico-2025/.

Fase terminada.
