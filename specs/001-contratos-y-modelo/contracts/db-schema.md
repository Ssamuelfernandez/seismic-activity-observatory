# Contrato del esquema de base de datos (consumidor → API)

Fuente de verdad documental del esquema. El DDL ejecutable es [`sql/001_schema.sql`](../../../sql/001_schema.sql) y debe describir las mismas tablas, columnas, claves e índices que este documento (FR-014). Las demás features lo referencian y no lo redefinen (constitución §15).

Los límites de cordura de los `CHECK` están **DECIDIDOS** (aprobados por el alumno el 2026-11-02).

## 1. Esquemas de PostgreSQL

| Esquema | Propósito | Tablas |
|---|---|---|
| `public` | Catálogo compartido por live y replay | `country`, `date_dim` |
| `live` | Datos en vivo e histórico 2025 (`source = usgs_historical`) | `current_event`, `event_version`, `quarantine`, `exclusion` |
| `replay` | Reproducción histórica; **mismas tablas que `live`** | `current_event`, `event_version`, `quarantine`, `exclusion` |
| `ingest` | Estado del productor | `ingest_state`, `ingest_run`, `raw_response` |

**Aislamiento del replay (J3):** el consumidor escribe en `replay` solo mensajes de `earthquakes.replay`, y en `live` solo los de `earthquakes.live` (ver `kafka-message.md` §1). El replay no escribe en `live`, ni a la inversa. `country` y `date_dim` son catálogos compartidos: `date_dim` puede recibir días nuevos desde ambos modos (solo inserciones de referencia) y ningún otro dato cruza entre `live` y `replay`. Las tablas `ingest.*` son compartidas: el replay no usa estado de ingesta propio. La API elige el esquema según `mode` con una lista cerrada (`live`, `replay`), nunca con texto del cliente.

### 1.1 Quién escribe y quién lee

| Esquema.tabla | Escribe | Lee |
|---|---|---|
| `public.country` | Consumidor (carga del catálogo `paises.geojson` al arrancar) | Consumidor y carga histórica (clave foránea al escribir `current_event`); API (unión para `country_name` y `subregion`) |
| `public.date_dim` | Consumidor y carga histórica (insertan el día UTC de cada evento si no existe) | Consumidor y carga histórica (clave foránea) |
| `live.current_event` | Consumidor y carga histórica | API (solo lectura); consumidor y carga histórica (comparar `updated`) |
| `live.event_version` | Consumidor y carga histórica | Consumidor y carga histórica (detectar reenvío o conflicto); consultas de evidencia |
| `live.quarantine` | Consumidor y carga histórica | Consultas de calidad y evidencia |
| `live.exclusion` | Productor | Consultas de calidad y evidencia |
| `replay.current_event` | Consumidor | API (solo lectura); consumidor (comparar `updated`) |
| `replay.event_version` | Consumidor | Consumidor (detectar reenvío o conflicto); consultas de evidencia |
| `replay.quarantine` | Consumidor | Consultas de calidad y evidencia |
| `replay.exclusion` | Productor (el de replay) | Consultas de calidad y evidencia |
| `ingest.ingest_state` | Productor | Productor (Q12) |
| `ingest.ingest_run` | Productor | Productor; API (`last_ingestion`, Q8) |
| `ingest.raw_response` | Productor | Consultas de evidencia y defensa |

- **La API es solo lectura:** no escribe en ninguna tabla. Lee `current_event`, `country` e `ingest_run`.
- La carga histórica solo escribe en `live` (con `source = usgs_historical`); nunca en `replay`.
- Los roles y permisos de base de datos (un rol de solo lectura para la API) se definen en `infra-compose`; `sql/001_schema.sql` no crea roles.

## 2. Reglas transversales

