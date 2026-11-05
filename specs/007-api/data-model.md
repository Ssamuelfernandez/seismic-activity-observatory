# Modelo de datos: API de consulta

La feature **no crea tablas, índices ni roles**. Solo lee. La forma de las respuestas JSON está en `specs/001-contratos-y-modelo/contracts/api.md`; las tablas, en `db-schema.md` y `sql/001_schema.sql`. Aquí se fijan las estructuras internas y la correspondencia columna -> campo.

## 1. Tablas que se leen (rol `observatory_api`, solo `SELECT`)

| Tabla | Para qué | Consulta (`db-schema.md` §4) |
|---|---|---|
| `{live\|replay}.current_event` | Eventos, recuentos y estadísticas | Q1, Q2, Q3, Q4 |
| `public.country` | `country_name` (`name_es`) y `subregion` | LEFT JOIN por `country_id` |
| `ingest.ingest_run` | `last_ingestion` (siempre del modo en vivo) | Q8 |

## 2. Correspondencia columna -> JSON

| `current_event` / `country` | Campo de la respuesta |
|---|---|
| `event_id` | `Feature.id` |
| `lon`, `lat`, `depth_km` | `geometry.coordinates = [lon, lat, depth_km]` (`depth_km` nulo -> `null`) |
| `mag`, `mag_type` | `properties.mag`, `properties.magType` (nulos -> `null`) |
| `place`, `status`, `url`, `sig` | `properties.place`, `status`, `url`, `sig` (nulos -> `null`) |
| `event_time_ms`, `updated_ms` | `properties.time`, `properties.updated` |
| `country_id`, `country.name_es` | `properties.country_id`, `properties.country_name` (sin país -> ambos `null`) |
| `is_synthetic` | `properties.is_synthetic` |

`numeric` de PostgreSQL llega como `Decimal`: se convierte a `float` finito al serializar; un valor no finito (no debería existir por el CHECK) se serializa como `null`.

## 3. Estructuras internas (en memoria)

| Estructura | Campos | Reglas |
|---|---|---|
| `QueryFilters` | `start_ms`, `end_ms`, `min_mag: float \| None`, `country_id: str \| None` (`"ESP"`, `"none"` o `None`), `mode: "live" \| "replay"` | `start_ms < end_ms`; `country_id` normalizado; rango por defecto según `api.md` §3.1 con `now_ms` |
| `PageRequest` | `limit: int`, `cursor: CursorPosition \| None` | `1 <= limit <= API_MAX_EVENTS`; solo en `/api/eventos` |
| `CursorPosition` | `time_ms: int`, `event_id: str` | Se codifica como base64url de `{"t","id"}`; mal formado -> `invalid_cursor` |
| `ApiSettings` | `max_events: int` (defecto 5000, >= 1), `db_timeout_seconds: int` (defecto 5, 1–9) | Variables `API_MAX_EVENTS`, `API_DB_TIMEOUT_SECONDS` |
| `ApiError` | `status`, `code`, `message` | `code` de `api.md` §6; mensaje en español sin SQL ni credenciales |

Parámetros de consulta: `start`, `end`, `min_mag`, `country_id`, `mode`, `limit`, `cursor` (`api.md` §3.1). Los desconocidos se ignoran; los conocidos repetidos son `invalid_parameter`.

## 4. Constantes con nombre (no se repiten en el código)

| Constante | Valor | Origen |
|---|---|---|
| `MAGNITUDE_THRESHOLDS` | `[1, 2, 3, 4, 5, 6, 7]` (8 tramos) | `api.md` §5.1 |
| `DEPTH_THRESHOLDS` | `[10, 35, 70, 300]` (5 tramos) | `api.md` §5.1 |
| `COMPARISON_MIN_MAG` | `4.0` | `api.md` §5.1 |
| `REFERENCE_PERIOD` | `[2025-01-01T00:00Z, 2026-01-01T00:00Z)` en ms (365 días) | `api.md` §5.1 |
| `RECENT_WINDOW_HOURS` | `24` | `api.md` §3.1 y §5.1 |
| `MS_PER_HOUR` | `3 600 000` | — |

## 5. Identidades que las pruebas comprueban (mismos filtros, misma transacción)

- `estadisticas.total == eventos.metadata.total`.
- `sum(by_hour.buckets[].count) == total`.
- `sum(by_country.items[].count) == total` (el elemento sin país cuenta una vez).
- `sum(histograms.depth.bins[].count) + depth.no_value == total`.
- `sum(histograms.magnitude.bins[].count) == total` **si hay `min_mag`** (los nulos ya no están en `total`); `== total − magnitude.no_value` **si no hay** `min_mag`.
- `histograms.magnitude.no_value == eventos.metadata.null_mag_excluded` cuando se envía `min_mag`.
- `comparison.n_2025` coincide con una cuenta SQL independiente de 2025 con `mag >= min_mag_applied` y el mismo país.

## 6. Estados y transiciones

No hay estado propio: cada petición es independiente (única «memoria»: el cursor, que lleva la posición). El único efecto en el sistema es la lectura.
