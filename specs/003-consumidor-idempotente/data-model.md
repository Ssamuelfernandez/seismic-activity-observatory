# Modelo de datos del procesamiento: Consumidor idempotente

Esta feature **no crea ni cambia tablas**: usa el DDL de [`sql/001_schema.sql`](../../sql/001_schema.sql) y los permisos de [`sql/002_roles.sql`](../../sql/002_roles.sql) tal cual. Las columnas y claves se describen en `specs/001-contratos-y-modelo/contracts/db-schema.md` (no se repiten aquí). Este documento define lo que el contrato no cubre: las estructuras en memoria del procesamiento, el mapeo mensaje → columnas, el resultado de cada versión y el cálculo de los contadores.

## 1. Estructuras en memoria (`common/records.py`, inmutables)

| Estructura | Campos | Para qué |
|---|---|---|
| `MessageRef` | `topic`, `partition`, `offset` | Referencia al mensaje (columnas `kafka_*`; datos del registro de cada intento). |
| `DecodeResult` | `raw: bytes`, `obj: Any \| None`, `ok: bool` | Resultado de `decode_value`. `ok = False` ⇒ `invalid_json`. `raw` es siempre `bytes` (vacío si el valor Kafka era nulo). |
| `ValidEvent` | `envelope` (source, mode, ingested_at, replay_at, is_synthetic ya tipados), `event` (el objeto original), campos extraídos: `event_id`, `time_ms`, `updated_ms`, `mag`, `depth`, `lon`, `lat`, `place`, `status`, `url`, `sig`, `mag_type` | Mensaje que pasó los 14 motivos. |
| `Rejection` | `reason` (uno de los 14 de `kafka-message.md` §6) | Resultado negativo de `validate_message`. |
| `EventRows` | `current`: dict de columnas de `current_event`; `version`: dict de columnas de `event_version`; `date`: (`date_id`, `year`, `month`, `day`, `dow`); `nulls`: tupla de campos nulos | Salida de `build_event_rows`. `country_id` no aparece. |
| `QuarantineRow` | `event_id`, `reason`, `original` (texto JSON o `None`), `raw_text`, `original_sha256`, `source`, `kafka_topic`, `kafka_partition`, `kafka_offset`, `received_at`, `is_synthetic` | Salida de `build_quarantine_row`; se corresponde 1:1 con las columnas de `quarantine` salvo `id`. |
| `VersionOutcome` (enum) | `NEW_EVENT`, `NEWER_VERSION`, `LATE_OLD_VERSION`, `REDELIVERY`, `SAME_UPDATED_CONFLICT` | Qué pasó con la versión (§3). |
| `ProcessingResult` | `kind` (`EVENT` \| `QUARANTINE`), `outcome` (si `EVENT`), `reason` y `inserted: bool` (si `QUARANTINE`; `False` = duplicado), `converted: bool`, `nulls`, `updated_ms: int \| None` (el `updated` del evento si `EVENT`; `None` si `QUARANTINE`; lo usa `log_decision` para la línea `same_updated_conflict`) | Lo que `pipeline.process_record` devuelve a `loop` para actualizar contadores y registro. |
| `Counters` | los contadores de [contracts/consumer-runtime.md](contracts/consumer-runtime.md) §3 | Estado en memoria de la sesión. |

## 2. Mapeo mensaje → columnas

Todas las columnas de texto y fecha salen de campos ya validados (nunca se escribe un valor sin haber comprobado su tipo, plan §3 y research §3).

### `{live}.current_event` (una fila por evento)

