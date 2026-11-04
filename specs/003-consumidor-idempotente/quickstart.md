# Quickstart: verificar el consumidor idempotente

Guía de validación (no contiene el código de las pruebas). Los comandos de las secciones 3 a 6 existirán cuando se implemente la feature; la guía fija **qué se ejecuta y qué debe salir**. Los datos de la secuencia están en [data-model.md](data-model.md) §4; las variables y las líneas de registro, en [contracts/consumer-runtime.md](contracts/consumer-runtime.md).

## 1. Requisitos

- Docker con Compose v2 y un archivo `.env` copiado de `.env.example` (`KAFKA_GROUP_ID=consumer-live`).
- Para las pruebas unitarias en el equipo: Python 3.12 y `uv` (`uv sync`).
- Todos los datos de prueba son sintéticos (`is_synthetic = true`, ids `synthetic-…`) y no se mezclan con datos reales (constitución §7).

## 2. Arranque limpio (SC-011)

La imagen es compartida y solo `producer` tiene `build:`: `up --build` sobre `consumer` **no** la reconstruye y un `consumer` con imagen vieja ejecutaría el consumidor mínimo de `002`. Por eso se reconstruye siempre antes (`verify_consumer.py` lo hace como primer paso de cada escenario).

```text
docker compose build producer                              # imagen al día (producer es el único servicio con build:)
docker compose down -v
docker compose up -d kafka postgres consumer              # sin productor: solo existirán los mensajes de la prueba
docker compose ps                                          # consumer: healthy
docker compose logs consumer                               # buscar la línea "catalog loaded": total=177
```

Para filtrar el registro: en PowerShell, `docker compose logs consumer | Select-String "catalog loaded"`; en sh/bash, `docker compose logs consumer | grep "catalog loaded"`.

Comprobación SQL (con el administrador): `SELECT count(*) FROM public.country;` → **177**. Reiniciar el consumidor (`docker compose restart consumer`) y repetirlo → sigue en **177** y el registro dice `inserted=0 updated=0`.

## 3. Pruebas unitarias (sin Kafka ni PostgreSQL, FR-033)

```text
uv run pytest -m "not integration"
```

Esperado: todas pasan; incluyen la tabla hostil (US3.11), el fuzz determinista, las identidades de los contadores y el orden `escritura → hook → línea de decisión → commit de offset → contadores`.

## 4. Pruebas de integración (PostgreSQL 16 real, dentro de la red de Compose)

```text
docker compose up -d postgres
docker compose --profile test build tests                  # la etapa test copia common/ y consumer/: sin esto pueden estar desfasados
docker compose --profile test run --rm tests pytest -m integration -q
```

Esperado: pasan `test_faq12` (SC-001), `test_idempotence` (SC-002, SC-003), `test_quarantine` (SC-004, SC-008), `test_roles`, `test_nulls_times` (SC-007), `test_schema_parity` (FR-032), `test_catalog_load`, `test_restart_crash` (SC-005) y `test_counters_reconcile`. La base temporal se elimina al terminar; la base de la aplicación no se toca.

## 5. Secuencia de la FAQ 12 con Kafka real (SC-001, SC-012, pruebas 2, 3, 4)

```text
python scripts/verify_consumer.py faq12 --yes     # --yes (o VERIFY_CONSUMER_CONFIRM=yes) confirma el down -v, que borra los volúmenes locales
```

Hace: `docker compose build producer` (primer paso); `down -v`; levanta `kafka postgres consumer`; publica los 5 mensajes de [data-model.md](data-model.md) §4 en `earthquakes.live`; espera a que el grupo no tenga *lag*; ejecuta la consulta de evidencia y compara.

Consulta de evidencia (se guarda como `docs/evidencias/consumidor-idempotente/faq12_antes_despues.sql`):

```sql
SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY event_id;
SELECT event_id, updated_ms, mag FROM live.event_version ORDER BY event_id, updated_ms;
SELECT count(*) AS current_rows FROM live.current_event;
SELECT count(*) AS version_rows FROM live.event_version;
```

Esperado:

| Resultado | Valor |
|---|---|
| `live.current_event` | 2 filas: `synthetic-faq12-e1` (mag 4.6, updated 1793786940000) y `synthetic-faq12-e2` (mag 3.1) |
| `live.event_version` | 3 filas: E1 con 1793786700000 y 1793786940000; E2 con 1793787120000 |
| `COUNTERS` (tras `docker compose stop consumer`) | `received=5`, `new_events=2`, `newer_versions_applied=1`, `redeliveries_ignored=2`, `ms_to_utc_conversions=5` |

