# Research: Consumidor idempotente

Resuelve las incógnitas del plan. Formato: Decisión / Motivo / Alternativas. Los contratos (`kafka-message.md`, `db-schema.md`) se citan, no se copian. Lo verificado en el repositorio se marca como tal; lo que solo se confirma al implementar se marca "Verificar en T…" (los números ya están asignados en `tasks.md`: §6 → T093 y T041; §7 → T032 y T042; §8 → T037).

## 1. Cliente de base de datos y de Kafka

- **Decisión**: se usan los que ya fija `002`: `asyncpg 0.32.0` (`common/db.py`: `create_pool_with_retry`, `COMMAND_TIMEOUT_SECONDS = 5`) y `aiokafka 0.15.0`.
- **Motivo**: constitución §11 (sin dependencias nuevas) y coherencia con el código existente. `asyncpg` entrega el SQLSTATE en `exc.sqlstate` y distingue clases de excepción por clase SQLSTATE.
- **Alternativas**: `psycopg 3` (mejor soporte de `DataError`, pero añade una dependencia y obligaría a reescribir `common/db.py`); `psycopg2` (síncrono, y un `\u0000` en un parámetro lanza `ValueError` antes de llegar a la base: otro mapa de excepciones).
- **Parámetros**: `jsonb` se envía como texto (`$n::jsonb` con `str`), `numeric` como `Decimal(str(valor))` (4.6 → `Decimal('4.6')`, no la expansión binaria), `timestamptz` como `datetime` con zona UTC, `double precision` como `float`.

## 2. Fuente del catálogo de países y `country_id`

- **Decisión**: se carga `data/catalogo/paises.geojson` (verificado: 177 entidades, `ADM0_A3` único, sin nulos en `ADM0_A3`, `NAME_ES`, `ADMIN`, `CONTINENT`, `SUBREGION`; 838 726 bytes) con `common/catalog.py::parse_country_catalog` (pura) y `consumer/catalog_loader.py` (E/S). El archivo se monta en solo lectura en el contenedor del consumidor (no se copia a la imagen: `.dockerignore` excluye `data/` y la imagen no debe cambiar cada vez que cambie un dato).
- **`country_id` queda `NULL`** en todos los eventos (FR-021, constitución §4): ni el `INSERT` ni el `DO UPDATE` de `current_event` lo nombran. Cuando `geografia-pais` lo asigne, lo hará en el mismo upsert.
- **Repetible**: `INSERT ... ON CONFLICT (country_id) DO UPDATE ... WHERE <columnas> IS DISTINCT FROM <EXCLUDED>`; el rol tiene `SELECT, INSERT, UPDATE` sobre `public.country` (verificado en `sql/002_roles.sql`).
- **Alternativas**: precarga por SQL en el arranque de PostgreSQL (`db-schema.md` §3.1 dice que la carga es del consumidor); `DO NOTHING` (no corregiría una fila si el catálogo cambiara, aunque el archivo no se modifica).

## 3. Validación: orden y algoritmo (FR-004)

`decode_value` decodifica primero los bytes con `utf-8` **estricto** y después llama a `json.loads(str)` (no a `json.loads(bytes)`, que autodetectaría UTF-16/32 y aceptaría un BOM). Resultado fijado: un BOM UTF-8 (`EF BB BF`), un texto UTF-16/32 y cualquier byte no UTF-8 dan `invalid_json`.

Una única función pura y total, `validate_message(decoded, topic_mode)`, que devuelve el **primer** motivo del orden de `kafka-message.md` §6 (14 motivos). Algoritmo (cada paso devuelve `Rejection(reason)` o continúa):

