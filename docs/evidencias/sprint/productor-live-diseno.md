# Resumen fase `diseno` — productor-live (rama 004-productor-live)

## a) Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Feed | `all_day.geojson`, configurable (`USGS_FEED_URL`) | enunciado §4.1, B12 | sí |
| Hash de raw_response | sobre `features` en JSON canónico, no el cuerpo | `metadata.generated` cambia cada minuto | sí |
| Retención raw_response | 7 días (`RAW_RETENTION_DAYS`), purga tras ciclo correcto, conserva la última fila | db-schema §3.9 delega en la feature | sí |
| Backoff | exponencial con jitter, 2 s → 60 s; timeout HTTP 10 s | < latido máx. 120 s | sí |
| Latido | se renueva al completar ciclo (también con fallo controlado de USGS); no con fallo de Kafka/PG | — | sí |
| Fallo de Kafka a mitad de ciclo | se corta en el evento fallido; los confirmados quedan marcados; solo log, sin segunda fila en ingest_run | ack antes de marca | sí |
| Eventos sin id/updated | se publican sin marca en ingest_state (límite conocido: se republican cada ciclo) | kafka-message §3 | sí |
| Variable | `PRODUCER_INTERVAL_SECONDS` → `POLL_SECONDS` (60) | brief | no |
| Dependencias | ninguna nueva: urllib en hilo, mock con http.server | constitución §11 | sí |
| CODEMAP | se actualiza una sola vez (T021), desviación declarada de CLAUDE.md | proporcionalidad | sí (pide confirmación) |

## b) Preguntas para el alumno (decisión provisional entre paréntesis)
1. Retirar sintéticos del productor y adaptar check A1 de `scripts/verify_stack.py` a `is_synthetic=false` (sí; se conserva `common/synthetic_event.py`).
2. `GRANT SELECT, DELETE` sobre `ingest.raw_response` en `sql/002_roles.sql` (no es contrato) (sí). ¿Añadir línea en `db-schema.md` §1.1? El revisor indica que no es conflicto, solo sincronía de redacción; NO se edita el contrato (provisional: no tocar).
3. Retención 7 días y hash sobre `features` (se mantienen).
4. Fallo de Kafka solo en log (se mantiene).
5. Un volumen PostgreSQL ya creado necesita reaplicar el GRANT (quickstart §0) o `down -v`.
6. Desviación CODEMAP al final de la feature (T021).

## c) Hallazgos
Revisión: 0 bloqueantes, 0 importantes. Menores: 1 (límite conocido: timeout urllib por operación de socket). Sin ronda de corrección. Contratos, sql/001_schema.sql y docs/enunciado/ intactos.

## d) Tareas
22 activas en 5 bloques (tope 25/5): B1 config+puras T001–T005; B2 HTTP/PG/permisos T006–T009; B3 ciclo/bucle/fallos T010–T014; B4 docs T015–T016; B5 real+evidencias+CODEMAP+parada T017–T022. Ninguna implementada aún.

## e) Qué comprobar
spec.md (Clarifications), plan.md §5, tasks.md (tabla de trazabilidad). Informe: docs/evidencias/subagentes/plan-reviewer-productor-live.md.

Fase terminada.