- **Tiempos (E7):** cada instante de USGS se guarda dos veces: `timestamptz` (UTC, con precisión de microsegundo, suficiente para agrupar por hora) y el valor **original en milisegundos Unix** (`*_ms`). Una restricción `CHECK` obliga a que ambos coincidan.
- **Hora UTC:** las ventanas horarias usan `date_trunc('hour', event_time AT TIME ZONE 'UTC')` sobre `event_time` (tiempo del evento, no de procesamiento).
- **Nulos (constitución §5):** `mag`, `depth_km`, `country_id`, `mag_type`, `place`, `status`, `url` y `sig` admiten `NULL`. Nunca se sustituyen por 0.
- **Negativos:** `mag` y `depth_km` aceptan valores negativos (el feed real trae `mag = -0.06` y profundidad `-0.18`). Los `CHECK` de rango (`mag` entre −10 y 15; `depth_km` entre −100 y 1000; `lon`, `lat` en rango geográfico) excluyen `NaN`, infinitos y valores físicamente imposibles; **no** rechazan negativos. Son límites de cordura (**DECIDIDO**); los valores observados (`mag` −0,06…6; profundidad −0,18…377,9) caben con holgura.
- **Validación previa:** el consumidor valida los límites de cordura y los tipos antes de insertar y lleva a cuarentena lo que no los cumpla (`mag_out_of_range`, `depth_out_of_range`, `invalid_field_type`, `value_out_of_range`, `replay_at_missing`; ver `kafka-message.md` §6). Los `CHECK` son la última barrera: se valida antes de insertar y, si aun así la base rechaza el `INSERT`, se aplica el motivo de último recurso `db_constraint_violation` (rollback del mensaje, cuarentena y confirmación del offset, sin bloquear la cola). Un mensaje genera una sola fila de cuarentena, con el primer motivo que falle según el orden de prevalencia de `kafka-message.md` §6.
- **Datos sintéticos (constitución §7):** `is_synthetic boolean NOT NULL DEFAULT false` en `current_event`, `event_version`, `quarantine` y `exclusion`.
- **Origen:** `source` toma los mismos tres valores que el mensaje Kafka (`usgs_feed`, `usgs_historical`, `replay_demo`). Ajuste respecto al roadmap §1 (que proponía `feed | historical | replay`) para tener un solo vocabulario.
- **País:** `country_id` nulo = «Sin país asignado». No se infiere del texto `place`.
- **Identificadores** en inglés; comentarios y documentación en español.

## 3. Tablas

### 3.1 `public.country`

- **Grano:** una fila por entidad del catálogo `data/catalogo/paises.geojson` (177 entidades, `ADM0_A3` único, sin nulos en los campos usados).
- **Clave:** `country_id` (PK).

| Columna | Tipo | Nulo | Origen en el catálogo | Notas |
|---|---|---|---|---|
| `country_id` | text | no | `ADM0_A3` | PK; `CHECK` tres letras mayúsculas |
| `name_es` | text | no | `NAME_ES` | Se devuelve como `country_name` en la API |
| `admin` | text | no | `ADMIN` | Nombre administrativo en inglés |
| `continent` | text | no | `CONTINENT` | |
| `subregion` | text | no | `SUBREGION` | Usada en recuentos por país |

- **Relaciones:** referenciada por `current_event.country_id` (1 país : N eventos).
- **Índices:** solo la PK, que sirve a la unión con `current_event` (nombre y subregión en los recuentos por país, Q2) y a la comprobación de la clave foránea; la tabla tiene 177 filas y no necesita más.
- La carga del catálogo no es parte de esta feature (`consumidor-idempotente`); el archivo no se modifica.

### 3.2 `public.date_dim`

- **Grano:** una fila por día UTC. **Clave:** `date_id` (PK).
- **Columnas:** `date_id date`, `year smallint`, `month smallint` (1–12), `day smallint` (1–31), `dow smallint` (ISO, 1 = lunes … 7 = domingo). Todas no nulas.
- **Relaciones:** referenciada por `current_event.date_id`.
- **Índices:** solo la PK.
- Se rellena en `consumidor-idempotente`, que inserta el día de cada evento si no existe (`ON CONFLICT DO NOTHING`).

### 3.3 `{live|replay}.current_event`

- **Grano:** una fila por evento: su **versión más reciente**. Es la tabla de hechos del modelo.
- **Clave:** `event_id` (PK) → un evento = una fila actual.

