# Implementation Plan: Consumidor idempotente

**Branch**: `003-consumidor-idempotente` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: `specs/003-consumidor-idempotente/spec.md` (incluidas Clarifications, FR-011, FR-014 regla general, FR-023, FR-036 y "Preguntas para el alumno").

> Este plan es SOLO documentación de diseño (constitución §19): no contiene código de aplicación, Dockerfile ni compose. Los cambios en archivos de infraestructura que exigirá la implementación se listan en §12 para que `tasks.md` los convierta en tareas; no se hacen aquí.

## Summary

Se sustituye el consumidor mínimo de `002-infra-compose` (solo registra) por un consumidor que, por cada mensaje de `earthquakes.live`, hace: **decodificar → validar → transformar (ms → UTC) → una transacción en PostgreSQL → commit en PostgreSQL → commit del offset de Kafka**. Los mensajes inválidos van a `live.quarantine` (con saneado previo y regla de copia) y su offset se confirma. Los fallos de base de datos que no dependen del contenido se reintentan sin límite, con espera acotada, sin confirmar el offset. Toda la lógica pura (decodificar, validar, transformar, construir la fila de cuarentena, decidir el resultado de la versión, parsear el catálogo) vive en `common/` para que `historico-2025` y `replay` la reutilicen; la E/S (Kafka y PostgreSQL con `asyncpg`) vive en `consumer/`. El consumidor carga además `public.country` desde `data/catalogo/paises.geojson` al arrancar y lleva contadores en memoria (C8). El detalle de cada decisión está en [research.md](research.md); las entidades y el mapeo mensaje → columnas, en [data-model.md](data-model.md); el procedimiento de verificación, en [quickstart.md](quickstart.md); las variables nuevas, los contadores y el formato del registro, en [contracts/consumer-runtime.md](contracts/consumer-runtime.md).

No cambia ningún contrato (`kafka-message.md`, `db-schema.md`, `api.md`), ni el DDL (`sql/001_schema.sql`), ni los permisos (`sql/002_roles.sql`). Los contratos se referencian, no se copian (constitución §15).

## Technical Context

**Language/Version**: Python 3.12.16 (fijado en `Dockerfile` y `.python-version`).

**Primary Dependencies**: las que ya están bloqueadas en `uv.lock`: `aiokafka 0.15.0` (consumo y commit manual) y `asyncpg 0.32.0` (cliente de PostgreSQL, el que ya usa `common/db.py`). **No se añade ninguna dependencia** (constitución §11): ni `psycopg`, ni `pytest-asyncio`, ni `testcontainers`. Desarrollo: `pytest 9.2.0`.

**Storage**: PostgreSQL 16 (`postgres:16.15-bookworm`), esquemas `public` y `live` del DDL existente. Kafka: tema `earthquakes.live` (1 partición).

**Testing**: pytest en dos niveles. (1) Unitarios de funciones puras y de adaptadores con dobles, sin Kafka ni PostgreSQL (FR-033), ejecutables en el equipo del alumno. (2) Integración con PostgreSQL 16 real, marcados `integration`, ejecutados **dentro de la red de Compose** (la base no se publica al anfitrión: constitución §10). Verificación de punta a punta con Kafka y la parada de servicios mediante `scripts/verify_consumer.py` (mismo patrón que `scripts/verify_stack.py`).

**Target Platform**: Docker Compose v2 (Windows 11 / Docker 29 en el equipo del alumno; contenedores Linux).

**Project Type**: servicio de fondo (consumidor) más librería compartida de procesamiento.

**Performance Goals**: no hay objetivo de rendimiento; el volumen del feed de USGS es de decenas de eventos por minuto. Se prioriza la corrección: un commit de offset por mensaje (research §9).

**Constraints**: offset siempre después del commit en PostgreSQL (§1); rol `observatory_consumer` sin `SELECT` sobre la cuarentena (solo `INSERT ... ON CONFLICT DO NOTHING` simple, sin `RETURNING`); contadores solo en memoria; sin ampliar el alcance (§12).

**Scale/Scope**: 1 consumidor, 1 partición, 1 tema. El esquema `replay` queda soportado por la lógica compartida pero no se consume.

No quedan `NEEDS CLARIFICATION`: las incógnitas del plan están resueltas en [research.md](research.md).

## Constitution Check

*GATE: pasa antes de la investigación y se reevalúa tras el diseño.*

| § | Regla | Cumplimiento en este plan |
|---|---|---|
| 1 | Al menos una vez, escritura idempotente, offset tras commit en PG | Orden fijo en `consumer/pipeline.py` y `consumer/loop.py` (§1): transacción PG → commit PG → línea de decisión → `consumer.commit(offset+1)` → contadores. Escritura con `INSERT ... ON CONFLICT (event_id, updated_ms) DO NOTHING` y upsert condicional (`db-schema.md` §5). `enable_auto_commit=False` (ya en `002`). Hook de prueba entre ambos commits (§4) y pruebas 2, 8. |
| 2 | Versionado por `updated`; un evento = una fila actual | `common/processing.py::decide_version_outcome` (pura) y upsert con `WHERE EXCLUDED.updated_ms > current_event.updated_ms`. PK de `current_event` = una fila por evento. Pruebas 3 y 4. |
| 3 | Tiempos de USGS en ms, a UTC conservando el original | `common/transform.py::ms_to_utc` (aritmética entera, sin `float`); se guardan `event_time`/`event_time_ms` y `updated_at`/`updated_ms`. Rango admitido fijado en research §6. |
| 4 | País por geometría, nunca de `place` | Fuera de alcance: `country_id` queda `NULL` (FR-021); el upsert nunca escribe `country_id`. Se carga solo el catálogo (`public.country`). |
| 5 | Nulos sin rellenar con 0; negativos válidos | La validación acepta `None` en `mag`, profundidad, `place`, `status`, `url`, `sig`, `magType`; los límites son −10…15 y −100…1000, sin umbral en 0. Tests con `mag = -0.06` y profundidad `-0.18`. |
| 6 | Cuarentena con motivo y referencia; sin bloquear la cola | `common/quarantine_row.py` (pura) con saneado y regla de copia; `consumer/writer.py::write_quarantine`. Todo contenido hostil se resuelve antes del `INSERT` (regla general FR-014, research §5). |
| 7 | Datos sintéticos etiquetados y separados | `is_synthetic` se copia a las tres tablas; los fixtures de prueba llevan `is_synthetic = true`, `source = replay_demo` e ids `synthetic-…`. |
| 8 | Agregaciones desde el estado actual | Los contadores (C8) son un registro de transformaciones, no estadísticas de la API (FR-024); la API no los lee. |
| 9 | Nombres de servicio, nunca `localhost` | Sin cambios: `kafka:9092`, `postgres:5432`. El servicio de pruebas (`tests`) también usa nombres de servicio. |
| 10 | Solo la API expuesta; sin secretos; `.env.example` al día | No se publica ningún puerto nuevo: las pruebas de integración corren dentro de la red de Compose. Las variables nuevas (§12) van a `.env.example` y a `config.md`; `scripts/check_env_example.py` las verifica. |
| 11 | Versiones fijadas | Cero dependencias nuevas; ver Technical Context. Las etapas nuevas del `Dockerfile` reutilizan `uv sync --frozen`. |
| 12 | Alcance cerrado | Sin país, sin productor real, sin replay, sin cola de mensajes muertos, sin tabla de contadores, sin panel de calidad. |
| 13 | Identificadores en inglés; docstrings y documentación en español | Todos los módulos y funciones de §2 en inglés; los docstrings siguen la plantilla de `03-procedimiento-ejecucion.md` §7.4 (Qué hace / Recibe / Devuelve / Por qué existe). |
| 14 | Una responsabilidad por función; lo puro separado de la E/S | Partición de §2: `common/` puro, `consumer/` con E/S; ≤ 30 líneas por función y ≤ 250 por archivo (por eso `loop.py` delega la línea de decisión y el volcado de contadores en `reporting.py` y el commit con reintento en `resilience.py`); `main.py` solo configura y arranca. |
| 15 | Contratos únicos | Se referencian `kafka-message.md` y `db-schema.md`; el motivo, el orden de prevalencia y las tablas no se redefinen aquí. `contracts/consumer-runtime.md` solo documenta lo que ningún contrato cubre (variables de ejecución, contadores, registro). `docs/enunciado/` no se toca. |
| 16 | Cierre de feature | `tasks.md` incluirá: pruebas ejecutadas, evidencias en `docs/evidencias/consumidor-idempotente/`, `README.md` y `CODEMAP.md` actualizados (FR-034, FR-035). |
| 17 | Frontend sin cálculo de estadísticas | No aplica (sin frontend). |
| 18 | Enunciado de solo lectura; `specs/` no se copia a `docs/` | Sin cambios en `docs/enunciado/`. La memoria (`docs/memoria.md`) resume las reglas de calidad sin copiar `specs/`. |
| 19 | Una feature cada vez; sin implementar sin spec, plan y tareas revisados | Este paso solo produce documentos. No se escribe código, `Dockerfile` ni `compose.yaml`. Sin commits. |
| 20 | Commits descriptivos, sin trailers de IA | No se hace ningún commit; los mensajes futuros seguirán la regla. |
| 21 | Sin lenguaje de predicción ni de riesgo | Los documentos de la feature no emiten conclusiones sobre sismicidad. |

