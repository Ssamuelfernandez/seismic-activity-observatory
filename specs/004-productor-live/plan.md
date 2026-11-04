# Implementation Plan: Productor en vivo

**Branch**: `004-productor-live` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: `specs/004-productor-live/spec.md` (incluidas Clarifications y "Preguntas para el alumno").

> Este plan es SOLO documentación de diseño (constitución §19): sin código de aplicación, Dockerfile ni compose. Los cambios en archivos de infraestructura que exigirá la implementación están en `tasks.md`.

## Summary

Se sustituye el productor mínimo (un evento sintético cada intervalo) por un productor que cada `POLL_SECONDS` consulta el feed `all_day.geojson` de USGS, guarda el original y la consulta, filtra `type == earthquake` (anotando las exclusiones), compara `id` y `updated` con `ingest.ingest_state` y publica en `earthquakes.live` solo lo nuevo o revisado. Marca el evento en `ingest_state` **después** del ack de Kafka. Ante timeout, 429, 5xx o cuerpo no válido registra el error, no toca el estado y reintenta con backoff exponencial y jitter (2 s a 60 s). El consumidor existente no cambia. La lógica pura (validar el cuerpo, hash, decisión, mensaje, backoff) va a `common/`; la E/S, a `producer/`.

Decisiones y alternativas: [research.md](research.md). Tablas, filas y estructuras: [data-model.md](data-model.md). Verificación: [quickstart.md](quickstart.md).

No cambia ningún contrato (`kafka-message.md`, `db-schema.md`, `api.md`) ni `sql/001_schema.sql`. Sí cambia `sql/002_roles.sql` (no es contrato): `GRANT SELECT, DELETE ON ingest.raw_response TO observatory_producer`.

## Technical Context

- **Language/Version**: Python 3.12.16 (fijado en `Dockerfile`).
- **Dependencies**: las de `uv.lock` (`aiokafka 0.15.0`, `asyncpg 0.32.0`) y la biblioteca estándar (`urllib`, `hashlib`, `json`, `http.server` en pruebas). **Ninguna dependencia nueva** (constitución §11). Desarrollo: `pytest 9.2.0`.
- **Storage**: PostgreSQL 16 (esquemas `ingest` y `live`); Kafka, tema `earthquakes.live`.
- **Testing**: unitarias sin red ni servicios (funciones puras y ciclo con dobles); integración con PostgreSQL real en el servicio `tests` de Compose y mock de USGS en proceso; ejecución real con el stack y USGS.
- **Target Platform**: Docker Compose v2 sobre Windows 11 (contenedores Linux).
- **Project Type**: servicio de fondo (productor) más funciones puras compartidas.
- **Performance**: una consulta por minuto, del orden de cientos de eventos el primer ciclo y pocos después. Sin objetivo de rendimiento.
- **Constraints**: marca en `ingest_state` solo tras el ack; ningún fallo de USGS toca el estado; latido ≤ 120 s sin fallos de Kafka o PostgreSQL; sin ampliar el alcance.
- **Scale/Scope**: un productor, un tema, una partición.

Sin `NEEDS CLARIFICATION`: todo está resuelto en research.md.

## Constitution Check

