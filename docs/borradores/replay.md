# Borrador: replay (J1–J8, G10, F12, G12 `metadata.mode`; prueba 11)

Material para la memoria y la defensa. Feature `replay` (`specs/009-replay/`), estado Implemented. Resultados observados con contenedores y panel al final; evidencias en `docs/evidencias/replay/`.

## Qué hace

Un comando (`python -m producer.replay`) lee del histórico de 2025 (`data/historical/`, sha256 verificado) los 20 primeros eventos de una zona, ordenados por fecha, y los publica en `earthquakes.replay` a un intervalo fijo (2 s). Después publica un bloque controlado de 6 mensajes. El consumidor los guarda en el esquema `replay`, la API los sirve con `mode=replay` (`metadata.mode = "replay"`) y el panel los muestra con el banner «REPRODUCCIÓN» (J1, J4, F12, G10, G12). El tiempo original no se toca y se añade `replay_at`, el instante de publicación (J2, J7).

## Selección y su porqué (J1)

Zona `chile-norte` (lat −27 a −18, lon −72 a −68,5): 267 eventos en 2025; los 20 primeros por `(time, id)` van del 2025-01-01 08:08 al 2025-01-29 03:44 UTC. País reconocible (Chile 18, Bolivia 1, sin país 1). Japón-Honshu queda como segunda zona, pero 9 de 20 caen en el mar. El orden determinista hace el replay repetible y fija las cifras esperadas.

## Bloque controlado (J6)

Dos eventos sintéticos (`synthetic-replay-e1/e2`, `is_synthetic = true`, 2025-01-30) con la secuencia: E1 v1, E1 v1, E1 v2 (`updated` 10:09), E1 v1 tarde, E2, E1 intermedia (10:07). Se fabrican porque forzar dos versiones de un evento real obligaría a marcar como sintético un dato real.

| Medida | Esperado (SC-001) | Observado (T057) |
|---|---|---|
| Mensajes publicados | 26 | 26 (20 reales + 6 del bloque) |
| `replay.current_event` | 22 | 22 |
| `replay.event_version` | 24 | 24 |
| `replay.quarantine` | 0 | 0 |
| Reenvíos ignorados | 2 | 2 |
| Versiones posteriores | 1 | 1 |
| Antiguas tardías | 1 | 1 |
| E1 conserva `updated` | 10:09, 3 versiones | 10:09, 3 versiones |
| Duración con `--interval 2` | unos 52 s (< 90 s) | 51 s |

## Aislamiento (J3, J5)

Tres capas: el productor de replay solo conoce `earthquakes.replay`; el consumidor deriva el esquema del topic y lo guarda solo en `replay`; y la comprobación `mode` ↔ topic envía a cuarentena (`mode_topic_mismatch`) un mensaje con modo equivocado. Demostración: parar el productor live y comparar recuentos y huella `md5` de las tablas `live` antes y después (SC-002). Se reutiliza todo el procesamiento de `common/` y `consumer/`: el replay no llama a `process_record`, publica en Kafka (J5).

## Decisiones (D1 a D9)

- D1: un único consumidor suscrito a los dos topics (`KAFKA_CONSUMER_TOPICS`), sin segunda instancia ni servicio nuevo.
- D2: volumen de solo lectura de `data/historical/` en el servicio `producer`; el `Dockerfile` no cambia.
- D3: `--interval` en segundos (no `--speed`, para que 2 no se lea como «el doble de rápido»).
- D4: `chile-norte` y 20 eventos, elegidos inspeccionando los archivos reales.
- D5: se reutilizan manifiesto, deduplicación, publicador y temas; lo nuevo es lógica pura (mensaje, selección) separada de la E/S (lectura, publicador, CLI).
- D6: bloque controlado de 6 mensajes con ids sintéticos.
- D7: `source = replay_demo`; `ingested_at` = extracción del archivo (reales) o arranque (sintéticos); `replay_at` por mensaje.
- D8: aislamiento comprobable con el productor live parado.
- D9: el panel no se toca salvo que `fadeByAge` deje ilegibles los puntos de 2025 (se decide en T056).

## Límites conocidos

No hay borrado de tablas de replay (recrear el volumen); velocidad fija, no proporcional; selección fija; grupo `consumer-live` con dos topics; `KAFKA_TOPIC` ya no suscribe al consumidor; bloque de 6 mensajes frente a los 5 de la FAQ 12; `config.md` de `002` no refleja la variable nueva; `verify_stack.py` 14/16 por un `compose.override.yaml` local (puerto 5433) ajeno a la feature; `uv run` no funciona en el equipo (se usó `.venv` y el servicio `tests`); panel verificado solo con Edge headless por CDP, sin la extensión de Chrome; el replay no usa `usgs_gap_*` (research D10).

## Preguntas de defensa

- ¿Cómo sabes que el replay no contamina `live`? Topic distinto, esquema distinto, comprobación de modo y huella de las tablas `live` idéntica con el productor live parado (SC-002).
- ¿Qué pasa si se repite o se interrumpe? Es idempotente: todo son reenvíos y `replay_at` no cambia (SC-006, J6).
- ¿Por qué eventos sintéticos para las revisiones? Para no alterar ni marcar como sintético un dato real (constitución §7); llevan prefijo `synthetic-replay-` y `is_synthetic = true`.
- ¿Se alteran las fechas? No: `time` y `updated` salen tal cual del archivo; la API los devuelve iguales (J2, J7, SC-003).
- ¿Y si falta o se altera un archivo? Código 1, nombra el archivo y no publica nada (FR-018).
- ¿El panel calcula algo? No; muestra `metadata.mode` y lo que devuelve la API (G12, constitución §17).

## Resultados observados (T057)

Recorrido real con contenedores (T052 a T056), 2026-11-12. Con el productor live parado, las tablas de `live` tenían 211 filas en `current_event`, 211 en `event_version` y 0 en cuarentena, con la misma huella `md5` antes y después del replay y tras repetirlo (SC-002, `T053_despues.out`, `T054_repeticion.out`). Repetir el replay dejó 22 / 24 / 0 y los mismos `replay_at` (SC-006). Con una copia con un byte alterado el comando falla sin publicar (FR-018). La API devolvió `metadata.mode = "replay"` y 22 eventos con sus fechas originales; sin `mode` no sale ninguno de replay (`T055_comprobacion.txt`). El panel mostró el banner «REPRODUCCIÓN» y 22 eventos (`T056_panel.md`). Regresión (`T057_*.txt`): 756 pruebas unitarias y 210 de integración en verde; `check_env_example.py` en verde; `verify_stack.py` 14 de 16, con los dos fallos por el `compose.override.yaml` local que publica PostgreSQL en 127.0.0.1:5433 (no es del replay).