| Columna | Tipo | Nulo | Significado |
|---|---|---|---|
| `event_id` | text | no | `id` de USGS |
| `event_time` | timestamptz | no | Instante del terremoto (UTC), convertido de `properties.time` |
| `event_time_ms` | bigint | no | `properties.time` original (ms Unix) |
| `updated_at` | timestamptz | no | Última actualización (UTC) |
| `updated_ms` | bigint | no | `properties.updated` original (ms Unix); decide qué versión gana |
| `mag` | numeric | sí | Magnitud; negativa válida; `NULL` si USGS no la da |
| `mag_type` | text | sí | `properties.magType` (`ml`, `md`, `mb`, `mww`, `mwr`…) |
| `depth_km` | numeric | sí | `coordinates[2]`, en km; negativa válida |
| `lon` | double precision | no | `coordinates[0]` |
| `lat` | double precision | no | `coordinates[1]` |
| `place` | text | sí | `properties.place` (descripción; no se usa para el país) |
| `status` | text | sí | `properties.status` (p. ej. `automatic`) — FR-007b |
| `url` | text | sí | `properties.url` — FR-007b |
| `sig` | integer | sí | `properties.sig` — FR-007b |
| `country_id` | text | sí | FK a `public.country`; `NULL` = sin país |
| `date_id` | date | no | FK a `public.date_dim`; día UTC de `event_time` (`CHECK` de coherencia) |
| `source` | text | no | `usgs_feed` \| `usgs_historical` \| `replay_demo` |
| `is_synthetic` | boolean | no | Marca de dato sintético (por defecto `false`) |
| `ingested_at` | timestamptz | no | Instante en que el productor obtuvo el evento (tiempo de procesamiento) |
| `replay_at` | timestamptz | sí | Instante de reproducción; `NULL` en `live` |

- **Relaciones:** N:1 con `country` (opcional) y con `date_dim`; 1:N con `event_version`.
- **Restricciones:** rangos de cordura, `source` en su lista, coherencia `*_at` ↔ `*_ms` y `date_id` ↔ `event_time`.

### 3.4 `{live|replay}.event_version`

- **Grano:** una fila por **(evento, valor de `updated`) recibido**. Es el historial.
- **Clave:** `(event_id, updated_ms)` (PK). Impide duplicar un reenvío.

| Columna | Tipo | Nulo | Significado |
|---|---|---|---|
| `event_id` | text | no | FK diferida a `current_event.event_id` |
| `updated_ms` | bigint | no | `updated` original (ms Unix) |
| `updated_at` | timestamptz | no | `updated` en UTC |
| `event_time` | timestamptz | no | Instante del evento en esa versión |
| `mag` | numeric | sí | Magnitud de esa versión |
| `depth_km` | numeric | sí | Profundidad de esa versión |
| `original` | jsonb | no | Feature GeoJSON original, íntegro |
| `source` | text | no | Como en `current_event` |
| `is_synthetic` | boolean | no | Marca de dato sintético |
| `received_at` | timestamptz | no | Cuándo lo recibió el consumidor |
| `kafka_topic`, `kafka_partition`, `kafka_offset` | text, integer, bigint | sí | Referencia al mensaje de origen (`NULL` en la carga por lote) |

- **Relaciones:** N:1 con `current_event` (FK `DEFERRABLE INITIALLY DEFERRED`: versión y estado actual se escriben en una sola transacción, en cualquier orden).
- Los cambios entre versiones se observan comparando filas del mismo `event_id` (`mag`, `depth_km`, `original`).

### 3.5 `{live|replay}.quarantine`

- **Grano:** un original inválido rechazado por un motivo.
- **Clave:** `id` (identidad). **Unicidad:** `(original_sha256, reason)` — reprocesar el mismo original por el mismo motivo no duplica la fila (idempotencia, constitución §1). Ajuste respecto al roadmap §1.

| Columna | Tipo | Nulo | Significado |
|---|---|---|---|
| `id` | bigint | no | Identidad |
| `event_id` | text | sí | `id` del evento si se pudo leer |
| `reason` | text | no | Motivo (lista en `kafka-message.md` §6) |
| `original` | jsonb | sí | Valor original si es JSON |
| `raw_text` | text | sí | Valor original si no es JSON válido. `CHECK`: al menos uno de `original` o `raw_text` |
| `original_sha256` | text | no | SHA-256 (hex, 64 caracteres) del original; clave de idempotencia |
| `source` | text | sí | Origen si se pudo leer |
| `kafka_topic`, `kafka_partition`, `kafka_offset` | text, integer, bigint | sí | **Referencia al mensaje original** (constitución §6) |
| `received_at` | timestamptz | no | Cuándo se rechazó |
| `is_synthetic` | boolean | no | Marca de dato sintético |

- **Relaciones:** ninguna FK (el evento puede no existir ni ser identificable).

### 3.6 `{live|replay}.exclusion`

- **Grano:** una fila por (evento, `updated`, tipo de exclusión): un evento descartado de forma controlada antes de publicar (B3, p. ej. `type` distinto de `earthquake`).
- **Clave:** `id` (identidad). **Unicidad:** `(event_id, updated_ms, kind)`, porque el feed repite el mismo evento en cada consulta.