| Columna | Origen | Transformación |
|---|---|---|
| `event_id` | `event.id` | — (≤ 512 caracteres) |
| `event_time`, `event_time_ms` | `event.properties.time` | `ms_to_utc(ms)`; `ms` se guarda tal cual |
| `updated_at`, `updated_ms` | `event.properties.updated` | ídem |
| `mag` | `event.properties.mag` | `Decimal(str(x))`; `null` → `NULL` (nunca 0) |
| `mag_type` | `event.properties.magType` | `null` → `NULL` |
| `depth_km` | `event.geometry.coordinates[2]` | `Decimal(str(x))`; ausente o `null` → `NULL` |
| `lon`, `lat` | `coordinates[0]`, `coordinates[1]` | `float(x)` (tras comprobar rango) |
| `place`, `status`, `url` | `event.properties.*` | `null` → `NULL` |
| `sig` | `event.properties.sig` | entero (`int32`); `null` → `NULL` |
| `country_id` | — | **no se escribe** (queda `NULL`; FR-021) |
| `date_id` | `event_time` | `event_time.date()` en UTC (`CHECK` de coherencia del DDL) |
| `source`, `is_synthetic`, `ingested_at`, `replay_at` | sobre | copiados (`ingested_at`/`replay_at` parseados a `datetime` UTC) |

`DO UPDATE` actualiza todas las columnas anteriores salvo `event_id` y `country_id`, solo si `EXCLUDED.updated_ms > current_event.updated_ms`.

### `{live}.event_version` (una fila por `(event_id, updated_ms)` recibido)

| Columna | Origen |
|---|---|
| `event_id`, `updated_ms`, `updated_at`, `event_time`, `mag`, `depth_km` | como en `current_event` |
| `original` | `event` íntegro (`json.dumps(..., ensure_ascii=False, allow_nan=False)` → `jsonb`; research §13) |
| `source`, `is_synthetic` | sobre |
| `received_at` | reloj del consumidor (UTC) — distinto del tiempo del evento (FR-018) |
| `kafka_topic`, `kafka_partition`, `kafka_offset` | `MessageRef` |

### `{live}.quarantine`

Mapeo y reglas de saneado: research §4. Resumen: `original` = sobre completo si es almacenable, si no `NULL` + `raw_text` saneado; `original_sha256` = SHA-256 de los bytes recibidos; `event_id`/`source`/`is_synthetic` con la regla de copia; clave de idempotencia `(original_sha256, reason)`.

### `public.date_dim` y `public.country`

`date_dim`: una fila por día UTC del evento, `ON CONFLICT (date_id) DO NOTHING`; `dow = isoweekday()` (1 = lunes … 7 = domingo). `country`: 177 filas del catálogo (research §2).

## 3. Resultado de una versión (`decide_version_outcome`)

Entradas: `stored_updated_ms` (el de `current_event` antes de escribir, o `None`), `incoming_updated_ms`, `version_inserted` (la sentencia sobre `event_version` insertó fila), `content_differs` (solo se consulta si no se insertó). Es una función pura:

| `version_inserted` | `stored_updated_ms` | Resultado | `event_version` | `current_event` |
|---|---|---|---|---|
| sí | `None` | `NEW_EVENT` | +1 | insertar |
| sí | `< incoming` | `NEWER_VERSION` | +1 | sustituir |
| sí | `>= incoming` | `LATE_OLD_VERSION` | +1 | sin cambio |
| no | cualquiera, `content_differs = false` | `REDELIVERY` | sin cambio | sin cambio |
| no | cualquiera, `content_differs = true` | `SAME_UPDATED_CONFLICT` | sin cambio (se conserva la primera) | sin cambio |

Con `stored == incoming` y la versión recién insertada (estado inconsistente: una fila actual sin su versión, imposible si solo escribe este consumidor) se aplica la misma rama que `>`: el estado actual no cambia (una versión con `updated` igual o menor nunca sustituye, constitución §2) y se registra un `WARNING` «estado inconsistente» con el `event_id`. Ese aviso **no lo escribe `decide_version_outcome`** (pura, no registra) sino `consumer/writer.py`, que llama a la función pura `processing.is_inconsistent_state(stored, incoming, version_inserted)` y escribe la línea `inconsistent_state event_id=…` (consumer-runtime §4). La función no lanza excepciones: una excepción aquí bloquearía la partición por un estado de la base y no por el contenido. Esto concuerda con `kafka-message.md` §5.

## 4. Identidades de los contadores (FR-023)

Con `V` = cuarentenas de validación (motivo ≠ `db_constraint_violation`; nuevas + duplicadas) y `D` = `db_constraint_violation` (nuevas + duplicadas):

