# geografia-pais — fase diseno (resumen)

Rama 005-geografia-pais (desde main). Artefactos en specs/005-geografia-pais/: spec, plan, research, data-model, quickstart, tasks (25 tareas, 5 bloques), bitacora.
plan-reviewer: sin bloqueantes ni importantes (docs/evidencias/subagentes/plan-reviewer-geografia-pais.md). Diff de contratos vacío.

## Decisiones por defecto
| Pregunta | Decisión | Motivo | ¿Defender? |
|---|---|---|---|
| Librería de geometría | Shapely 2 sin GeoPandas (STRtree, covered_by) | Ligera, sin pandas; el roadmap citaba GeoPandas | Sí |
| type != earthquake en consumidor | Sin motivo nuevo de cuarentena; se demuestra en productor (exclusion) | kafka-message.md §3/§6 no lo definen; no tocar contrato | Sí |
| Carga del catálogo | En el consumidor al arrancar | db-schema.md §1.1 | Sí |
| Frontera | El borde cuenta como dentro (covers) | Roadmap F5 | Sí |
| Empates | Menor ADM0_A3 + log country_tie | Determinista | Sí |
| Sin polígono | country_id NULL, sin cuarentena, cuenta en totales | Prueba 7 | Sí |
| Filas previas | Sin recálculo retroactivo (límite conocido) | Alcance | No |
| Pruebas 003 contrarias | T010 reescribe dos pruebas existentes | Cambia el comportamiento esperado | Sí |

## Preguntas para el alumno
Las tres primeras filas, con decisión provisional aplicada. Cambiaría contrato solo si se quiere rechazar type != earthquake en el consumidor.

Fase terminada.
