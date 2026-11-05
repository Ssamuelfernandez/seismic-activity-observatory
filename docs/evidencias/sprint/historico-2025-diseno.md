# historico-2025 — fase diseno (resumen)

**a) Decisiones por defecto**
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| source del histórico | `usgs_historical` (el brief decía `historical`) | CHECK de sql/001_schema.sql y contratos | sí |
| Lote vs Kafka | lote directo a `live` | kafka-message.md §1 y db-schema.md §1 | sí |
| Reutilizar procesamiento | cargador llama a `consumer.pipeline.process_record` con RawRecord(partition=None, offset=None); `MessageRef.partition/offset` admiten None (common/transform.py, common/quarantine_row.py, logs %d→%s) | cambio mínimo, sin duplicar lógica; kafka_* son nullable en el esquema | sí |
| Hueco >24 h (B12) | `--start/--end` en el descargador → `usgs_gap_<start>_<end>.geojson` en `gaps` del manifiesto | procedimiento reproducible con el mismo mecanismo | sí |
| Ubicación y versionado | `data/historical/`; versionar si <50 MB (se mide en T019), si no .gitignore | regla del brief | sí |
| Dedup | por `id`, conserva `updated` mayor; sin id/updated → cuarentena | evita perder/duplicar | sí |
| Mes >20000 | partición recursiva por punto medio, fusionado en el mismo archivo mensual | brief | sí |

**b) Preguntas para el alumno** (provisionales aplicadas): 1) `--start/--end` (recomendado sí); 2) versionar o no los archivos según tamaño real; 3) cambio mínimo en código compartido (MessageRef None).

**c) Hallazgos**: 0 importantes. Menores: 2 límites conocidos (T010 antes de T011; carrera count/descarga se resuelve con error y repetición).

**d) Tareas**: 25 activas en 5 bloques (piezas puras 4; descarga simulada 5; carga y aceptación con PG 9; datos reales 3; cierre 4). Informe: docs/evidencias/subagentes/plan-reviewer-historico-2025.md.

**e) Comprobar**: specs/006-historico-2025/ (spec, plan, research D1 y D10, tasks). Contratos, enunciado y sql/001_schema.sql sin cambios.

Fase terminada.