1. `ms_to_utc_conversions = received − V`
2. `ms_to_utc_conversions = new_events + newer_versions_applied + late_old_versions + redeliveries_ignored + same_updated_conflicts + D`
3. `quarantined[motivo]` (filas nuevas) = `count(*)` SQL por motivo en `live.quarantine`.

Tabla de comprobación con los tres casos de FR-036:

| Caso | received | new_events | newer | late_old | redeliv. | conflicts | quarantined (nuevas) | duplicadas | conversiones |
|---|---|---|---|---|---|---|---|---|---|
| 1. FAQ 12 | 5 | 2 | 1 | 0 | 2 | 0 | 0 | 0 | 5 |
| 2. FAQ 12 + inválido ×2 (lat 145) | 7 | 2 | 1 | 0 | 2 | 0 | 1 (`coordinates_out_of_range`) | 1 | 5 = 7 − (1+1) |
| 3. FAQ 12 + `db_constraint_violation` ×2 (`dmin` = `NaN`) | 7 | 2 | 1 | 0 | 2 | 0 | 1 (`db_constraint_violation`) | 1 | 7 = 7 − 0 = 2+1+0+2+0+(1+1) |

Fixture de la secuencia FAQ 12 (todo sintético: `is_synthetic = true`, `source = replay_demo`, `mode = live`, ids `synthetic-faq12-e1` y `synthetic-faq12-e2`; 2026-11-04 UTC; ms Unix calculados):

| # | Mensaje | `time` (ms) | `updated` (ms) | `mag` | Resultado esperado |
|---|---|---|---|---|---|
| 1 | E1 | 1793786400000 (10:00) | 1793786700000 (10:05) | 4.2 | `NEW_EVENT` |
| 2 | E1 repetido | igual | igual | 4.2 | `REDELIVERY` |
| 3 | E1 | igual | 1793786940000 (10:09) | 4.6 | `NEWER_VERSION` |
| 4 | E1 (10:05) repetido tarde | igual | 1793786700000 | 4.2 | `REDELIVERY` (ya estaba en el historial) |
| 5 | E2 | 1793787060000 (10:11) | 1793787120000 (10:12) | 3.1 | `NEW_EVENT` |

Estado final: `current_event` = {E1: mag 4.6, updated 10:09; E2: mag 3.1}; `event_version` = {(E1, 10:05), (E1, 10:09), (E2, 10:12)} = 3 filas. Caso adicional de la prueba 4 (versión antigua tardía *no vista*): tras el paso 3, un E1 con `updated` 10:07 y `mag` 4.4 ⇒ `LATE_OLD_VERSION`, `current_event` sigue en 4.6/10:09 y el historial pasa a 4 versiones de las cuales 3 son de E1.

## 5. Consecuencias documentadas

- **Cuarentena por bytes**: el mismo JSON inválido con otra serialización (espacios, orden de claves) tiene otro hash y genera otra fila. Aceptado en Clarifications.
- **Nulo y vacío comparten fila** (mismo hash de cero bytes y motivo `invalid_json`).
- **`original` de `event_version`** se guarda re-serializado (research §13); el original bit a bit solo se conserva en cuarentena.
- **Contadores**: se pierden al reiniciar (viven en memoria); la verificación usa una sola sesión y SQL.
- **`replay`**: las funciones y el escritor admiten el esquema `replay` (misma estructura, FR-032); esta feature no lo ejercita más que en la prueba de paridad.

## 6. Transiciones de estado de un evento

```text
(inexistente) --NEW_EVENT--> actual(u1)
actual(u1) --NEWER_VERSION (u2 > u1)--> actual(u2)
actual(u2) --LATE_OLD_VERSION (u1' < u2, no vista)--> actual(u2)   (+ fila en event_version)
actual(u)  --REDELIVERY / SAME_UPDATED_CONFLICT--> actual(u)       (sin cambios)
```

`updated_ms` del estado actual solo crece. Nunca hay dos filas actuales por `event_id` (PK).