**Resultado**: sin violaciones. Reevaluado tras el diseño (research, data-model, contracts): igual. Hay un cambio de infraestructura de `002` (servicio `tests` bajo un perfil de Compose, montaje del catálogo, variables nuevas) que no viola ningún principio, pero se escala como decisión discutible (§13).

## Project Structure

### Documentation (this feature)

```text
specs/003-consumidor-idempotente/
├── spec.md
├── plan.md              # Este archivo
├── research.md          # Decisiones, alternativas y los menores heredados
├── data-model.md        # Entidades en memoria, mapeo mensaje -> columnas, reglas de resultado
├── quickstart.md        # Cómo verificar la feature (unitarias, integración, punta a punta)
├── contracts/
│   └── consumer-runtime.md   # Variables nuevas, contadores, líneas de registro, hook de prueba
├── checklists/requirements.md
└── tasks.md             # Generado por /speckit-tasks (93 tareas, T001-T093)
```

### Source Code (repository root)

Las rutas coinciden con las "previstas" de `CODEMAP.md` (`consumer/pipeline.py`, `common/validation.py`, `consumer/writer.py`, `common/processing.py::is_newer_version`). Los archivos nuevos se anotarán en `CODEMAP.md` al cerrar la feature.

```text
common/                      # LÓGICA PURA reutilizable por historico-2025 y replay (sin red ni base de datos)
├── records.py               # dataclasses: RawRecord, MessageRef, DecodeResult, ValidEvent, Rejection,
│                            #   EventRows, QuarantineRow, VersionOutcome (enum)
├── decode.py                # bytes|None -> JSON o invalid_json (UTF-8 estricto, enteros largos, RecursionError)
├── storable.py              # ¿cabe en jsonb/text?: no finitos, NUL, sustitutos sueltos, profundidad; saneado de textos
├── validation.py            # sobre + evento en el orden de prevalencia de kafka-message.md §6 (pura y total)
├── transform.py             # ms -> UTC, date_id, filas de current_event / event_version
├── quarantine_row.py        # fila de cuarentena: motivo, regla de copia, saneado, SHA-256 de los bytes
├── processing.py            # decide_version_outcome / is_newer_version (resultado de una versión)
├── catalog.py               # parse_country_catalog(geojson) -> filas de public.country
└── kafka_topics.py          # (existe) + topic_mode(topic) -> "live" | "replay"

consumer/                    # E/S (Kafka, PostgreSQL, registro, señales)
├── main.py                  # (existe) configura y arranca; instala el manejador de SIGTERM
├── loop.py                  # (existe) SOLO bucle de consumo, sondeo del broker (con registro del fallo), latido y
│                            #   parada; por mensaje: pipeline -> reporting.log_decision -> resilience (commit del
│                            #   offset) -> counters.apply_result. Meta: ≤ 250 líneas (constitución §14)
├── reporting.py             # línea de decisión por mensaje (log_decision), línea COUNTERS periódica y final
│                            #   (dump_counters, tarea de 60 s); formato de consumer-runtime §4
├── pipeline.py              # process_record: decodificar -> validar -> escribir -> (hook) ; devuelve ProcessingResult
│                            #   (no confirma offsets ni toca contadores)
├── writer.py                # transacción de evento y escritura de cuarentena (asyncpg)
├── queries.py               # sentencias SQL con parámetros (el esquema sale de una lista cerrada)
├── db_errors.py             # is_content_error(exc): clase 22/23 o excepción equivalente de asyncpg
├── resilience.py            # retry_db_operation / commit_offset_with_retry (commit con reintento), sin límite,
│                            #   con parada limpia
├── counters.py              # Counters (en memoria), apply_result, snapshot, identidades de FR-023
├── catalog_loader.py        # lee el GeoJSON y hace el upsert en public.country
├── schema_check.py          # comprueba que existen las tablas esperadas (FR-026)
└── fault_hook.py            # hook de prueba entre el commit de PG y el commit del offset (prueba 8)

tests/
├── common/                  # unitarias puras (decode, storable, validation, transform, quarantine_row, processing, catalog)
├── consumer/                # unitarias con dobles (db_errors, counters, resilience, reporting, pipeline, fault_hook, loop)
└── integration/             # marcadas `integration`: PostgreSQL 16 real, rol observatory_consumer
    ├── conftest.py          # base temporal + DDL (001) + GRANT de 002 + conexiones consumidor/administrador
    └── test_*.py

tests/support/publish_messages.py   # publicador de los escenarios de verify_consumer.py; vive en tests/ porque
                                    #   esa carpeta ya se monta en el servicio `tests` (scripts/ no) y este
                                    #   alcanza Kafka por nombre de servicio (kafka:9092)
scripts/verify_consumer.py   # punta a punta con Compose (Kafka real, parada de PG y de Kafka, reinicio, contadores)
scripts/verify_stack.py      # (existe) se actualiza el check A1 del log del consumidor (regresión de 002, §12)
docs/memoria.md              # (existe) §4 Calidad: resumen con referencias (C1, FR-034)
docs/evidencias/consumidor-idempotente/   # SQL antes/después, logs, fila de cuarentena, contadores (FR-034)
```

**Structure Decision**: un solo proyecto Python con raíz compartida (como en `002`). `common/` contiene todo lo reutilizable; `consumer/` solo adaptadores y orquestación. `consumer/loop.py` conserva `start_consumer` y `broker_reachable` (la prueba existente `tests/consumer/test_broker_probe.py` sigue valiendo); se retira `describe_message` y su uso.

## 1. Orden de operaciones por mensaje (C1, C2; FR-001, FR-002)

`loop.py` pide un único mensaje (`getmany(timeout_ms=1000, max_records=1)`), así el orden por partición es el de lectura y el commit del offset es por mensaje. **Reparto de responsabilidades (decisión provisional, §13.9 y §13.10)**: `pipeline.process_record` hace solo los pasos 1 a 6 y devuelve un `ProcessingResult`; **el bucle de consumo (`loop.py`) hace los pasos 7 a 9**: escribe la línea de decisión (`reporting.log_decision`), confirma el offset (`resilience.commit_offset_with_retry`) y, solo después, llama a `counters.apply_result`. Así `process_record` no conoce a Kafka ni a los contadores. Para cada mensaje, `pipeline.process_record` hace:

