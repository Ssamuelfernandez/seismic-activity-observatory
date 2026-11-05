# Resumen fase diseno — api (rama 007-api)

a) Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| P1 CORS / F9 | fuera de la feature; OPTIONS da 405 hasta despliegue | el brief lo aplaza | sí |
| P2 rango por defecto en replay | mismas 24 h en ambos modos | api.md no distingue el modo | sí |
| P3 variables API_MAX_EVENTS (5000) y API_DB_TIMEOUT_SECONDS (5) | en .env.example y README, sin editar config.md de 002; anotadas en decisiones.md (T024) | no tocar contratos de 002 | sí |
| D1 validación | código propio, sin 422 | un solo cuerpo de error, mensajes en español | sí |
| D2 consistencia | transacción REPEATABLE READ de solo lectura por petición | total coherente con el escritor activo | sí |
| D6 paginación | cursor por (event_time, event_id) en base64url | estable ante inserciones | sí |
| D7/D8 errores BD | RETRIABLE_DB_ERRORS → 503; error SQL no previsto también 503 | simplicidad | sí |
| replay | lee replay.current_event (vacío hasta la feature replay) | sin reescribir la API después | sí |

b) Preguntas para el alumno: P1, P2, P3 (provisionales arriba). Recomiendo mantenerlas.
c) Hallazgos: plan-reviewer sin bloqueantes ni importantes. El analyze corrigió 5 cosas (openapi.json expuesto, httpx fuera del lock, orden de ApiError, servicio api en compose, F1–F11 vs F9). Menores: 0 listados.
d) Tareas: 25 en 5 bloques (5, 6, 5, 4, 5), ninguna ejecutada aún.
e) El alumno debe comprobar P1–P3 y que despliegue cubra F9.
Fase terminada.