| Columna | Tipo | Nulo | Significado |
|---|---|---|---|
| `id` | bigint | no | Identidad |
| `event_id` | text | no | `id` de USGS |
| `updated_ms` | bigint | no | `updated` original (ms Unix) |
| `kind` | text | no | Tipo de exclusión; valor inicial `non_earthquake_type` |
| `reason` | text | no | Motivo legible |
| `observed_type` | text | sí | Valor observado de `properties.type` |
| `fetched_at` | timestamptz | no | Cuándo se consultó el feed |
| `is_synthetic` | boolean | no | Marca de dato sintético |

- Los eventos sin `id` o sin `updated` **no** se excluyen aquí: se publican y el consumidor los lleva a `quarantine` (la invalidez tiene prioridad).

### 3.7 `ingest.ingest_state`

- **Grano:** una fila por evento publicado. **Clave:** `event_id` (PK).
- **Columnas:** `event_id text`, `last_updated_ms bigint` (último `updated` publicado), `published_at timestamptz`. Todas no nulas.
- Sobrevive a reinicios del productor (B6): el productor publica solo si el `updated` es mayor que `last_updated_ms`, y actualiza la fila **después** del ack de Kafka.

### 3.8 `ingest.ingest_run`

- **Grano:** una fila por consulta al feed, correcta o fallida. **Clave:** `id` (identidad).
- **Columnas:** `run_at timestamptz` (no nulo), `url text` (no nulo), `status integer`, `latency_ms integer` (≥ 0), `event_count integer` (≥ 0), `sha256 text`, `error text`. Los cinco últimos admiten `NULL` (una consulta que agota el tiempo no tiene estado ni hash).
- **Consulta correcta** = `error IS NULL AND status = 200`. `last_ingestion` de la API es el máximo `run_at` de esas filas.

### 3.9 `ingest.raw_response`

- **Grano:** una fila por cuerpo de respuesta distinto del anterior (se inserta solo si el hash difiere). **Clave:** `id` (identidad).
- **Columnas:** `fetched_at timestamptz`, `sha256 text` (hex, 64), `body jsonb`. Todas no nulas.
- La retención por antigüedad se define en la feature `productor-live`.

## 4. Índices y consultas que los justifican

| Id | Consulta concreta | Índice / clave que la sirve |
|---|---|---|
| Q1 | `/api/eventos`: eventos con `event_time >= :start AND event_time < :end`, orden `event_time DESC, event_id DESC`, página siguiente con `(event_time, event_id) < (:t, :id)` | `ix_current_event_time (event_time DESC, event_id DESC)` |
| Q2 | Filtro `country_id = :c` dentro de un intervalo; recuento por país | `ix_current_event_country_time (country_id, event_time DESC)` |
| Q3 | Filtro `mag >= :min_mag`, incluido el `n_2025` de la comparación (M ≥ 4) | `ix_current_event_mag (mag)` — candidato: se mantiene solo si `EXPLAIN ANALYZE` lo justifica (E6, `mediciones-costes`) |
| Q4 | `/api/estadisticas`: `GROUP BY date_trunc('hour', event_time AT TIME ZONE 'UTC')` en un intervalo | Recorrido por rango de `ix_current_event_time` |
| Q5 | Búsqueda de un evento por `event_id` (upsert, medición de búsqueda) | PK de `current_event` |
| Q6 | Historial de un evento y comprobación de reenvío (`ON CONFLICT (event_id, updated_ms)`) | PK de `event_version` |
| Q7 | Motivo de cuarentena de un evento concreto | `ix_quarantine_event_id (event_id) WHERE event_id IS NOT NULL` |
| Q8 | `/api/salud` y `metadata.last_ingestion`: `max(run_at) WHERE error IS NULL AND status = 200` | `ix_ingest_run_last_ok (run_at DESC) WHERE error IS NULL AND status = 200` |
| Q9 | Purga de respuestas originales por antigüedad (`fetched_at < :limite`) | `ix_raw_response_fetched_at (fetched_at)` |
| Q10 | Evitar duplicar la cuarentena de un mismo original y motivo | Restricción única `(original_sha256, reason)` |
| Q11 | Evitar duplicar la exclusión de un mismo evento y `updated` | Restricción única `(event_id, updated_ms, kind)` |
| Q12 | Decidir si el productor publica: `last_updated_ms` del evento | PK de `ingest_state` |
| Q13 | Recuperar el cuerpo original de una consulta a partir de su `sha256` | `ix_raw_response_sha256 (sha256)` |