| Paso | Motivo | Condición |
|---|---|---|
| 0 | `invalid_json` | `decode_value` falló (tombstone, vacío, UTF-8 inválido, JSON roto, `ValueError` por enteros largos, `RecursionError`). |
| 1 | `invalid_envelope` | el JSON no es un objeto (`null`, `[]`, `123`); falta `source`, `mode`, `ingested_at`, `is_synthetic` o `event`; `source` no es uno de los 3 valores; `mode` no es `live`/`replay`; `ingested_at`, o `replay_at` si no es `null`/ausente, no cumple `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z$` o no es una fecha real; `is_synthetic` no es `bool` exacto; `event` no es objeto. Un `replay_at` ausente en modo `live` se toma como `null`. |
| 2 | `mode_topic_mismatch` | `mode` ≠ `topic_mode(topic)`. |
| 3 | `replay_at_missing` | `mode = replay` y `replay_at` nulo o ausente. |
| 4 | `missing_id` | `event.id` ausente, `null` o `""`. (Una clave Kafka nula no es motivo por sí sola.) |
| 5 | `missing_time` | `event.properties` no es objeto, o `time` ausente o no `int` (un `bool` y un `float` cuentan como no entero). |
| 6 | `missing_updated` | ídem para `updated`. |
| 7 | `invalid_geometry` | `geometry` no es objeto, `type` ≠ `Point`, `coordinates` no es lista o tiene < 2 elementos. |
| 8 | `coordinates_out_of_range` | `lon`/`lat` numéricos (`int`/`float`, no `bool`) no finitos o fuera de [−180, 180] / [−90, 90]. Los no numéricos se dejan al paso 11. |
| 9 | `mag_out_of_range` | `mag` numérico no finito o fuera de [−10, 15]. `null` es válido. |
| 10 | `depth_out_of_range` | `coordinates[2]` numérico no finito o fuera de [−100, 1000]. Ausente o `null` es válido. |
| 11 | `invalid_field_type` | `event.id` no es `str`; `place`, `url`, `status`, `magType` ni `str` ni `null`; `sig` ni `int` (no `bool`) ni `null`; `mag`, profundidad, `lon`, `lat` no numéricos. |
| 12 | `value_out_of_range` | `sig` fuera de `int32`; `time` o `updated` fuera del rango de §6; `len(event.id) > 512`. |
| 13 | `db_constraint_violation` | válido por contrato, pero `event` no es almacenable como `jsonb`/`text` (§5): no finitos, NUL, sustitutos sueltos, profundidad > 64. Se decide **sin tocar la base** y sin reintentos. |

Los pasos 5, 6 y 11 usan comprobación de **tipo exacto** (`type(v) is int`, `type(v) is float`): en Python `bool` es subclase de `int` y se colaría. Las comparaciones de rango con enteros enormes no usan `float()` ni `math.isfinite` sobre `int` (lanzaría `OverflowError`): solo se comprueba finitud en los `float`.

Esta función no lee la base; el tope de longitud y el rango de tiempos están aquí para que una escritura nunca falle por contenido (regla general FR-014).

## 4. Saneado exacto del contenido de la cuarentena (FR-011)

Se decide **antes del `INSERT`**, inspeccionando el contenido (nunca por el SQLSTATE devuelto). `build_quarantine_row` calcula siempre `original_sha256 = sha256(bytes_recibidos).hexdigest()` (minúsculas, 64 caracteres; para tombstone y vacío, el hash de cero bytes `e3b0c442…b855`).

| Campo | Regla |
|---|---|
| `original` (jsonb) | El **valor completo** del mensaje (el sobre) solo si el JSON se deserializó y `is_storable_json` es verdadero. Si no → `NULL`. |
| `raw_text` (text) | `NULL` si `original` no es nulo. Si `original` es `NULL`: `sanitize_raw_text(bytes)`. Garantiza el `CHECK quarantine_has_original`. |
| `sanitize_raw_text(raw)` | (1) `raw.decode("utf-8", errors="backslashreplace")`: cada byte no UTF-8 queda como `\xNN` literal; (2) se sustituye cada `U+0000` por la cadena de 4 caracteres `\x00`. `None` o vacío → `""`. No es reversible (un `\xNN` legítimo del original es indistinguible), por eso el hash de los bytes originales es la referencia fiable. Un `\u0000` escrito como secuencia JSON (6 caracteres ASCII) no es un NUL real y se guarda tal cual. |
| `event_id` | Si `event.id` es `str`, no contiene `U+0000` ni sustitutos sueltos y `len ≤ 512` → se copia. En cualquier otro caso (no es cadena, ausente, con NUL/sustitutos, o más de 512) → `NULL`. No se escapa: un identificador alterado engañaría a `ix_quarantine_event_id`. |
| `source` | Solo si es exactamente `usgs_feed`, `usgs_historical` o `replay_demo`; si no, `NULL` (así el `CHECK quarantine_source_values` nunca falla). |
| `is_synthetic` | Solo si es `bool` exacto; si no, `false`. |
| `reason` | El motivo decidido por `validate_message` (nunca viene del mensaje). |
| `kafka_topic`, `kafka_partition`, `kafka_offset` | De la referencia del registro (`MessageRef`). |
| `received_at` | Reloj inyectado (UTC). |

