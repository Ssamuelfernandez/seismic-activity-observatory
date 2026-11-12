# Plan de implementación: replay (009)

**Rama**: `009-replay` | **Fecha**: 2026-11-12 | **Spec**: `specs/009-replay/spec.md`
**Requisitos**: F9, J1 a J8, G10, F12, G12 (`metadata.mode`), prueba 11.

Solo documentos de diseño (constitución §19). Los contratos de `specs/001-contratos-y-modelo/contracts/` se citan, no se copian ni se modifican. Es trabajo de clase: se corrige lo que haga fallar un criterio de aceptación, contradiga un contrato o la constitución, pierda o duplique datos; lo demás va como límite conocido de una línea.

## Resumen

Un productor de replay (`producer/replay.py`, CLI, lanzado con `docker compose run --rm producer`) lee 20 eventos reales de una zona (por defecto Chile norte) de `data/historical/`, verifica su sha256, los ordena por fecha, añade un bloque controlado de 6 mensajes sobre dos eventos sintéticos (secuencia de la FAQ 12) y los publica en `earthquakes.replay` con `mode = replay`, `source = replay_demo` y `replay_at`, uno cada 2 s. El consumidor existente, suscrito ahora a los dos topics, los lleva al esquema `replay` con el mismo procesamiento. La API y el panel ya sirven y muestran `mode=replay`; esta feature los verifica con datos reales.

No hay cambios de contrato, de esquema SQL ni de `docs/enunciado/`. Decisiones y alternativas: `research.md` (D1 a D11).

## Technical Context

| Pieza | Valor |
|---|---|
| Lenguaje | Python 3.12.16 (la imagen compartida); `aiokafka` y `argparse` (biblioteca estándar); sin dependencias nuevas |
| Almacenamiento | PostgreSQL 16, esquema `replay` ya existente |
| Mensajería | Kafka, topic `earthquakes.replay` (1 partición, 7 días) |
| Pruebas | `pytest` sin Docker para lo puro; integración con el servicio `tests` y el recorrido real con Compose |
| Rendimiento | 26 mensajes a 2 s = unos 52 s (SC-007: menos de 90 s) |
| Restricciones | Una feature cada vez; sin servicios nuevos en Compose (FR-020); código nuevo con docstrings de `03 §7.4`, funciones de unas 30 líneas y archivos de 250 como máximo |

## Constitución (comprobación)

| Principio | Cumple | Cómo |
|---|---|---|
| §1 Al menos una vez e idempotente | Sí | El consumidor no cambia; el replay confirma cada envío y repetirlo solo produce reenvíos |
| §2 Versionado por `updated` | Sí | Lo decide `common/processing.py`; el bloque controlado lo demuestra |
| §3 y §5 Tiempos y nulos | Sí | `event` se publica sin tocar; `time` y `updated` originales |
| §4 País por geometría | Sí | Lo asigna el consumidor |
| §7 Sintéticos separados | Sí | Solo `synthetic-replay-e1/e2`, con `is_synthetic = true` |
| §9 Nombres de servicio | Sí | `kafka:9092` del entorno |
| §10 Secretos y `.env.example` | Sí | Una variable nueva sin secretos, añadida a `.env.example` |
| §11 Versiones fijadas | Sí | Sin dependencias nuevas |
| §12 Alcance cerrado | Sí | Sin servicios ni paneles nuevos |
| §13 Idioma | Sí | Identificadores en inglés; docs en español |
| §14 Una responsabilidad; puro separado del I/O | Sí | Selección y armado de mensajes puros; ficheros y Kafka en módulos aparte |
| §15 Contratos únicos | Sí | Solo se citan |
| §16 Cierre | Sí | Último bloque: evidencia, README y `CODEMAP.md` |
| §17 Frontend sin cálculo | Sí | No se toca el panel |
| §19 Una feature, plan antes de código | Sí | Este plan; tareas revisables en `tasks.md` |

Sin violaciones que justificar.

## Cambios por archivo (diseño)

### Código nuevo

| Archivo | Contenido | Puro |
|---|---|---|
| `common/replay_message.py` | `SOURCE_REPLAY`, `MODE_REPLAY`, `ReplayItem`, `build_replay_message(item, replay_at)`, `build_controlled_block(started_at)` (los 6 elementos de `data-model.md`) | Sí |
| `producer/replay_selection.py` | `Zone`, `ZONES`, `select_events(pairs, zone, count)` sobre pares `(feature, extracted_at)`; orden `(time, id)`, ids únicos | Sí |
| `producer/replay_source.py` | Verifica el sha256 de los archivos del manifiesto, lee y deduplica; `ReplaySourceError` que nombra el archivo | I/O (disco) |
| `producer/replay_runner.py` | Publica los elementos en orden: `ensure_topics`, `start_producer`, `publish_message` al topic `earthquakes.replay`, `asyncio.sleep(interval)` entre mensajes, resumen final (publicados y número real de eventos) | I/O (Kafka) |
| `producer/replay.py` | CLI: lee argumentos, configura y arranca; código de salida 1 con mensaje claro ante `ReplaySourceError` o selección vacía | Solo configura |