| § | Regla | Cumplimiento |
|---|---|---|
| 1 | Al menos una vez, idempotente | El productor publica con `acks=all` e idempotencia y marca tras el ack; un corte entre ambos puede reenviar un mensaje, que el consumidor tolera (prueba 2, SC-004). |
| 2 | Versionado por `updated` | `decide_publication` solo publica con `updated` mayor; el `UPSERT` de `ingest_state` solo avanza. |
| 3 | Tiempos en ms | El evento viaja sin transformar; la conversión es del consumidor. |
| 4 | País por geometría | Fuera de alcance. |
| 5 | Nulos y negativos | `event` sin cambios: `mag` nulo y negativos viajan tal cual. |
| 6 | Cuarentena | Eventos sin `id` o `updated` se publican y los atiende el consumidor (`kafka-message.md` §3). |
| 7 | Sintéticos separados | El productor real solo publica `is_synthetic = false`. Los eventos del mock de pruebas son sintéticos, etiquetados `synthetic-…` y nunca van a una base real. |
| 8 | Agregaciones desde estado | No aplica. |
| 9 | Nombres de servicio | `kafka:9092`, `postgres:5432`; el mock de pruebas corre en el propio proceso de pruebas. |
| 10 | Exposición y secretos | Sin puertos nuevos. Las variables nuevas no son secretos y van a `.env.example`. |
| 11 | Versiones fijadas | Cero dependencias nuevas. |
| 12 | Alcance cerrado | Sin país, histórico, replay, API, reconciliación de eliminados ni `Retry-After`. |
| 13 | Idioma | Identificadores en inglés; docstrings y documentos en español (plantilla `03-procedimiento-ejecucion.md` §7.4). |
| 14 | Una responsabilidad; puro separado de E/S | Partición del §2 de este plan; <= 30 líneas por función y <= 250 por archivo. |
| 15 | Contratos únicos | Se referencian, no se copian. `db-schema.md` NO se edita: §1.1 es solo sincronía de redacción, sin cambio de contrato (§5). |
| 16 | Cierre de feature | Tareas del bloque 5: pruebas, evidencias, README y CODEMAP. |
| 17 | Frontend | No aplica. |
| 18 | Enunciado de solo lectura | No se toca `docs/enunciado/`. |
| 19 | Una feature cada vez | Solo documentos; sin commits. |
| 20 | Commits | Sin atribución de herramientas. |
| 21 | Sin predicción ni riesgo | No aplica. |

**Resultado**: sin violaciones, antes y después del diseño.

## Project Structure

### Documentación

```text
specs/004-productor-live/
├── spec.md
├── plan.md           # este archivo
├── research.md       # decisiones y alternativas
├── data-model.md     # filas, estructuras, variables, línea de log
├── quickstart.md     # cómo verificar
├── tasks.md
└── checklists/requirements.md
```

### Código (ruta prevista; se confirma en `CODEMAP.md` al cerrar)

```text
common/
├── usgs_feed.py          # puro: validar cuerpo (FeedFormatError), hash canónico de features
├── ingest_decision.py    # puro: Decision, decide_publication, build_exclusion_row
├── live_message.py       # puro: build_live_message
├── backoff.py            # puro: BackoffSettings, compute_backoff_seconds
└── config.py             # + FeedSettings y load_feed_settings; se quita PRODUCER_INTERVAL
producer/
├── usgs_client.py        # E/S: GET con timeout (urllib en hilo), FeedResponse, FeedFetchError
├── ingest_queries.py     # SQL del productor (constantes)
├── ingest_store.py       # E/S: ingest_run, raw_response, exclusion, ingest_state, purga
├── cycle.py              # un ciclo completo (orquesta; sin lógica de decisión)
├── loop.py               # bucle: ciclo, espera, backoff, latido
├── publisher.py          # se conserva (start_producer, publish_message)
└── main.py               # solo configura y arranca
sql/002_roles.sql         # + GRANT SELECT, DELETE ON ingest.raw_response
tests/
├── common/               # pruebas de las funciones puras
├── producer/             # cliente HTTP, ciclo con dobles, bucle
├── integration/          # ciclo con PostgreSQL real y mock de USGS
└── support/mock_usgs.py  # servidor simulado de USGS (sintético, etiquetado)
```

`common/synthetic_event.py` se conserva (lo usan pruebas). `scripts/verify_stack.py` (check A1) y `tests/producer/test_loop.py` se adaptan.

## 1. Flujo de un ciclo

```text
GET feed ──error──> ingest_run(error) ──> backoff ──> siguiente ciclo
   │ ok
   v
validar cuerpo ──inválido──> ingest_run(error) ──> backoff
   │ ok
   v
[transacción] raw_response (si hash nuevo) + ingest_run(ok)
   v
clasificar elementos (puro) ──> exclusion (idempotente)
   v
leer ingest_state de los id ──> por cada PUBLISH: send_and_wait ──> UPSERT ingest_state
   v                                            └─ fallo de Kafka: cortar ciclo, backoff, sin latido
latido ──> purga raw_response ──> esperar POLL_SECONDS
```

Fallo de USGS (primeras dos ramas): se renueva el latido (el productor está vivo) y se espera con backoff. Fallo de Kafka o PostgreSQL: sin latido. Tras un ciclo correcto el contador de fallos vuelve a cero.

## 2. Contratos de función (resumen; la plantilla de docstring va en el código)