Si el `INSERT` ya saneado falla, es error de base: reintento sin recursión (FR-011, FR-014). El caso «valor Kafka nulo o vacío» produce `invalid_json`, `raw_text = ""` y el hash de cero bytes; nulo y vacío comparten fila (consecuencia aceptada).

## 5. Regla general «ningún contenido hace fallar una escritura» (FR-014)

Tres comprobaciones previas al `INSERT`, todas en `common/` (puras): **tipo** (§3, pasos 5-11), **almacenabilidad** (`is_storable_json`) y **longitud** (paso 12).

**`is_storable_json(obj)`**: recorrido iterativo con pila explícita (sin recursión: un anidamiento no debe lanzar `RecursionError`). Devuelve `False` si encuentra: un `float` no finito (`NaN`, `±Infinity`, y también `1e400`/`1e999999`, que `json.loads` convierte en `inf`); una cadena (valor **o clave**) con `U+0000`; una cadena con un sustituto suelto (`U+D800`–`U+DFFF`; se detecta intentando `s.encode("utf-8")`); o profundidad > **64** (`MAX_JSON_DEPTH`, salvaguarda propia para que un anidamiento extremo no cause un `54001` persistente en la base). Un USGS real tiene profundidad 4.

**Tabla hostil de US3.11** (cada fila es un test de `validate_message`/`build_quarantine_row`):

| Mensaje | Motivo | `original` | `event_id` en cuarentena |
|---|---|---|---|
| `event.id` numérico (`12345`) o `true` | `invalid_field_type` | el sobre | `NULL` |
| `time` = `true` | `missing_time` | el sobre | el id |
| `sig` = `true` | `invalid_field_type` | el sobre | el id |
| `place` = `42` | `invalid_field_type` | el sobre | el id |
| `mag` = `NaN` (literal `NaN` del JSON) | `mag_out_of_range` | `NULL` (no almacenable), `raw_text` saneado | el id |
| `mag` = `1e400` | `mag_out_of_range` | `NULL`, `raw_text` | el id |
| `dmin` = `NaN` (campo no validado) | `db_constraint_violation` (válido por contrato, no almacenable) | `NULL`, `raw_text` | el id |
| `place` con `\u0000` | `db_constraint_violation` | `NULL`, `raw_text` | el id |
| entero de 4301 dígitos | `invalid_json` | `NULL`, `raw_text` | `NULL` |
| `event.id` de 600 caracteres | `value_out_of_range` | el sobre | `NULL` |
| bytes no UTF-8 | `invalid_json` | `NULL`, `raw_text` con `\xNN` | `NULL` |
| `"\ud800"` en una cadena | `db_constraint_violation` si por lo demás es válido; si no, el motivo que corresponda | `NULL`, `raw_text` (ASCII, contiene `\ud800` literal) | el id |
| `event.id` de exactamente 512 caracteres, contenido normal | válido, se guarda | — | — |
| JSON anidado a 1500 niveles | `decode_value` lo decodifica sin error (en Python 3.12 no salta `RecursionError` a 1500 niveles). Rige entonces la validación: si la raíz es una lista, `invalid_envelope`; si el anidamiento está dentro de `event`, `db_constraint_violation` (profundidad > 64, como la fila de 100 niveles). | `NULL`, `raw_text` en el segundo caso | `NULL` en el primero, el id en el segundo |
| JSON anidado a 200000 niveles (`EXTREME_NESTING_DEPTH` en `tests/common/test_decode.py`) | `invalid_json` (`RecursionError` capturado en `decode_value`) | `NULL`, `raw_text` | `NULL` |
| JSON anidado a 100 niveles dentro de `event` | `db_constraint_violation` (profundidad > 64) | `NULL`, `raw_text` | el id |

**`1e400`**: Python lo lee como `inf`; PostgreSQL `numeric` lo aceptaría. Se aplica «no finito tras deserializar = no almacenable» (criterio de la spec, FR-014 punto 2): el consumidor trabaja con `float` y no puede asegurar que lo guardado coincida con lo recibido. Se prefiere el rigor a la excepción: si el campo es `mag`, `lon`, `lat` o profundidad, rige su motivo; en otro campo, `db_constraint_violation`.

**Enteros > 4300 dígitos**: `json.loads` lanza `ValueError` (límite de `sys.set_int_max_str_digits`, 4300 por defecto en Python 3.12) y se trata como `invalid_json`. No se modifica el límite global. Un entero de ≤ 4300 dígitos en un campo no validado es almacenable (`jsonb` admite hasta 131 072 dígitos).

