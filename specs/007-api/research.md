# Investigación y decisiones: API de consulta

Cada decisión: qué se elige, por qué y qué se descartó. No quedan «NEEDS CLARIFICATION»: las dudas de la spec están resueltas en sus Clarifications y en «Preguntas para el alumno» (provisionales).

## D1. Validación de parámetros con código propio, no con el tipado de FastAPI

- **Decisión**: los routers no declaran parámetros tipados; reciben `request.query_params`, y `api/params.py` (puro) devuelve `QueryFilters` y `PageRequest` o lanza `ApiError(400, "invalid_parameter" | "invalid_cursor", mensaje en español)`.
- **Motivo**: FastAPI responde 422 con `{"detail": …}` ante un tipo erróneo; el contrato exige 400 con el cuerpo común (FR-013). Además un parámetro repetido (`?min_mag=1&min_mag=2`) solo se ve en la lista cruda, y el mensaje debe nombrar el parámetro.
- **Alternativas**: tipado de FastAPI + manejador de `RequestValidationError` que traduce a 400 (los mensajes salen del framework y no distinguen repetidos); dependencia con `Query()` y validadores (más código y el mismo problema con repetidos).

## D2. Una transacción de lectura por petición

- **Decisión**: `api/db_access.py` abre una conexión del pool con `acquire(timeout=API_DB_TIMEOUT_SECONDS)` y una transacción `REPEATABLE READ` de solo lectura; dentro se ejecutan todas las consultas de la petición.
- **Motivo**: sin ella, el consumidor puede insertar un evento entre el `count` y la página (o entre los bloques de estadísticas) y `total` ≠ suma de bloques (FR-010, SC-003). Con una instantánea la coherencia es una propiedad, no una casualidad de la prueba.
- **Alternativas**: consultas sueltas sin transacción (coherencia solo probable); una única consulta gigante con CTE (ilegible, difícil de probar por bloques).

## D3. «Ahora» único y fechas exactas

- **Decisión**: el router toma `now_ms` (entero) al entrar y lo pasa a `params.py` (rango por defecto), a las respuestas (`generated`) y a la comparación (`recent_period`). Las fechas del cliente se convierten a ms enteros; para consultar se construyen `datetime` UTC con `epoch + timedelta(milliseconds=ms)` (exacto).
- **Motivo**: `generated`, `period.end` y `recent_period.end` coherentes en una respuesta; sin errores de redondeo de coma flotante en los límites inclusivo/exclusivo ni en el desempate del cursor.
- **Alternativas**: `datetime.fromtimestamp(ms/1000)` (flotante: pierde precisión en el borde); comparar por `event_time_ms` (exacto pero no usa `ix_current_event_time`).

## D4. Interpretación de fechas ISO 8601

- **Decisión**: `datetime.fromisoformat` de Python 3.12 (admite `Z`, desplazamientos y solo fecha). Sin zona = UTC; solo fecha = 00:00 UTC (`api.md` §3.1). `ValueError` y `OverflowError` (años extremos al pasar a UTC) → `invalid_parameter`. `start >= end` → `invalid_parameter`.
- **Motivo**: sin dependencias nuevas. **Alternativa**: `python-dateutil` (dependencia extra sin necesidad).

## D5. `min_mag` y `limit`

- **Decisión**: `min_mag` = `float()` + `math.isfinite`; `nan`, `inf`, vacío o texto → 400. Los negativos valen. `limit` = entero decimal entre 1 y `API_MAX_EVENTS`; `0`, negativos, decimales, texto o mayor → 400. Un parámetro conocido repetido → 400.
- **Motivo**: constitución §5 (nunca NaN/Infinity); Clarifications de la spec. **Alternativa**: truncar un `limit` excesivo al máximo (el contrato dice error 400).

## D6. País

- **Decisión**: `country_id.upper()`; válido si `[A-Z]{3}` ASCII o `NONE` → se guarda `"none"`. `none` filtra `country_id IS NULL`; un código válido inexistente devuelve vacío. País del evento con `LEFT JOIN public.country` (nombre `name_es`, `subregion`).
- **Motivo**: `api.md` §3.1. **Alternativa**: validar contra el catálogo y dar 400 si no existe (el contrato dice que no es error).

## D7. Esquema `live`/`replay` por lista cerrada

- **Decisión**: `SCHEMAS = {"live": "live", "replay": "replay"}`; `sql_filters.py` obtiene el nombre desde ese diccionario con el `mode` ya validado y lo inserta en la plantilla; los demás valores van como `$n`. El rol ya tiene `SELECT` en ambas tablas (`002_roles.sql`).
- **Motivo**: un identificador no puede ser un parámetro SQL; la lista cerrada evita la inyección (FR-014, `db-schema.md` §1). **Alternativa**: dos funciones duplicadas (una por esquema): duplica SQL.

## D8. Paginación por clave