Prueba 2 (reenvío): reenviar 100 veces el mensaje 1 → los dos `count(*)` no cambian. Prueba 4 con versión antigua *no vista*: publicar E1 con `updated` 1793786820000 (10:07) y mag 4.4 → `current_event` sigue en 4.6 y `event_version` pasa a 4 filas.

## 6. Escenarios restantes de `verify_consumer.py`

Todos los escenarios que ejecutan `down -v` (todos salvo `kafka-down`) llevan `--yes` (o la variable `VERIFY_CONSUMER_CONFIRM=yes`): sin ella el script avisa de que se borran los volúmenes locales de Kafka y PostgreSQL y termina con código 2 sin hacer nada destructivo. Se invocan como `python scripts/verify_consumer.py <escenario> --yes`.

| Comando | Qué demuestra | Esperado |
|---|---|---|
| `quarantine --yes` | Prueba 6 (SC-004): mensaje con latitud 145 seguido de uno válido; más un NUL, bytes no UTF-8, tombstone, `mode = replay` | 1 fila por mensaje inválido en `live.quarantine` (leída con el administrador) con motivo, `kafka_topic/partition/offset` y `original_sha256` de 64 hex; 0 filas en `current_event` para ellos; el válido guardado; el consumidor sigue sano |
| `restart --yes` | Prueba 8 (SC-005): con `CONSUMER_FAULT_CRASH_AT_OFFSET=2` el proceso termina tras el commit de PG del offset 2; Compose lo reinicia | Registro `FAULT crash_after_db_commit offset=2`; tras el reinicio, `decision=redelivery_ignored` para ese offset; SQL idéntico al de la ejecución sin corte; 0 duplicados, 0 pérdidas |
| `pg-down --yes` | SC-006, FR-029: `docker compose stop postgres` durante el consumo y `start` después | Líneas `retry attempt=…` con `event_id`, tema, partición y offset (≤ 2 por minuto en régimen); ningún offset confirmado sin guardar; el contenedor pasa a `unhealthy` y vuelve a `healthy` al recuperar la base; todos los mensajes pendientes quedan guardados sin intervención |
| `kafka-down` | US2.5, FR-029: `docker compose stop kafka` durante el consumo y `start` después (sin `down -v`) | El consumidor sigue vivo y reintenta sin traza fatal; pasa a `unhealthy` y vuelve a `healthy`; tras publicar mensajes nuevos se guardan todos, sin pérdidas ni duplicados (cifras SQL) |
| `counters --case faq12 --yes` / `invalid-twice` / `constraint-twice` (con `--yes`) | SC-009 (FR-036): base y grupo limpios, una sola sesión | Casos 1, 2 y 3 de la tabla de [data-model.md](data-model.md) §4: contadores = cifras SQL y las identidades se cumplen |
| `catalog --yes` | SC-011 | 177 filas; repetir el arranque no cambia el número |

Cada escenario ejecuta `docker compose build producer` como primer paso (imagen al día, ver §2) y, si usa el servicio `tests` para publicar, `docker compose --profile test build tests`. En `kafka-down` el consumidor registra `broker_unreachable` ([consumer-runtime.md](contracts/consumer-runtime.md) §4) y la prueba lo busca en el registro. Tras `down`/`up`, la comprobación A1 de `verify_stack.py` depende de que el productor publique un evento nuevo (el grupo conserva su offset; el límite es `EVENT_TIMEOUT_SECONDS` = 60 s).

Cada escenario escribe su salida en `docs/evidencias/consumidor-idempotente/` y devuelve código de salida 0 solo si todo coincide.

## 7. Leer la cuarentena

El rol del consumidor no puede hacer `SELECT` sobre la cuarentena; se lee con el administrador:

```text
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, reason, event_id, source, is_synthetic, kafka_topic, kafka_partition, kafka_offset, left(original_sha256, 12) AS sha, original IS NOT NULL AS has_json, left(raw_text, 40) AS raw FROM live.quarantine ORDER BY id"'
```

## 8. Cierre (constitución §16)

Antes de dar la feature por terminada: pruebas unitarias e integración ejecutadas, regresión de `002` (antes, `docker compose build producer`; luego `python scripts/verify_stack.py`, `uv run python scripts/check_env_example.py`), `git diff --stat -- specs/001-contratos-y-modelo/contracts/` vacío (FR-035), evidencias en `docs/evidencias/consumidor-idempotente/`, `docs/memoria.md` §4, `README.md` y `CODEMAP.md` actualizados, y parada para revisión del alumno (sin commit ni merge).