**Totalidad**: un test de fuzz determinista (semilla fija) muta un mensaje válido (cambia tipos, inserta `NaN`, NUL, enteros enormes, claves repetidas, listas por objetos) y comprueba que `validate_message` y `build_quarantine_row` nunca lanzan.

## 6. Rango admitido de `time` / `updated` (`value_out_of_range`)

- **Decisión**: `1000-01-01T00:00:00Z ≤ instante < 3000-01-01T00:00:00Z`, es decir, `MIN_EPOCH_MS = -30610224000000` y `MAX_EPOCH_MS = 32503680000000` (exclusivo). Constantes con nombre en `common/transform.py`.
- **Motivo**: (a) el `CHECK` del DDL `event_time = timestamptz 'epoch' + event_time_ms * interval '1 millisecond'` multiplica un `interval` por un `bigint` convertido a `double`; el producto en microsegundos es exacto mientras `ms × 125` quepa en 53 bits (ms < 7,2·10¹³, año ≈ 4250), y más allá puede perder microsegundos y hacer fallar la restricción con un error `23514` dependiente del contenido; (b) `date_dim.year` es `smallint` (≤ 32 767) y `datetime` de Python llega a 9999; (c) ningún sismo real de USGS queda fuera de 1000-2999. Es un subconjunto del rango de `timestamptz`, como pide FR-014.
- **Verificación**: se comprueba **antes de construir `transform` y `validation`**, solo con SQL, en la tarea T093 (extremos 1000-01-01T00:00:00.000Z y 2999-12-31T23:59:59.999Z contra la misma expresión del `CHECK`); la prueba de integración de T041 lo repite con filas reales. Si el `CHECK` no acepta los extremos, **se detiene el trabajo y se escala al alumno** (no se reduce el rango por cuenta propia): habría que rehacer T021-T025, este §6, `consumer-runtime.md` §1 y `plan.md` §13.2.
- **Conversión**: `ms_to_utc(ms) = datetime(1970,1,1,tzinfo=UTC) + timedelta(milliseconds=ms)`; aritmética entera, sin `float`.
- **Alternativas**: usar el rango completo de `timestamptz` (arriesga el `CHECK`); 1900-2100 (más estrecho de lo necesario para un catálogo con eventos históricos).

## 7. Mapa de excepciones del cliente y detección de clase 22/23

- **Decisión**: tabla de [plan.md](plan.md) §6. `is_content_error(exc)` devuelve `True` si `isinstance(exc, (asyncpg.exceptions.IntegrityConstraintViolationError, asyncpg.exceptions.DataError, UnicodeError))` **o** `str(getattr(exc, "sqlstate", "") or "")[:2] in {"22", "23"}`.
- **Verificado en el repositorio** (`.venv`, `asyncpg 0.32.0`): `asyncpg.exceptions.DataError` es la clase de errores SQLSTATE 22 (subclase de `PostgresError`, `sqlstate = '22000'`) y es la que levanta el propio `asyncpg` por «invalid input for query argument» (`prepared_stmt.pyx`); `_base.DataError(InterfaceError, ValueError)` queda tapada en el espacio de nombres de `asyncpg.exceptions`. `CharacterNotInRepertoireError`, `NumericValueOutOfRangeError` y `UntranslatableCharacterError` heredan de ella.
- **Por qué es seguro con la validación previa**: un NUL en un `text` da 22021 y en `jsonb`, 22P05; un entero fuera de `int32` en un parámetro `integer`, el `DataError` de cliente. Como esas condiciones se detectan antes (§3, §5), llegar a este mapa es un defecto de la validación: se registra una línea `ERROR` «defecto de validación previa» además de ir a cuarentena, para que se corrija la validación y no se normalice el atajo.
- **Momentos**: `INSERT` y `COMMIT`. `async with conn.transaction()` lanza en la salida si el `COMMIT` falla (p. ej. la FK diferida 23503 o un disparador de restricción diferido); la excepción es la misma familia y se trata igual. Tras el error la conexión se devuelve limpia al pool.
- **Transitorios**: cualquier otra `PostgresError`, `InterfaceError` (conexión cerrada), `OSError`, `asyncio.TimeoutError`. `asyncpg` abre conexiones nuevas al pedirlas al pool tras una caída.
- **Excepciones que no son de base** (`TypeError`, `KeyError`…): se propagan y el proceso termina con traza; no se silencian.
- **Verificar en T032 (unitaria) y T042 (integración)**: prueba unitaria con excepciones reales (`asyncpg.exceptions.CheckViolationError("x")`, `CharacterNotInRepertoireError("x")`, `CannotConnectNowError("x")`) y prueba de integración que fuerza un `NUL` en `text` saltándose la validación previa.

