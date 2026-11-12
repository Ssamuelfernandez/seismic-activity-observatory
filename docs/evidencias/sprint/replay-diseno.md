# Resumen fase diseño — replay (rama 009-replay)

Artefactos: specs/009-replay/{spec,plan,research,data-model,quickstart,tasks,bitacora}.md. Revisión: docs/evidencias/subagentes/plan-reviewer-replay.md (0 bloqueantes/importantes). Contratos, sql/001 y enunciado sin cambios.

## Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Consumidor | un proceso, dos topics (KAFKA_CONSUMER_TOPICS), grupo consumer-live | pipeline ya enruta por topic_mode; sin servicios nuevos | sí |
| Compose | volumen ro data/historical en producer; sin servicios nuevos | mantiene los 5 servicios | sí |
| Velocidad | --interval segundos (def. 2), no --speed | --speed 2 se leería "doble de rápido"; 03 §8.5 lo actualiza el alumno | sí |
| Duplicados/revisiones | 6 mensajes sintéticos (synthetic-replay-e1/e2, is_synthetic) | forzar versiones de evento real lo marcaría sintético (§7) | sí |
| Zona | chile-norte N=20 (2025-01-01..29, M4.0–6.1) | 18 Chile, 1 Bolivia, 1 sin país | sí |
| Recuentos | 26 publicados, 22 current, 24 versions, 0 cuarentena | secuencia FAQ 12 | sí |
| Live no cambia | se comprueba con el productor live parado | USGS real seguiría ingiriendo | sí |
| Panel | no se toca salvo fadeByAge ilegible (T056) | alcance | sí |

## Preguntas para el alumno
Confirmar las 5 decisiones; validar zona; actualizar 03 §8.5.

## Tareas
18 activas (T041–T058) en 5 bloques. Límites conocidos en research.md D11.
Menores: spec "Status: Draft"; T053 depende de que existan las métricas de reenvío en el log del consumidor.

Fase terminada.