1. `decode_value(raw)` → JSON o `invalid_json`. Pura.
2. `validate_message(decoded, topic_mode)` → `ValidEvent` o `Rejection(reason)`. Pura y total.
3. Si es válido, `build_event_rows(...)` (transformación ms → UTC). Pura.
4. **Escritura**, con reintento (§5): una transacción PostgreSQL (`writer.write_event`) o, si hay rechazo, una sentencia de cuarentena (`writer.write_quarantine`).
5. **Commit en PostgreSQL** (salida limpia del `async with conn.transaction()`; para cuarentena, la sentencia autocommit).
6. **Hook de prueba** `after_db_commit(ref, is_synthetic)` (por defecto, nada; §4).
7. **Línea de decisión** (la escribe el bucle, no `process_record`): `reporting.log_decision(result)`, justo después del commit de PostgreSQL (el hook del paso 6 es solo de prueba y está inactivo en producción) y **antes** del commit del offset. Así FR-003 (una línea por decisión) se cumple siempre, también si el commit del offset se salta por `CommitFailedError`.
8. **Commit del offset** (también el bucle): `consumer.commit({tp: offset + 1})`, con reintento (§5).
9. Solo ahora: `counters.apply_result(result)` (los contadores cambian tras el commit del offset, FR-023).

Garantías: si el proceso muere entre 5 y 8, el mensaje se reentrega y el paso 4 es idempotente (reenvío ignorado). Si falla 4, no se llega a 7. Ningún contador cambia antes de 8 (FR-023). **Consecuencia aceptada (decisión provisional, §13.10)**: una reentrega duplica la línea de decisión del mismo `topic/partition/offset` (la primera, p. ej. `new_event`, y la segunda, `redelivery_ignored`); es aceptable porque cada línea describe una decisión real y los contadores no se ven afectados por la línea.

## 2. Estructura de módulos (FR-030, constitución §14)

Funciones puras (todas en `common/`, sin importar `asyncpg` ni `aiokafka`):

| Función | Entra → sale | Notas |
|---|---|---|
| `decode.decode_value(raw)` | `bytes\|None` → `DecodeResult` | Primero `raw.decode("utf-8")` estricto y luego `json.loads(str)` (nunca `json.loads(bytes)`, que autodetecta UTF-16/32). `None`/vacío, UTF-8 inválido, **BOM (`EF BB BF`) y UTF-16/32** (`json.loads` del `str` con `﻿` inicial falla), `JSONDecodeError`, `ValueError` de enteros > 4300 dígitos y `RecursionError` → `invalid_json`. |
| `storable.is_storable_json(obj)` | objeto → `bool` | Recorrido iterativo (sin recursión): no finitos, NUL, sustitutos sueltos, profundidad > 64. |
| `storable.sanitize_raw_text(raw)` | `bytes` → `str` | Saneado exacto en research §4. |
| `validation.validate_message(decoded, topic_mode)` | → `ValidEvent \| Rejection` | 14 motivos en orden de prevalencia + regla general FR-014 (research §3). |
| `transform.ms_to_utc(ms)`, `transform.build_event_rows(valid, ref, now)` | → `datetime`, `EventRows` | Incluye `date_id`, `dow` y la conversión de `numeric` (`Decimal(str(x))`). |
| `quarantine_row.build_quarantine_row(decoded, reason, ref, now)` | → `QuarantineRow` | Los bytes recibidos van en `decoded.raw` (4 parámetros). Regla de copia y saneado de FR-011; SHA-256 de los bytes recibidos. |
| `processing.decide_version_outcome(...)`, `processing.is_newer_version(...)` | → `VersionOutcome` | Resultado de una versión a partir de lo que devolvió la base. |
| `catalog.parse_country_catalog(geojson)` | `dict` → `list[CountryRow]` | 177 filas; falla con nombre si falta un campo. |
| `consumer/db_errors.is_content_error(exc)` | excepción → `bool` | Pura aunque viva en `consumer/` (no abre conexiones; solo inspecciona la excepción). |
| `consumer/counters.apply_result` | → contadores | Pura sobre el objeto en memoria. |

**Relación con el roadmap.** `02-roadmap-implementacion.md` (F3/F6) habla de `common.processing.process_event()` como la lógica que reutilizaría el cargador histórico. Aquí esa idea se reparte en dos: la parte pura (decidir el resultado de una versión, validar, transformar) vive en `common/processing.py`, `common/validation.py` y `common/transform.py`; la parte con E/S (la transacción) vive en `consumer/writer.py::write_event`. No existe una función `process_event()` con ese nombre: es decisión provisional (§13.9) y `historico-2025` importará `common/*` y `consumer/writer.py` (o moverá `writer.py` a `common/` si decide no depender de `consumer/`; lo decide esa feature).

E/S (solo `consumer/`): `loop.py` (Kafka, latido), `reporting.py` (registro de decisiones y contadores), `writer.py` (PostgreSQL), `catalog_loader.py` (lee el archivo y escribe), `schema_check.py` (consulta), `resilience.py` (esperas y parada), `fault_hook.py` (puede terminar el proceso), `main.py` (entorno y señales).

El modo se parametriza por tema: `topic_mode(topic)` en `common/kafka_topics.py` (usa las constantes `TOPIC_LIVE`/`TOPIC_REPLAY` que ya existen) y el esquema destino sale de una lista cerrada `{"live": "live", "replay": "replay"}`; ningún texto del mensaje llega a un identificador de SQL. Esta feature solo consume `earthquakes.live`, pero `historico-2025` y `replay` importan las mismas funciones.

## 3. Carga del catálogo de países y de `date_dim` (FR-019, FR-025, FR-026)

- **Arranque** (`run_consumer`): `check_database` (ya existe) → `schema_check.ensure_schema_ready` (comprueba con `to_regclass` las 8 tablas que usa: `public.country`, `public.date_dim`, `live.current_event`, `live.event_version`, `live.quarantine` y las mismas de `replay` para el contrato de paridad; si falta alguna, lanza `SchemaNotReadyError` con el nombre de la tabla y el proceso termina; Compose lo reinicia) → `catalog_loader.load_country_catalog` → `start_consumer`.
- **Catálogo**: `common/catalog.py::parse_country_catalog` extrae `ADM0_A3 → country_id`, `NAME_ES → name_es`, `ADMIN → admin`, `CONTINENT → continent`, `SUBREGION → subregion` (db-schema §3.1). `catalog_loader` hace un `INSERT ... ON CONFLICT (country_id) DO UPDATE SET ... WHERE (columnas) IS DISTINCT FROM (EXCLUDED....)` en una sola transacción. Repetible: la segunda ejecución no cambia nada. Registra "N países cargados, M nuevos, K actualizados". El archivo no se modifica y llega al contenedor con un montaje de solo lectura (§12).
- **`date_dim`**: no se precarga. Dentro de la transacción de cada mensaje, antes del evento, `INSERT INTO public.date_dim (...) VALUES (...) ON CONFLICT (date_id) DO NOTHING` (`year`, `month`, `day`, `dow` ISO con `isoweekday()`). Varios mensajes del mismo día no fallan (US-edge "Día UTC nuevo").

## 4. Transacción de un mensaje válido y mecanismo de corte (FR-005, FR-009, FR-010; prueba 8)

Dentro de **una** transacción `READ COMMITTED` sobre una conexión del pool (`writer.write_event`):

1. `INSERT INTO public.date_dim ... ON CONFLICT DO NOTHING`.
2. `SELECT updated_ms FROM {esquema}.current_event WHERE event_id = $1 FOR UPDATE` (estado previo; bloquea la fila si dos consumidores se solaparan por error; el rol tiene `UPDATE`).
3. `INSERT INTO {esquema}.event_version (...) ON CONFLICT (event_id, updated_ms) DO NOTHING`; el resultado (`INSERT 0 1` / `INSERT 0 0` en la etiqueta de la sentencia) dice si la versión es nueva.
4. Si la versión **no** era nueva: `SELECT original IS DISTINCT FROM $1::jsonb FROM {esquema}.event_version WHERE event_id = $2 AND updated_ms = $3` (comparación `jsonb`, insensible a espacios y orden de claves). Distinto → conflicto «mismo `updated`, contenido distinto».
5. `decide_version_outcome(stored_updated_ms, incoming_updated_ms, version_inserted, content_differs)` → `NEW_EVENT | NEWER_VERSION | LATE_OLD_VERSION | REDELIVERY | SAME_UPDATED_CONFLICT`.
6. Solo si `NEW_EVENT` o `NEWER_VERSION`: `INSERT INTO {esquema}.current_event (...) ON CONFLICT (event_id) DO UPDATE SET ... WHERE EXCLUDED.updated_ms > {esquema}.current_event.updated_ms` (`db-schema.md` §5). El `DO UPDATE` no escribe `country_id`.
7. Salida del bloque `transaction()` = `COMMIT`. La FK diferida `event_version → current_event` se comprueba aquí.