- **Decisión**: orden `event_time DESC, event_id DESC`; la página siguiente añade `(e.event_time, e.event_id) < ($t, $id)`; se pide `limit + 1` filas para saber si hay más; `next_cursor` solo si hay más; `truncated = count < total`. Cursor = base64url de `{"t": <ms>, "id": "<id>"}` (sin relleno); cualquier fallo al decodificar (base64, JSON, tipos) → `invalid_cursor`.
- **Motivo**: contrato `api.md` §3.3 e índice `ix_current_event_time` (Q1). Una revisión conserva `event_time` e `id`, así que no cambia de posición. **Alternativa**: `OFFSET` (repite o pierde eventos si llegan datos; lento).
- **Nota**: la comparación de `event_id` usa la ordenación de la base, la misma del índice; es coherente consigo misma.

## D9. Recuentos con una sola consulta

- **Decisión**: una consulta sobre el rango y el país **sin** `min_mag` devuelve `total` (`count(*) FILTER (WHERE mag cumple min_mag)`) y `null_count` (`count(*) FILTER (WHERE mag IS NULL)`). `null_mag_excluded` = `null_count` si hay `min_mag`, si no 0. Estadísticas reutiliza la misma función, así `histograms.magnitude.no_value` coincide por construcción con `null_mag_excluded`.
- **Alternativa**: dos consultas independientes (riesgo de divergencia).

## D10. Estadísticas

- **Por hora**: SQL agrupa por `floor(event_time_ms / 3 600 000)` y devuelve solo las horas con eventos; `stats_builder` rellena con ceros desde la hora que contiene `start` hasta la que contiene `end − 1 ms`.
- **Por país**: `GROUP BY country_id, name_es, subregion ORDER BY count DESC, country_id ASC NULLS LAST`; el elemento con `country_id` nulo es uno más y `no_value` repite su recuento sin sumarlo dos veces.
- **Histogramas**: `width_bucket(valor, ARRAY[umbrales])` devuelve 0 para «menor que el primero» y N para «mayor o igual que el último», que coincide con los tramos de `api.md` §5.1; el bucket `NULL` (profundidad sin valor) es el `no_value` de `depth`. Magnitud: los nulos se contabilizan con la consulta de D9, no con el histograma. Los tramos y sus límites son constantes con nombre en `stats_builder.py`.
- **Comparación** (solo `live`): una consulta con `count(*) FILTER (…)` para `n_recent` y para `n_2025`, con `mag >= max(min_mag, 4.0)` y el mismo filtro de país, y `WHERE (rango reciente OR rango 2025)` para usar el índice. `daily_mean_2025 = n_2025 / 365`, `diff_abs = n_recent − daily_mean_2025`, `variation_pct = round(diff_abs / daily_mean_2025 × 100, 2)` o `null` si la media es 0; `recent_incomplete: true`. `recent_period = [now − 24 h, now]`.
- **Alternativa descartada**: calcular tramos y horas en Python sobre las filas (violaría §8 y el «no una muestra»).

## D11. Errores

- **Decisión**: `ApiError(status, code, message)` + manejadores globales: `ApiError` → su cuerpo; `StarletteHTTPException` 404 → `not_found`, 405 → `method_not_allowed` (conserva `Allow`); `RequestValidationError` → `invalid_parameter` (red de seguridad, no debería ocurrir); `Exception` → `internal_error` con mensaje fijo y registro de la traza en el log, nunca en la respuesta; errores de base (`RETRIABLE_DB_ERRORS`) → `database_unavailable` en `db_access.py`.
- **Motivo**: FR-013, `api.md` §6, pendiente heredado de `002`. El 404 de Starlette para rutas inexistentes y el 405 llegan al manejador de `StarletteHTTPException`.
- **Nota**: en pruebas, el cliente debe tolerar que Starlette relance la excepción del manejador 500 (`raise_app_exceptions=False` en el transporte).

## D12. Tiempo del 503

- **Decisión**: `acquire(timeout=API_DB_TIMEOUT_SECONDS)` (defecto 5; permitido 1–9) más el `command_timeout=5` ya existente del pool. Con PostgreSQL parado la conexión se rechaza de inmediato o vence el plazo; ambos casos son `database_unavailable` en < 10 s. La recuperación es automática: el pool abre conexiones nuevas cuando la base vuelve; no hace falta reiniciar la API.
- **Límite**: si PostgreSQL está parado al arrancar, `create_pool_with_retry` reintenta y la API no atiende (comportamiento de `002`).

## D13. Pruebas de la API

- **Decisión**: `httpx.AsyncClient(transport=ASGITransport(app))` dentro de `asyncio.run`, con `app.state.pool` creado a mano (el transporte no ejecuta el `lifespan`) con el rol real `observatory_api` sobre la base temporal. La base temporal se llena como administrador (INSERT directos de eventos sintéticos).
- **Motivo**: patrón de `tests/integration/` (servicio `tests`, sin `pytest-asyncio`). **Alternativa**: `TestClient` síncrono de Starlette (corre la app en otro hilo/bucle y complica el uso del pool asyncpg).
- **Coste**: `httpx` (grupo dev) y `DB_API_PASSWORD` en el servicio `tests`.

## D14. Qué no se hace

CORS (P1), autenticación, caché, limitación de tasa, índices nuevos, cambios de DDL o roles, pruebas de rendimiento, fuzz, endurecimiento de casos raros (se documentan como límite conocido).