Ningún índice se afirma como mejora hasta medirlo (FAQ 20). `date_id` no tiene índice propio: ninguna consulta de la API filtra por él.

Todas las agregaciones de `/api/estadisticas` (Q4, recuentos por país, histogramas y comparación con 2025) se calculan desde `current_event` del esquema que corresponde al `mode` (constitución §8), nunca con contadores por mensaje.

## 5. Escritura idempotente y reglas de versiones (C4)

Por mensaje, en **una transacción** (el offset se confirma después del commit):

```sql
-- 1) Historial: un reenvío o un mismo updated no se duplica.
INSERT INTO live.event_version (...) VALUES (...)
ON CONFLICT (event_id, updated_ms) DO NOTHING;

-- 2) Estado actual: solo gana un updated estrictamente mayor.
INSERT INTO live.current_event (...) VALUES (...)
ON CONFLICT (event_id) DO UPDATE SET ...
WHERE EXCLUDED.updated_ms > live.current_event.updated_ms;
```

- `updated` entrante **igual**: no cambia nada. Si el `original` entrante difiere del guardado (`original <> :nuevo`), la segunda versión se ignora, se anota en el log con el `event_id` y se cuenta en los contadores del consumidor (C8).
- `updated` entrante **menor** y no visto: se inserta en `event_version`; `current_event` no cambia.
- `INSERT ... ON CONFLICT (event_id, updated_ms) DO NOTHING` devuelve 0 filas cuando la versión ya existía; así el consumidor distingue «nueva» de «reenvío».

## 6. Equivalencia con el enunciado (E3)

| Enunciado (ENUNCIADO §7 / FAQ 20) | Proyecto | Esquema |
|---|---|---|
| `evento_actual` | `current_event` | `live`, `replay` |
| `evento_version` | `event_version` | `live`, `replay` |
| `pais` | `country` | `public` |
| `fecha` (`fecha_id`) | `date_dim` (`date_id`) | `public` |
| `cuarentena` | `quarantine` | `live`, `replay` |
| Estado de ingesta y calidad (última versión publicada, consultas, rechazos) | `ingest.ingest_state`, `ingest.ingest_run`, `ingest.raw_response`, `exclusion` | `ingest`, `live`, `replay` |
| `event_id`, `updated` | `event_id`, `updated_ms` / `updated_at` | — |

## 7. Cambios respecto al roadmap §1

| Cambio | Motivo |
|---|---|
| `event_time_ms` añadida a `current_event` | Conservar el original en ms, no solo `updated_ms` (constitución §3, E7) |
| `status`, `url`, `sig` añadidas a `current_event` | FR-007b: la API los expone |
| `source` con los valores del mensaje Kafka | Un solo vocabulario |
| `event_version`: `updated_at`, `source`, `is_synthetic`, `kafka_topic` añadidas; `event_time` pasa a no nulo | Etiquetado de sintéticos; referencia completa al mensaje |
| `quarantine`: `original` pasa a nulo, se añaden `raw_text`, `original_sha256`, `source`, `kafka_topic` y la restricción única | Admitir originales que no son JSON; idempotencia |
| `exclusion`: se añaden `updated_ms`, `observed_type`, `is_synthetic`, restricción única; `fetched_at` no nulo | Idempotencia ante el feed repetido |
| Identidad (`GENERATED ALWAYS AS IDENTITY`) en lugar de `bigserial` | Estándar SQL actual de PostgreSQL |
| `ingest_run`: `url` no nulo, `CHECK` ≥ 0 | Integridad |

## 8. Notas para features posteriores

- **(a) Copia de `live` en `replay`:** el esquema `replay` se escribe a mano como copia de `live`. La feature `consumidor-idempotente` debe incluir una prueba que compare las columnas y las restricciones de ambos esquemas.
- **(b) `date_dim` empieza vacía:** el consumidor debe insertar el día del evento (`ON CONFLICT DO NOTHING`) antes de escribir `current_event`, porque `current_event.date_id` tiene clave foránea a `date_dim`.
- **(c) Versión de PostgreSQL:** el DDL se ha probado con PostgreSQL 16 (2026-11-02, ver `docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql`). `infra-compose` debe usar esa misma versión.