Un error de clase 22/23 en cualquiera de las sentencias o en el `COMMIT` sube como excepción tras el `ROLLBACK`; `pipeline` lo convierte en cuarentena `db_constraint_violation` (research §7). Cualquier otro error se reintenta (§6).

**Límite anotado (carrera).** Un `23505`/`23503` causado por una carrera con una instancia zombi del consumidor (dos procesos solapados) se enviaría a cuarentena como `db_constraint_violation` aunque el mensaje sea correcto. Es muy improbable con 1 consumidor y 1 partición y el `SELECT ... FOR UPDATE` lo mitiga; no se diseña nada más (alcance, §12).

**Hook de corte (prueba 8).** `pipeline.process_record` recibe un parámetro `after_db_commit` (callable o `None`, con la referencia del mensaje y su `is_synthetic`) que se invoca justo después del commit de PostgreSQL y justo antes de que el bucle llame a `consumer.commit`. Tiene dos usos, ninguno modifica el flujo de producción:

- **pytest (integración, PostgreSQL real, Kafka simulado)**: un doble que lanza `SimulatedCrash` (hereda de `BaseException`, para que ningún `except` del flujo lo absorba) cuando llega el offset elegido. La prueba reinicia el bucle con un consumidor simulado que parte del último offset confirmado y comprueba que la base queda idéntica a la de una ejecución sin corte (SC-005).
- **Docker (evidencia con Kafka real)**: `fault_hook.crash_once_at_offset(offset, marker_path)` termina el proceso con `os._exit(137)` tras el commit de PostgreSQL, **una sola vez** (deja un archivo marcador en `/tmp` del contenedor, que sobrevive al reinicio de `restart: unless-stopped` pero se pierde si se recrea el contenedor) y **solo si el mensaje es `is_synthetic=true`** (salvaguarda: aunque la variable quedara activada por error, un dato real nunca provoca la salida, ni tras recrear el contenedor). Se activa solo con la variable opcional `CONSUMER_FAULT_CRASH_AT_OFFSET` (vacía = desactivada; detalle en [contracts/consumer-runtime.md](contracts/consumer-runtime.md)). Con la variable vacía, `main.py` no instala ningún hook.

## 5. Reintentos con tope y tasa de registro (FR-014, FR-029)

Valores concretos, sin variable nueva (se reutilizan `RETRY_INITIAL_SECONDS = 1` y `RETRY_MAX_SECONDS = 30` de `002`):

| Concepto | Valor |
|---|---|
| Número de intentos | **Sin límite** (decisión de Clarifications). |
| Espera | `common/retry.py::next_delay`: 1, 2, 4, 8, 16 s y 30 s a partir de entonces (tope = `RETRY_MAX_SECONDS`). Se reinicia a 1 s con cada mensaje nuevo. |
| Registro | **Una línea `WARNING` por intento**, sin traceback, con `event_id`, tema, partición, offset, clase de excepción, SQLSTATE si lo hay y el mensaje de la excepción truncado a 200 caracteres. En régimen (tope alcanzado) son ≤ 2 líneas por minuto por mensaje bloqueado: el contenido no crece sin límite. |
| Qué se reintenta | Escritura del evento, escritura de cuarentena y commit del offset (clasificación en §6). |
| Parada limpia | La espera es `asyncio.wait_for(stop_event.wait(), delay)`: una señal de parada interrumpe el reintento sin confirmar el offset. |
| Commit de offset | `CommitFailedError` (el grupo cambió de generación) **no** se reintenta: se registra y se sigue (la línea de decisión ya se escribió en el paso 7; los contadores no se tocan); el mensaje se reentregará y la base es idempotente. Otros `KafkaError`/`OSError` se reintentan con la misma espera. |
| Salto de poll | `max_poll_interval_ms = 86_400_000` (24 h, constante con nombre) para que un reintento largo no expulse al consumidor del grupo; `session_timeout` y latido de grupo quedan por defecto de `aiokafka`. |

**Latido durante el reintento (FR-029).** El latido solo se renueva en `loop.py` después de dar una vuelta completa (mensaje procesado o sondeo vacío con el broker alcanzable). Mientras un mensaje está en reintento, el bucle no avanza y **el latido no se renueva**: con `HEALTH_MAX_AGE_SECONDS = 60` y 3 comprobaciones de 15 s, el contenedor pasa a `unhealthy` unos 90-105 s después del último latido. En cuanto la base responde, el mensaje se guarda, el bucle continúa y el latido se renueva, así que el contenedor vuelve a `healthy` (se verifica en `verify_consumer.py`, escenario `pg-down`). Es la consecuencia aceptada del alumno para mensaje venenoso y errores `54*`; ningún cambio de `compose.yaml` en los umbrales.

## 6. Mapa de excepciones del cliente de base de datos (FR-014)

El cliente de `002` es **`asyncpg 0.32.0`** (`common/db.py`). Clasificación en `consumer/db_errors.py::is_content_error(exc)`, aplicada **solo** a errores del `INSERT`/`COMMIT` de un mensaje ya validado:

| Excepción de `asyncpg` | Clase SQLSTATE | Tratamiento |
|---|---|---|
| `asyncpg.exceptions.IntegrityConstraintViolationError` y subclases (`UniqueViolationError` 23505, `ForeignKeyViolationError` 23503, `CheckViolationError` 23514, `NotNullViolationError` 23502…) | 23 | contenido → `db_constraint_violation` |
| `asyncpg.exceptions.DataError` (clase 22 del servidor: `CharacterNotInRepertoireError` 22021, `NumericValueOutOfRangeError` 22003, `UntranslatableCharacterError` 22P05…; también la que `asyncpg` levanta en cliente por «invalid input for query argument», sin SQLSTATE del servidor) y cualquier `PostgresError` con `sqlstate` que empiece por `22` o `23` | 22 / equivalente | contenido → `db_constraint_violation` |
| `UnicodeError` al codificar un argumento | equivalente | contenido (y se registra como defecto de validación previa) |
| Resto de `asyncpg.PostgresError` (`08*`, `40*`, `53*`, `54*`, `57*`, `42*`, `28*`…), `asyncpg.InterfaceError`, `OSError`, `asyncio.TimeoutError` | otras | transitorio / configuración → reintento |
| Cualquier otra excepción (`TypeError`, `KeyError`…) | — | defecto del programa: **se propaga** y el proceso termina con traza (Compose lo reinicia). No se captura con `except Exception`. |

Nota de verificación: en `asyncpg 0.32.0` hay dos clases llamadas `DataError` (`_base.DataError`, cliente, `InterfaceError`+`ValueError`, y `exceptions.DataError`, servidor, clase 22); la del módulo `asyncpg.exceptions` es la de `PostgresError` y es la que usa el código de `asyncpg` al rechazar argumentos. La clasificación por `isinstance` **y** por prefijo de `sqlstate` cubre ambos casos; la tarea de `db_errors` incluye una prueba con excepciones reales de la librería y una prueba de integración con un `\u0000` forzado, de modo que el mapa se confirma contra el comportamiento real (research §7).

Cuando el escritor de **cuarentena** lanza cualquier excepción de las dos primeras filas, **no** se aplica este mapa: es error de base (reintento, sin recursión), según FR-011/FR-014.

## 7. Contadores de C8 (FR-023, FR-024, FR-036)