Pruebas: `tests/common/test_replay_message.py`, `tests/producer/test_replay_selection.py`, `test_replay_source.py`, `test_replay_runner.py`, `test_replay_cli.py` (sin Docker, con dobles) y `tests/integration/test_replay_consumer.py` (consumidor con PostgreSQL real, sin Kafka: los 26 mensajes pasan por `process_record` y dan 22/24/0).

### Código existente que cambia

| Archivo | Cambio |
|---|---|
| `common/config.py` | `load_consumer_topics()`: lee `KAFKA_CONSUMER_TOPICS` (coma), valida cada nombre contra `CONTRACT_TOPICS`, `ConfigError` si no |
| `consumer/loop.py` | `ConsumerSettings.topics`; `start_consumer` y el log de arranque usan todos los topics |
| `consumer/main.py` | `build_settings` rellena `topics` |
| `tests/consumer/test_consumer_loop.py` | Los dos `ConsumerSettings(...)` reciben `topics` |

### Compose, entorno e imagen

| Archivo | Cambio |
|---|---|
| `compose.yaml` | Servicio `consumer`: `KAFKA_CONSUMER_TOPICS: ${KAFKA_CONSUMER_TOPICS:-earthquakes.live,earthquakes.replay}`. Servicio `producer`: volumen `./data/historical:/app/data/historical:ro`. Sin servicios nuevos |
| `.env.example` | `KAFKA_CONSUMER_TOPICS=earthquakes.live,earthquakes.replay` con su comentario; `scripts/check_env_example.py` debe seguir en verde |
| `Dockerfile` | Sin cambios (ya copia `common/`, `producer/` y `historical/`) |
| `README.md` | Sección de configuración: fila de `KAFKA_CONSUMER_TOPICS` (defecto `earthquakes.live,earthquakes.replay`) y nota de que `KAFKA_TOPIC` ya no sirve para suscribir al consumidor. `specs/002-infra-compose/contracts/config.md` no se edita |
| Reconstrucción | Tras el cambio de código: `docker compose build producer` y `docker compose up -d consumer` (la imagen es compartida) |

### Lo que NO cambia

`common/{decode,validation,processing,transform,geo}.py`, `consumer/{pipeline,writer,queries}.py`, `api/`, `frontend/`, `sql/`, contratos, `docs/enunciado/`.

### Desviaciones respecto al diseño (comprobadas al cerrar)

- El volumen `./data/historical:/app/data/historical:ro` también está en el servicio `tests` de `compose.yaml` (las pruebas de integración usan los archivos reales); no es un contrato ni un servicio nuevo.
- La integración de la API con replay está en `tests/integration/test_api_replay_real.py` (archivo nuevo), no en una ampliación de `test_api_replay_events.py`.
- Parámetro de velocidad: `--interval` (D3), no `--speed`.
- `KAFKA_CONSUMER_TOPICS` se documenta en `.env.example` y README; `specs/002-infra-compose/contracts/config.md` no se editó.
- El replay solo lee `manifest.files`; los archivos `usgs_gap_*` no se usan (D10).
- `uv run` no funciona en el equipo: las pruebas sin Docker se ejecutaron con `.venv` y el servicio `tests`.

## Flujo

```
data/historical/*.geojson --(sha256, manifiesto)--> producer/replay_source.py
   -> producer/replay_selection.py (caja, orden, N)  + common/replay_message.py (bloque controlado)
   -> producer/replay_runner.py -> Kafka earthquakes.replay (clave = event.id)
   -> consumer (mismo proceso, dos topics) -> topic_mode -> esquema replay
   -> API ?mode=replay&start=2025-01-01&end=2026-01-01 -> panel (banner REPRODUCCIÓN)
```

## Verificación (resumen; detalle en `quickstart.md`)

1. Pruebas unitarias y de integración (bloques 1 y 2).
2. Recorrido de extremo a extremo con contenedores: recuentos de `live` antes y después (productor live parado), recuentos del replay (SC-001: 26, 22, 24, 0; 2 reenvíos, 1 posterior, 1 tardía), repetición idempotente (SC-006), API con `mode=replay` y `mode=live` (SC-003), panel con banner (SC-005).
3. README y `docs/borradores/replay.md` (J8).

## Riesgos y límites

- Los datos de 2025 se dibujan con opacidad mínima en el panel por `fadeByAge` (D9): se comprueba a mano; no se asume problema.
- El consumidor con dos topics: una prueba de `topic_mode` ya cubre el enrutado; la comprobación `mode` ↔ topic sigue en `common/validation_envelope.py`.
- El replay y el productor live a la vez cambian `live` por la actividad real de USGS, no por el replay; por eso se para el productor live durante la comprobación (spec, límites).
- `03 §8.5` dice `--speed 2`; el alumno lo actualiza a `--interval 2` (D3).