## 8. Cuarentena con un rol sin `SELECT`

- **Decisión**: `INSERT INTO {esquema}.quarantine (...) VALUES (...) ON CONFLICT DO NOTHING` **sin destino de conflicto** (única forma admitida; `ON CONSTRAINT` se descarta porque PostgreSQL también podría exigir `SELECT` sobre las columnas de la restricción), sin `RETURNING` ni `DO UPDATE`. Con destino `(original_sha256, reason)` PostgreSQL exige `SELECT` sobre esas columnas y el rol daría `42501`, error que se reintentaría sin fin. La tabla tiene una sola restricción única, así que la forma sin destino cubre el mismo caso. El `PRIMARY KEY` (`id`, secuencia) no puede chocar. Se lee la etiqueta de estado de `asyncpg` (`conn.execute` devuelve `"INSERT 0 1"` o `"INSERT 0 0"`) para distinguir fila nueva de duplicado y alimentar `quarantined` / `quarantine_duplicates`.
- **Motivo**: `sql/002_roles.sql` da al consumidor solo `INSERT` sobre `quarantine` (y `USAGE` en la secuencia de `id`). `RETURNING` y `DO UPDATE` exigen `SELECT`; `DO NOTHING` no.
- **Verificar en T037**: `test_roles.py` ejecuta exactamente esa sentencia (sin destino) con el rol real `observatory_consumer` (inserción `INSERT 0 1` y duplicado `INSERT 0 0`) y comprueba que `SELECT` está denegado. Además ejecuta la variante con destino `(original_sha256, reason)` para documentar su resultado. En ningún caso se concede `SELECT` para resolverlo (FR-027): la respuesta es la forma sin destino. Si ni esa funcionara, **se escala**.
- **Alternativas**: `INSERT ... WHERE NOT EXISTS (SELECT ...)` (necesita `SELECT`).

## 9. Offsets, bucle y reintentos

- **Un mensaje por vuelta, un commit de offset por mensaje**: `getmany(timeout_ms=1000, max_records=1)` y `commit({tp: offset + 1})`. Para el volumen de USGS el coste (un viaje al coordinador por mensaje) es irrelevante, y evita razonar sobre commits parciales de lotes.
- **`max_poll_interval_ms = 86_400_000`** (24 h): `aiokafka` expulsa del grupo al consumidor que tarda más de 300 000 ms entre `getmany`, y un reintento sin límite puede superarlo; la expulsión generaría una redistribución y un `CommitFailedError`.
- **`CommitFailedError`** (cambio de generación): reintentar es inútil; se registra y se continúa. Cualquier otro `KafkaError`/`OSError` en el commit se reintenta con la espera de `common/retry.py::next_delay`.
- **Valores**: espera 1, 2, 4, 8, 16, 30 s…, tope 30 s (`RETRY_MAX_SECONDS`); una línea `WARNING` por intento (≤ 2 por minuto en régimen), sin traceback. Sin límite de intentos.
- **Parada limpia**: `SIGTERM`/`SIGINT` activan un `asyncio.Event`; la espera de reintento y el bucle lo respetan, no se confirma el offset en curso, se imprime el resumen de contadores y se cierran consumidor y pool.
- **Arranque**: sin grupo previo, `auto_offset_reset="earliest"` (ya está en `start_consumer`); la idempotencia hace seguro releer.

## 10. Contadores: unidad y justificación

- **Una vez por mensaje, tras el commit del offset**; los reintentos no cuentan. Solo se acumulan en memoria (la spec descarta una tabla; las preguntas abiertas 3 y 4 se asumen con su recomendación).
- **Por qué la conversión ms → UTC cuenta en `db_constraint_violation` y no en las cuarentenas de validación**: la conversión es la transformación del paso 3 del flujo y ocurre **antes** de la escritura; un mensaje que la base rechaza ya la había hecho; uno rechazado por validación no llegó a transformarse. De ahí las identidades (plan §7): `conversiones = recibidos − cuarentenas de validación` y `conversiones = nuevos + más recientes + antiguas + reenvíos + conflictos + db_constraint_violation`.
- **`db_constraint_violation` pre-base** (válido por contrato pero no almacenable): se decide después de `build_event_rows`, así que sí cuenta conversión, igual que el rechazo de la base. Coherente con FR-036 caso 3 (7 recibidos → 7 conversiones).
- **Valores nulos conservados**: una cuenta por campo y por mensaje transformado cuyo valor es `null` (`mag`, `depth_km`, `place`, `status`, `url`, `sig`, `mag_type`); misma población que las conversiones.
- **Duplicados de cuarentena**: contador aparte por motivo; «cuarentenas por motivo» coincide con el recuento SQL de filas.