- `consumer/counters.py::Counters` en memoria: `received`, `new_events`, `newer_versions_applied`, `late_old_versions`, `redeliveries_ignored`, `same_updated_conflicts`, `ms_to_utc_conversions`, `nulls_kept` (por campo: `mag`, `depth_km`, `place`, `status`, `url`, `sig`, `mag_type`), `quarantined` (por motivo: filas nuevas) y `quarantine_duplicates` (por motivo). Nombres y significado: [contracts/consumer-runtime.md](contracts/consumer-runtime.md).
- Se actualizan **solo** en el paso 9 del flujo (tras el commit del offset), una vez por mensaje. Los reintentos no tocan nada.
- Se vuelcan (`reporting.dump_counters`) al registro en una línea `COUNTERS {json}` cada 60 s (`COUNTERS_LOG_INTERVAL_SECONDS`) y una vez al detenerse (manejador de `SIGTERM`/`SIGINT` en `main.py`, `stop_event` que `loop.py` comprueba en cada vuelta; al detenerse, `loop.py` cancela y espera a la corrutina periódica, que escribe el volcado final **solo al ser cancelada**).
- Las identidades de FR-023 son una función pura (`counters.check_identities(snapshot)`) que usan los tests y `verify_consumer.py`:
  1. `ms_to_utc_conversions = received − (cuarentenas de validación nuevas + duplicadas)`;
  2. `ms_to_utc_conversions = new_events + newer_versions_applied + late_old_versions + redeliveries_ignored + same_updated_conflicts + (db_constraint_violation nuevas + duplicadas)`.
  Aquí «cuarentenas de validación» = todas las de motivo ≠ `db_constraint_violation`.

**Cómo se verifican con base y grupo limpios.** `scripts/verify_consumer.py counters --case {faq12|invalid-twice|constraint-twice}` ejecuta: `docker compose build producer` (§8, imagen al día) → `docker compose down -v` (borra los volúmenes de PostgreSQL y de Kafka, por tanto la base y los offsets del grupo) → `docker compose up -d kafka postgres consumer` (**sin** productor, para que solo existan los mensajes de la prueba) → publica el caso con el servicio `tests` → espera a que el *lag* del grupo sea 0 → `docker compose stop consumer` (SIGTERM, resumen final) → lee la última línea `COUNTERS` y las cifras SQL (`count(*)` por tabla y motivo, con el rol administrador) → compara con las identidades y con las cifras esperadas de FR-036 (5/5; 7/5 con 1 nueva + 1 duplicada; 7/7). Los contadores viven en memoria: una sola sesión, sin reinicios, es condición de la prueba (SC-009).

## 8. Estrategia de tests

**Unitarios (sin Kafka ni PostgreSQL; `uv run pytest -m "not integration"` en el equipo del alumno).**
- `decode`: tombstone, vacío, UTF-8 inválido, BOM (`invalid_json`), UTF-16 (`invalid_json`), `\ud800`, JSON roto, 4301 dígitos, anidamiento profundo.
- `validation`: una prueba por motivo (14), el orden de prevalencia (mensaje con varios fallos → el primero), nulos/negativos válidos, los límites exactos (−10, 15, −100, 1000, 512 caracteres), `bool` como número, y la **tabla hostil** de US3.11 (cada fila con su motivo esperado; research §5).
- `validation` es *total*: un test de fuzz determinista (semilla fija, ~2000 mutaciones de un mensaje válido) comprueba que **nunca lanza** y siempre devuelve `ValidEvent` o `Rejection`.
- `storable`, `transform` (UTC, `date_id`, `dow`, extremos del rango), `quarantine_row` (regla de copia, saneado, SHA-256 de bytes, tombstone/vacío), `processing` (tabla de los 5 resultados), `catalog` (el archivo real: 177 filas, `ADM0_A3` único).
- `db_errors` con excepciones reales de `asyncpg` construidas a mano (`CheckViolationError`, `CharacterNotInRepertoireError`, `CannotConnectNowError`, `InterfaceError`, `OSError`…).
- `counters` (identidades de FR-023 con los tres casos de FR-036 como tablas de resultados) y `resilience` (secuencia de esperas 1, 2, 4, 8, 16, 30, 30; parada limpia; una línea de registro por intento).
- `pipeline` con escritor y reloj de mentira: orden `write → hook` y `ProcessingResult` correcto; cuarentena fallida ⇒ reintento sin recursión; fallo del escritor ⇒ `process_record` no devuelve resultado.
- `reporting`: formato de la línea de decisión y de `COUNTERS` (claves ordenadas); línea `broker_unreachable` emitida por `broker_reachable`.
- `loop` con consumidor y escritor de mentira: orden `write → hook → línea de decisión → commit offset → contadores`; fallo del escritor ⇒ el offset no se confirma y los contadores no cambian; `CommitFailedError` ⇒ no se cuenta (el mensaje reentregado se cuenta como nuevo: limitación de FR-023).
- Salvaguarda del hook (`fault_hook`): con `is_synthetic=false` no dispara aunque coincida el offset.

**Integración con PostgreSQL 16 real (`pytest -m integration`, dentro de la red de Compose).**
- Fixture de sesión: crea una **base temporal** (`observatory_test_<id>`) con el rol administrador, aplica `sql/001_schema.sql` (SQL puro, con `asyncpg` en una sola llamada) y reaplica las sentencias `GRANT` de `sql/002_roles.sql` leyéndolas del propio archivo (los roles ya existen en el clúster; el archivo usa metacomandos de `psql` que no se pueden ejecutar tal cual). Las pruebas escriben con `observatory_consumer` y **leen con el administrador** (el consumidor no tiene `SELECT` sobre la cuarentena). Al terminar se elimina la base.
- `test_faq12.py`: la secuencia de la FAQ 12 (5 mensajes) → 2 actuales, E1 con mag 4.6 y updated 10:09, 3 versiones (SC-001); y la versión antigua tardía *no vista* (prueba 4) como caso aparte.
- `test_idempotence.py`: reenviar 100 veces cada mensaje no cambia ninguna tabla (SC-002); conflicto «mismo `updated`, distinto contenido» conserva la primera; evento con `mag` nula y luego con `mag`.
- `test_quarantine.py`: latitud 145 (prueba 6, SC-004); cada motivo; duplicado por (hash, motivo); tombstone y vacío; hostiles con `original` a `NULL` y `raw_text` saneado; `db_constraint_violation` post-base (un `CHECK` añadido a la base temporal rechaza un id concreto, y un disparador de restricción *diferido* lo rechaza en el `COMMIT`) con rollback completo; `INSERT` de cuarentena fallido ⇒ reintento sin recursión; `event.id` de 512 caracteres se guarda.
- `test_roles.py`: con el rol real `observatory_consumer` (sin permisos añadidos): (a) `SELECT` en `live.quarantine` denegado (`42501`); (b) **la sentencia exacta de producción, `INSERT ... ON CONFLICT DO NOTHING` sin destino, inserta la primera vez (`INSERT 0 1`) y no falla ni exige `SELECT` con un duplicado (`INSERT 0 0`)**; (c) como prueba negativa que justifica la decisión, el destino con columnas, `ON CONFLICT (original_sha256, reason) DO NOTHING`, **da `42501`** con el rol real (queda como evidencia de por qué se usa la forma sin destino); (d) no puede escribir en `ingest.*`; (e) `live.event_version`: `INSERT` y `SELECT` permitidos y `UPDATE` denegado con `42501` (el historial es inmutable; `sql/002_roles.sql` concede `SELECT, INSERT`); sí puede `INSERT`/`UPDATE` en `live.current_event`, `INSERT` en `public.date_dim` e `INSERT`/`UPDATE` en `public.country` (los permisos de `db-schema.md` §1.1 que usa el escritor).
- `test_nulls_times.py`: `mag` nula → `NULL`; −0,06 y −0,18 conservados; pares UTC/ms coherentes (incluidos los extremos del rango de research §6); `date_id` existente en `date_dim`; `country_id` `NULL`; `ingested_at` ≠ tiempo del evento.
- `test_schema_parity.py` (FR-032): compara columnas (`information_schema.columns`), restricciones (`pg_get_constraintdef` con `live.`/`replay.` normalizados) e índices de las cuatro tablas de `live` y `replay`.
- `test_catalog_load.py`: 177 filas, segunda carga sin cambios.
- `test_restart_crash.py` (prueba 8, SC-005): hook que lanza `SimulatedCrash` tras el commit de PG; reinicio desde el último offset confirmado; la base queda idéntica a la ejecución sin corte (0 duplicados, 0 pérdidas).
- `test_counters_reconcile.py` (SC-009 en modo integración): los tres casos de FR-036 con `process_record` y contadores reales contra la base temporal; compara contadores con SQL.