| Función | Entrada | Salida | Pura |
|---|---|---|---|
| `parse_feed_body(raw: bytes)` | cuerpo | lista de `features` (dict) o `FeedFormatError` | sí |
| `hash_features(features)` | lista | sha256 hex | sí |
| `decide_publication(feature, last_updated_ms)` | elemento y estado | `Decision` | sí |
| `build_exclusion_row(feature, fetched_at)` | elemento | fila de `exclusion` | sí |
| `build_live_message(feature, ingested_at)` | elemento e instante | `dict` del contrato §3 | sí |
| `compute_backoff_seconds(failures, settings, jitter_fraction)` | nº de fallos, parámetros, número en [0,1) | segundos | sí |
| `fetch_feed(url, timeout)` | URL | `FeedResponse` o `FeedFetchError` | no (HTTP) |
| funciones de `ingest_store` | conexión/pool y filas | nada o datos | no (PostgreSQL) |
| `run_cycle(deps, settings)` | dependencias (pool, productor, cliente, reloj) | `CycleResult` | no |

`run_cycle` recibe sus dependencias (cliente, publicador, almacén, reloj) como argumentos para probarlo con dobles sin red ni servicios. El `jitter_fraction` entra por argumento para que la prueba del backoff sea determinista.

## 3. Backoff y latido

- Espera tras el fallo número `n` (n >= 1): `min(60, 2 * 2^(n-1))` multiplicado por un factor aleatorio entre 0,5 y 1,0. Secuencia base: 2, 4, 8, 16, 32, 60, 60… (SC-006). Tras un ciclo correcto, `n = 0` y se espera `POLL_SECONDS`.
- Peor caso de una vuelta fallida: 10 s de timeout + 60 s de espera = 70 s, menor que `HEALTH_MAX_AGE_SECONDS = 120`.
- El latido se renueva al terminar un ciclo correcto o con fallo controlado de USGS; no tras un fallo de Kafka o PostgreSQL.

## 4. Cambios en infraestructura (los hace `tasks.md`)

- `.env.example`, `compose.yaml` (servicio `producer`), `config.md`: añadir `POLL_SECONDS`, `USGS_FEED_URL`, `HTTP_TIMEOUT_SECONDS`, `RAW_RETENTION_DAYS`; quitar `PRODUCER_INTERVAL_SECONDS`. El servicio `tests` recibe además `DB_PRODUCER_PASSWORD` para probar con el rol real del productor.
- `sql/002_roles.sql`: el `GRANT` de §Summary. El `conftest.py` de integración ya aplica todos los `GRANT` de ese archivo a la base temporal.
- El `Dockerfile` no cambia (copia `common/` y `producer/` ya).
- `docs/borradores/productor-live.md`: texto de B2, B11 y B12 para la memoria (la memoria final la redacta el alumno). README: política de retención y ejecución.

## 5. Preguntas para el alumno (siguen abiertas)

1. **Sintéticos fuera del productor y A1 adaptado**: decisión provisional de la spec mantenida (ver spec).
2. **`DELETE` en `sql/002_roles.sql`**: se concede `SELECT, DELETE` (hace falta `SELECT` para el `WHERE` y la subconsulta). **Sincronía de redacción, sin cambio de contrato**: la tabla de `db-schema.md` §1.1 dice que `raw_response` solo la escribe el productor y la leen consultas de evidencia; con este cambio el productor también la lee y borra. La feature solo concreta §3.9 (retención); `db-schema.md` NO se edita y el `GRANT` está en `sql/002_roles.sql`, que no es contrato.
   - **Volúmenes ya creados**: `postgres_init.sh` solo corre con volumen nuevo; hay que reaplicar el `GRANT` con `psql` o hacer `docker compose down -v` (quickstart §0).
   - **Desviación de CODEMAP**: las tareas no tocan `CODEMAP.md`; se actualiza una sola vez en T021 (desviación de CLAUDE.md por proporcionalidad, a confirmar con el alumno).
   - **Límites conocidos**: el timeout de `urllib` actúa por operación de socket, no sobre la descarga total; y los eventos sin `id` o `updated` se republican en cada ciclo.
3. **Retención de 7 días y hash sobre `features`**: decisión provisional mantenida.
4. **Fallo de Kafka y `ingest_run`**: se interpreta "el ciclo se registra con error" como registro en el log, sin segunda fila en `ingest_run` (research §2). Si el alumno prefiere una fila de error, hay que decidir qué `status` lleva.

## Complexity Tracking

Sin violaciones que justificar.