## 11. Hook de prueba para la prueba 8

- **Decisión**: parámetro `after_db_commit` de `process_record`, invocado entre el commit de PostgreSQL y el commit del offset. Dos implementaciones: un doble de pytest que lanza `SimulatedCrash(BaseException)`, y `fault_hook.crash_once_at_offset(offset, marker_path)` que termina el proceso con `os._exit(137)` una sola vez (archivo marcador en `/tmp`), activada solo si `CONSUMER_FAULT_CRASH_AT_OFFSET` no está vacía y **solo para mensajes `is_synthetic=true`** (salvaguarda: el marcador de `/tmp` se pierde si se recrea el contenedor, y así un dato real nunca provoca la salida).
- **Motivo**: el punto exacto «después del commit de PG y antes del commit del offset» no se puede acertar con `docker kill` de forma fiable. Con el marcador, el reinicio de Compose (`restart: unless-stopped`) no vuelve a morir en el mismo offset.
- **Alternativas**: solo hook en proceso (sin evidencia con contenedor); parar PostgreSQL justo antes del commit (no determinista).

## 12. Infraestructura de pruebas

- **Problema**: la base no se publica (constitución §10) y la imagen de producción excluye `tests/`, `sql/` y las dependencias de desarrollo (`.dockerignore`, `uv sync --no-dev`).
- **Decisión**: servicio `tests` en el perfil `test` de Compose (no se levanta con `up`), construido con una etapa `test` del `Dockerfile` que instala el grupo `dev` con `--frozen`, y con `tests/`, `sql/` y `data/catalogo/` montados en solo lectura. Se ejecuta con `docker compose --profile test run --rm tests pytest -m integration`.
- **Aislamiento**: base temporal por sesión de pytest (fixture), no la base de la aplicación. Los `GRANT` de `sql/002_roles.sql` se reaplican leyendo el archivo (el script usa `\set` y `\gexec` de `psql`, que `asyncpg` no ejecuta).
- **Sin `pytest-asyncio`**: las pruebas son síncronas y llaman a `asyncio.run(...)`; evita una dependencia nueva (§11).
- **Alternativas**: `testcontainers` (dependencia nueva y requiere el socket de Docker); publicar el puerto 5432 en `127.0.0.1` solo para pruebas (contraria al espíritu de §10).

## 13. Serialización del `original`

- **Decisión**: `json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":"))` del objeto deserializado, enviado como `jsonb`. `allow_nan=False` es una segunda barrera (lanzaría `ValueError` si un no finito pasara, lo que sería un defecto).
- **Efecto**: valores íntegros; formato numérico normalizado (`1E5` → `100000.0`), orden de claves y espacios los normaliza `jsonb`. La cuarentena es la única que conserva los bytes exactos, vía hash y `raw_text`.
- **Límites de precisión**: un `float` pierde precisión por encima de ~17 dígitos significativos y `1e-400` pasa a `0.0` sin aviso; se acepta como decisión provisional (plan §13.7). Alternativa: `parse_float=Decimal`.
- **Alternativa**: conservar la subcadena exacta del `event` en los bytes recibidos (requiere un analizador propio; desproporcionado).

## 14. Recursos de Compose para el catálogo y para el grupo

- **Grupo**: `KAFKA_GROUP_ID=consumer-live` (el actual `consumer-minimal` describe el consumidor mínimo). Una base y un grupo «limpios» son los de un volumen recién creado (`down -v`); el grupo del consumidor mínimo nunca confirmó offsets, así que no hay estado que migrar.
- **Variables nuevas** (todas en [contracts/consumer-runtime.md](contracts/consumer-runtime.md)): `COUNTRY_CATALOG_PATH` (constante de diseño en `compose.yaml`) y `CONSUMER_FAULT_CRASH_AT_OFFSET` (opcional, vacía).