**Imagen al día (decisión provisional, §13.10).** Solo `producer` tiene `build:`; `consumer` y `api` reutilizan la imagen por nombre (`pull_policy: never`) y `up --build` sobre `consumer` **no** la reconstruye (no depende de `producer`). Una imagen vieja ejecutaría el consumidor mínimo de `002` y falsearía la evidencia. Por tanto: (a) antes de **cada** escenario de `verify_consumer.py` y de la regresión de `002` se ejecuta `docker compose build producer`; **`verify_consumer.py` lo hace como primer paso** de cada escenario, antes de `down -v`/`up`; (b) para el servicio `tests`, `docker compose --profile test build tests` (o `docker compose --profile test run --rm --build tests …`) antes de ejecutar pytest, porque la etapa `test` copia `common/` y `consumer/`. Solo `producer` conserva `build:`.

**Punta a punta con Docker (`scripts/verify_consumer.py`)**: escenarios `faq12`, `quarantine`, `restart` (hook por variable de entorno, prueba 8), `pg-down` (SC-006), **`kafka-down`** (US2.5, FR-029), `counters` (SC-009) y `catalog` (SC-011). Cada uno guarda su salida en `docs/evidencias/consumidor-idempotente/`.

`kafka-down`: con el consumidor sano y unos mensajes ya guardados, `docker compose stop kafka`; se comprueba que el consumidor sigue vivo, registra el fallo del broker (línea `broker_unreachable` de [consumer-runtime.md](contracts/consumer-runtime.md) §4, que emite `broker_reachable` en cada sondeo fallido) y reintenta (sin traza fatal), y el contenedor pasa a `unhealthy` (el latido no se renueva con el broker inalcanzable, `config.md` §E); luego `docker compose start kafka`, se publican mensajes nuevos y se comprueba que retoma el consumo, que el latido vuelve a `healthy` y que las cifras SQL no tienen pérdidas ni duplicados (conteo por `event_id` y por `(event_id, updated_ms)`). Si Kafka vuelve con el volumen intacto, los offsets del grupo se conservan; el escenario no usa `down -v`.

**Regresión de `002`.** Al cerrar: `uv run python scripts/check_env_example.py`, los tests existentes de `002` (`uv run pytest -m "not integration"`) y `python scripts/verify_stack.py` deben pasar, con `verify_stack.py` actualizado (§12).

**Notas para `tasks.md`.** (a) El publicador de los escenarios vive en `tests/support/publish_messages.py` (véase «Source Code» en Project Structure). (b) SC-008 pide «0 filas reales con la marca»: además de los fixtures sintéticos, `test_quarantine.py` y `test_nulls_times.py` incluyen un caso con `is_synthetic=false` (mensaje real simulado, solo en la base temporal de pruebas, nunca en la base de la aplicación) y comprueban que la marca queda `false` en las tres tablas. (c) FR-035 se comprueba al cierre con `git diff --stat -- specs/001-contratos-y-modelo/contracts/` (vacío).

**Evidencia SQL**: consultas fijas de [quickstart.md](quickstart.md) §5 (antes/después) guardadas como `.sql` + salida. FR-031 queda cubierto por el test de la FAQ 12 y por esa consulta.

## 9. Menores heredados de clarify (cierre en el plan)

| Menor | Decisión del plan | Dónde |
|---|---|---|
| Justificación de FR-023 de conversión en `db_constraint_violation` | La transformación (ms → UTC) ocurre antes de saber si la base aceptará el mensaje; por eso un mensaje que acaba en `db_constraint_violation` ya consumió su conversión y la cuenta. Un rechazo de validación no transforma nada, así que no la cuenta. La identidad 2 de §7 lo hace comprobable. | research §10 |
| `1e400` (`inf` en Python, válido en `numeric`) | Se trata como no finito tras deserializar (criterio de FR-014 punto 2): `mag` → `mag_out_of_range`; coordenadas → `coordinates_out_of_range`; en un campo no validado de otro modo (`dmin`) → `db_constraint_violation`. Regla única: «no finito en Python = no almacenable», porque el consumidor no puede garantizar que lo que guarda sea lo que llegó. | research §5 |
| Enteros > 4300 dígitos | `json.loads` lanza `ValueError` (límite de dígitos de Python 3.12); se captura y es `invalid_json`. **No** se toca `sys.set_int_max_str_digits`. Los enteros ≤ 4300 dígitos en campos no validados (p. ej. `nst`) pasan: caben en `jsonb`. | research §5 |
| Cuarentena sin `SELECT` | Solo `INSERT ... ON CONFLICT DO NOTHING` **sin destino de conflicto** (única forma admitida; no se usa `ON CONSTRAINT`, que también podría exigir `SELECT`), sin `RETURNING`. Se evita el destino `(original_sha256, reason)` porque PostgreSQL marca las columnas del destino con privilegio `SELECT` y el rol solo tiene `INSERT` (`sql/002_roles.sql`): daría `42501`, que se reintentaría sin fin. La tabla tiene una sola restricción única, así que la forma sin destino cubre exactamente el mismo caso. «Fila nueva / duplicada» se lee de la etiqueta (`INSERT 0 1` / `INSERT 0 0`). Lo demuestra `test_roles.py` con el rol real: (b) la forma sin destino funciona y (c) el destino con columnas da `42501`. Las pruebas leen con el administrador. | §8, research §8 |
| Cuarentena por bytes, no por contenido semántico | Documentado en `data-model.md` y en la memoria: el mismo JSON con otra serialización crea otra fila. | data-model §5 |
| Tope de espera y tasa de registro | Valores de §5. | §5 |

## 10. Trazabilidad requisito → módulo → prueba

| Requisito | Módulo (diseño) | Prueba |
|---|---|---|
| C1, FR-003, FR-004, FR-034 | `common/validation.py`, `consumer/pipeline.py`, `consumer/reporting.py`; `docs/memoria.md` §4 | `tests/common/test_validation.py`, línea de registro por decisión (`tests/consumer/test_reporting.py`, `test_consumer_loop.py`); revisión de `docs/memoria.md` |
| C2, FR-001, FR-002, US2.5 | `consumer/pipeline.py`, `consumer/loop.py`, `consumer/resilience.py` (commit con reintento) | `tests/consumer/test_consumer_loop.py` (orden decisión / commit offset / contadores), `test_pipeline.py`, `test_restart_crash.py` (prueba 8), `verify_consumer.py restart` y `kafka-down` |
| C3, FR-005, FR-006, FR-010 | `consumer/writer.py`, `consumer/queries.py` | `tests/integration/test_idempotence.py` (SC-002), `test_faq12.py` |
| C4, FR-007, FR-008, FR-009 | `common/processing.py`, `consumer/writer.py` | `tests/common/test_processing.py`, `test_faq12.py` (pruebas 3 y 4, SC-003) |
| C5, FR-011, FR-012, FR-013, FR-015 | `common/quarantine_row.py`, `common/storable.py`, `consumer/writer.py` | `tests/common/test_quarantine_row.py`, `tests/integration/test_quarantine.py` (prueba 6, SC-004) |
| FR-014 (reintentos, clases 22/23, regla general) | `consumer/db_errors.py`, `consumer/resilience.py`, `common/validation.py`, `common/storable.py` | `tests/consumer/test_db_errors.py`, `test_resilience.py`, `tests/common/test_validation.py` (tabla hostil + fuzz), `test_quarantine.py` (`db_constraint_violation` post-base), `verify_consumer.py pg-down` (SC-006) |
| C6, FR-016, FR-017 | `common/validation.py`, `common/transform.py` | `tests/common/test_validation.py`, `tests/integration/test_nulls_times.py` (SC-007) |
| C7, FR-018, FR-019, FR-020, FR-021 | `common/transform.py`, `consumer/writer.py` | `tests/common/test_transform.py`, `test_nulls_times.py` |
| C8, FR-023, FR-024, FR-036 | `consumer/counters.py`, `consumer/reporting.py` (línea `COUNTERS`), `consumer/loop.py` | `tests/consumer/test_counters.py`, `test_reporting.py`, `test_counters_reconcile.py`, `verify_consumer.py counters` (SC-009) |
| C13, FR-022 | `common/transform.py`, `common/quarantine_row.py` | `test_nulls_times.py`, `test_quarantine.py` (SC-008: `is_synthetic` en las tres tablas) |
| FR-025, FR-026 | `common/catalog.py`, `consumer/catalog_loader.py`, `consumer/schema_check.py` | `tests/common/test_catalog.py`, `tests/integration/test_catalog_load.py`, `verify_consumer.py catalog` (SC-011) |
| FR-027 | `consumer/main.py` (`DB_USER=observatory_consumer`), `sql/002_roles.sql` | `tests/integration/test_roles.py` |
| FR-028 | `consumer/loop.py::start_consumer` (`group_id`, `auto_offset_reset="earliest"`) | `verify_consumer.py restart` (reanuda desde el offset confirmado) |
| FR-029 | `consumer/loop.py` (incluye `broker_reachable` y su línea `broker_unreachable`), `common/health.py` | `verify_consumer.py pg-down` y `kafka-down` (`unhealthy` y recuperación) |
| FR-030, SC-010 | `common/*` (sin imports de `asyncpg`/`aiokafka`) | `tests/common/*` ejecutan sin red; una prueba comprueba que `common/` no importa `asyncpg` ni `aiokafka` (módulos de decisión) |
| FR-031 | — | `test_faq12.py` + consulta de [quickstart.md](quickstart.md) §5 |
| FR-032 | — | `tests/integration/test_schema_parity.py` |
| FR-033 | — | marcador `integration` separa los dos niveles |
| FR-034, FR-035, SC-012 | documentación | `docs/evidencias/consumidor-idempotente/`, `docs/memoria.md` §4, `README.md`, `CODEMAP.md`; revisión de [quickstart.md](quickstart.md); FR-035 (no tocar `kafka-message.md`, `db-schema.md`, `api.md`): `git diff --stat -- specs/001-contratos-y-modelo/contracts/` vacío al cierre |
| Pruebas de aceptación 2, 3, 4, 6, 8 | ver arriba | 2: `test_idempotence.py`; 3 y 4: `test_faq12.py`; 6: `test_quarantine.py`; 8: `test_restart_crash.py` + `verify_consumer.py restart` |

## 11. Evidencias previstas (`docs/evidencias/consumidor-idempotente/`)

`faq12_antes_despues.sql` y `.out` (SC-001); `prueba2_reenvio.out`; `prueba3_4_versiones.out`; `prueba6_cuarentena.out` (fila con motivo y referencia); `prueba8_reinicio.log` y `.out` (logs del corte y de la reentrega + SQL idéntico); `contadores_faq12.out`, `contadores_invalido_repetido.out`, `contadores_constraint_repetido.out` (SC-009); `pg_caida.log` (SC-006, `unhealthy` y recuperación); `catalogo_paises.out` (177 filas, repetición); `kafka_caida.log` (US2.5, FR-029); `regresion_002.txt` (salida de `verify_stack.py`, `check_env_example.py` y tests de `002`); `contratos_sin_cambios.txt` (`git diff --stat` vacío, FR-035); `pytest_unitarias.txt`, `pytest_integracion.txt`; `roles_consumidor.out`.

**Entregable de memoria (C1, FR-034).** `docs/memoria.md` §4 «Calidad» (hoy vacío) recibe un resumen breve de las reglas de validación y calidad implementadas (orden de prevalencia, nulos y negativos válidos, cuarentena con motivo, regla general de no fallo por contenido, idempotencia, **transacción única por mensaje, orden de commits —PostgreSQL, línea de decisión, offset, contadores— y la secuencia de la FAQ 12 con su resultado**), **con referencias** a `kafka-message.md` §6, a `db-schema.md` §5 y a la spec/plan de la feature; no copia texto de `specs/` a `docs/` (constitución §18, §15).

## 12. Archivos existentes que la implementación tocará (para `tasks.md`; no se tocan aquí)

Son cambios en la infraestructura de `002`, no en contratos ni en DDL:

- `Dockerfile`: **nombrar las etapas** (`FROM ... AS production` para la actual, sin cambiar su contenido, y `FROM production AS test` o equivalente para la nueva) y añadir la etapa `test`, que instala también el grupo `dev` (`uv sync --frozen --no-install-project`). `FROM production AS test` hereda `USER observatory` y `uv sync` sobre `/opt/venv` necesita root: la etapa `test` pone `USER root` antes de `uv sync` y **vuelve a `USER observatory`** al terminar. Motivo: una etapa `test` añadida al final sería el *target* por defecto y `docker compose build` de `producer`/`consumer`/`api` construiría la imagen compartida con dependencias de desarrollo.
- `compose.yaml`: **solo `producer`** (el único servicio con `build:`) fija `build: target: production` de forma explícita; `consumer` y `api` **no** ganan `build:` (construir la misma etiqueta tres veces provoca el conflicto que advierte el comentario de `compose.yaml`) y siguen reutilizando la imagen por nombre. Por eso la imagen puede quedar desfasada: ver «Imagen al día» en §8. El servicio `tests` **no hereda** el ancla `x-python-service` (esta fija `image: seismic-observatory-python:0.1.0`, `pull_policy: never` y `restart`): lleva su propio `build: target: test`, su propia imagen (otro nombre), sin `restart` y con **`networks: [backend]` declarado explícitamente** (sin el ancla no tendría red). Detalles: `.pytest_cache` no puede escribirse en los montajes de solo lectura, así que el servicio fija un directorio escribible para la caché (p. ej. `-p cache_dir=/tmp/pytest_cache` o `PYTEST_ADDOPTS`) o la desactiva (`-p no:cacheprovider`); la variable del hook se interpola como **`CONSUMER_FAULT_CRASH_AT_OFFSET: ${CONSUMER_FAULT_CRASH_AT_OFFSET:-}`** (con `:?` una variable vacía rompería `compose`), y `check_env_example.py` exige que figure en `.env.example` y en `compose.yaml`. (a) `consumer`: montaje de solo lectura `./data/catalogo:/app/data/catalogo:ro` y variables `COUNTRY_CATALOG_PATH` (constante de diseño, como `HEALTH_FILE`) y `CONSUMER_FAULT_CRASH_AT_OFFSET`; (b) servicio `tests` bajo `profiles: ["test"]` (no arranca con `up`, así siguen siendo cinco servicios) con `./tests`, `./sql` y `./data/catalogo` montados en solo lectura y las credenciales de administrador y de consumidor que ya existen en `.env`.
- `scripts/verify_stack.py` (**regresión de 002**): `check_synthetic_event_in_consumer_log` (A1, líneas 90-99) busca `[SINTÉTICO]` y `synthetic-` en el log del consumidor; ese formato desaparece con `describe_message`. **Opción elegida: actualizar el check** para que reconozca la línea de decisión de [consumer-runtime.md](contracts/consumer-runtime.md) §4 (`decision=… event_id=synthetic-…`), sin exigir `[SINTÉTICO]`. Motivo: es un cambio de una línea en un script de verificación, mientras que conservar `[SINTÉTICO]` obligaría a meter en las líneas de decisión de producción un marcador que solo existe para un check heredado, y un evento sintético ya se reconoce por su `event_id` `synthetic-…` y por `is_synthetic` en la base. Tarea de regresión: ejecutar `verify_stack.py`, `scripts/check_env_example.py` y los tests de `002` tras todos los cambios de infraestructura, y guardar la salida en `docs/evidencias/consumidor-idempotente/regresion_002.txt`. Antes de ejecutarla, `docker compose build producer` (imagen al día, §8). Tras `down`/`up` el grupo conserva su offset, así que A1 ya no relee desde el principio: **depende de que el productor publique un evento nuevo** (`PRODUCER_INTERVAL_SECONDS` admite hasta 60) dentro de `EVENT_TIMEOUT_SECONDS` = 60 s de `verify_stack.py`; la tarea anota qué ocurre si el intervalo configurado es largo. Nota: el evento sintético del productor de `002` debe poder validarse; si se rechaza, la línea `decision=quarantined … event_id=synthetic-…` también satisface el check, pero la tarea debe comprobar qué ocurre y anotarlo.
- `.env.example`: `KAFKA_GROUP_ID=consumer-live` (el grupo deja de llamarse `consumer-minimal`) y `CONSUMER_FAULT_CRASH_AT_OFFSET=` (vacía, solo para la prueba 8).
- `scripts/check_env_example.py` y `specs/002-infra-compose/contracts/config.md`: reflejar las variables nuevas (la lectura opcional de una variable vacía requiere `read_optional_int` en `common/config.py`).
- `pyproject.toml`: el marcador `integration` en `[tool.pytest.ini_options]`.
- `README.md` y `CODEMAP.md`: cierre de feature. En `README.md` (línea ~80, «Comprobar») hay que sustituir la cita de las líneas «Evento recibido [SINTÉTICO] …» por la línea de decisión (`decision=… event_id=synthetic-…`), porque `describe_message` desaparece.
- `docs/memoria.md` §4: ver el entregable de §11 (con transacción, orden de commits y secuencia de la FAQ 12).
- `common/retry.py` no cambia (se reutiliza `next_delay`); `common/db.py` se reutiliza (`create_pool_with_retry`, `COMMAND_TIMEOUT_SECONDS = 5`).

## 13. Decisiones discutibles y escalados

**Escalados (algo exigiría cambiar contrato, DDL o alcance): ninguno.** Se anotan aquí por si el alumno discrepa:

1. **Servicio `tests` en un perfil de Compose y etapa `test` del `Dockerfile`** (§12): necesario porque la base no se publica (§10) y la imagen de producción excluye `tests/` y las dependencias de desarrollo. Alternativa: publicar `127.0.0.1:5432` solo para pruebas (viola el espíritu de §10) o no tener pruebas de integración (incumple FR-033).
2. **Rango de tiempos admitido: años 1000-2999** (research §6), más estricto que el de `timestamptz`; el contrato (`kafka-message.md` §6, `value_out_of_range`) y FR-014 punto 2 delegan en el plan fijarlo. Se escoge para que el `CHECK` de coherencia `*_at = epoch + *_ms * interval` sea exacto (la multiplicación `interval * bigint` usa `double`) y para que quepa en `date_dim.year smallint`. Los extremos se comprueban solo con SQL en T093, antes de construir `transform`/`validation`; si el `CHECK` no los aceptara, se escala al alumno (rehacer T021-T025, research §6, consumer-runtime §1 y este punto).
3. **Profundidad máxima de JSON 64** (research §5): salvaguarda propia, no del contrato, para que un anidamiento extremo no pueda provocar un error `54001` persistente en `jsonb`. Se trata como «no almacenable».
4. **Hook de prueba activable por variable de entorno** (`CONSUMER_FAULT_CRASH_AT_OFFSET`): añade código de prueba al servicio de producción, desactivado por defecto. Alternativa: solo el hook en proceso de pytest (sin evidencia con contenedor real).
5. **Commit de offset por mensaje** y `getmany(max_records=1)`: más lento que por lote, más simple de razonar y de demostrar (research §9).
6. **Saneado de `event_id` y `source` en cuarentena = poner `NULL`** si contienen NUL/sustitutos o superan 512 caracteres (research §4), en vez de escaparlos: un identificador escapado engañaría a `ix_quarantine_event_id`.
7. **Re-serialización del `original`**: `json.dumps` del objeto deserializado; los valores se conservan, el formato numérico se normaliza (`1E5` pasa a `100000.0`) y `jsonb` ya normaliza espacios y orden. **Pérdida de precisión (decisión provisional)**: al deserializar con `float`, un número con más de ~17 dígitos significativos pierde precisión y un valor como `1e-400` pasa a `0.0` sin aviso (y `1e400` ya es «no finito», research §5). Se acepta porque los campos numéricos de USGS caben en `float` y `FR-020` se interpreta como «los valores del feed íntegros»; solo la cuarentena conserva los bytes exactos (vía el hash y, si no es JSON, `raw_text`). Alternativa: `json.loads(parse_float=Decimal)`, que conservaría los dígitos pero cambiaría las comprobaciones de rango y finitud (research §3, §5); se descarta por tamaño. El alumno decide si prefiere `Decimal`.
8. **Los tres temas «Pendientes de confirmar» de la spec** (regla general de no fallo por contenido, regla de copia, y las preguntas 3 y 4 abiertas) se **asumen con la recomendación de la spec**; si el alumno decide otra cosa, cambian research §3-§5 y las tareas de validación.
9. **Decisiones de la revisión del plan (provisionales)**: (a) el bucle `loop.py` confirma el offset y llama a `counters`; `process_record` termina en el hook (§1); (b) no existe `common.processing.process_event()`: la lógica se reparte entre `common/*` y `consumer/writer.py` (§2); (c) cuarentena con `ON CONFLICT DO NOTHING` sin destino (§9); (d) regresión de `002`: se actualiza `verify_stack.py` en lugar de conservar `[SINTÉTICO]` (§12); (e) escenario `kafka-down` (§8); (f) `docs/memoria.md` §4 como entregable (§11); (g) BOM y UTF-16 → `invalid_json` por decodificación UTF-8 estricta previa (§2); (h) hook de crash solo con `is_synthetic=true` (§4); (i) etapas nombradas en el `Dockerfile` y `target:` explícito en compose, `tests` sin el ancla `x-python-service` (§12); (j) publicador en `tests/support/` (§8).
10. **Decisiones de la segunda vuelta de revisión (provisionales)**: (a) imagen desfasada: `docker compose build producer` antes de cada escenario de `verify_consumer.py` (primer paso del script) y de la regresión de `002`, y `docker compose --profile test build tests` (o `run --build`) antes de pytest; solo `producer` conserva `build:` con `target: production` (§8, §12); (b) cuarentena solo con `ON CONFLICT DO NOTHING` sin destino; `ON CONSTRAINT` descartado, y `test_roles` (c) prueba que el destino con columnas da `42501` (§8, §9); (c) la línea de decisión se escribe tras el commit de PostgreSQL y antes del commit del offset, y los contadores tras el commit del offset; una reentrega duplica la línea de decisión, aceptable (§1); (d) `broker_reachable` emite la línea `broker_unreachable` (consumer-runtime §4); (e) `loop.py` se divide en `loop.py` (bucle, sondeo, latido, parada), `reporting.py` (línea de decisión y volcado de `COUNTERS`) y `resilience.py` (commit con reintento) para respetar el límite de 250 líneas (Project Structure); (f) `docs/memoria.md` §4 incluye transacción, orden de commits y secuencia de la FAQ 12 (§11); (g) el README (línea ~80) deja de citar `[SINTÉTICO]` (§12); (h) detalles del `Dockerfile` y de `compose.yaml` de §12 (`USER root`, `networks`, interpolación `${…:-}`, caché de pytest).
11. **Decisiones de la revisión del análisis (provisionales)**: (a) como `tests/` no tiene `__init__.py`, los nombres base de las pruebas son únicos en todo `tests/`: el bucle del consumidor se prueba en `tests/consumer/test_consumer_loop.py` (ya existe `tests/producer/test_loop.py`); se comprueba con `uv run pytest --collect-only -q`; (b) `test_roles` (e) afirma `INSERT` y `SELECT` permitidos y `UPDATE` denegado (`42501`) sobre `live.event_version`, según `sql/002_roles.sql` (el DDL y los permisos no cambian); (c) la corrutina periódica de `reporting` escribe el volcado final **solo al ser cancelada** por el bucle (no mira `stop_event`); (d) las garantías de FR-003 y de duplicación de la línea de decisión se redactan según §1 (muerte entre 5 y 7: sin línea; entre 7 y 8: línea duplicada).

## Hallazgos

_(Sección reservada para los hallazgos de `/speckit-analyze` y de la revisión del plan. Vacía a propósito.)_
