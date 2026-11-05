# Tasks: API de consulta

**Input**: `specs/007-api/` (spec.md, plan.md, research.md, data-model.md, quickstart.md).

**Rama**: `007-api`. **Estado**: 0/25 tareas hechas. No se hace commit ni merge: al terminar T025 se detiene el trabajo y se espera la revisión del alumno.

**Cubre**: F1–F8, F10, F11 y F12 parcial. F9 (CORS) queda en la feature `despliegue` (P1, provisional).

**Alcance**: 25 tareas en 5 bloques. Fuera de alcance: CORS, panel, replay (productor, consumidor, datos), túnel, despliegue, autenticación, caché, fuzz, auditorías y endurecimiento de casos raros. `api.md`, `db-schema.md`, `kafka-message.md`, `sql/001_schema.sql`, `sql/002_roles.sql`, `specs/002-infra-compose/contracts/config.md` y `docs/enunciado/` no se tocan (se comprueba en T025). Lo raro es un límite conocido en una línea (plan §8), no una tarea.

## Formato y criterios comunes

Cada tarea: `- [ ] T### [P?] [US?] Descripción con ruta`, con **Cubre** (IDs) y **Criterio** (comando y resultado). `[P]` = paralelizable con otras `[P]` del bloque. Etiquetas: US1 eventos, US2 paginación, US3 estadísticas, US4 salud y fallos, US5 errores y replay.

Toda tarea de código cumple además: **CC-DOC** (identificadores en inglés salvo rutas y campos del contrato; docstrings y comentarios en español con la plantilla de `03-procedimiento-ejecucion.md` §7.4; type hints; sin `print`; sin `except Exception: pass`); **CC-14** (una responsabilidad por función, ≈ 30 líneas, archivo ≤ 250, lo puro no importa `asyncpg` ni `fastapi`, sin números ni textos mágicos, todo valor del cliente como parámetro SQL `$n`, esquema solo por la lista cerrada); **CC-MAP** (la tarea que crea, mueve o elimina archivos de código ajusta la fila de `CODEMAP.md`, o lo deja a T024 y lo anota en la bitácora).

La prueba va antes que su implementación (TDD): «falla antes» significa que al escribirla falla por falta de implementación o por import. Las pruebas usan eventos `synthetic-…` con `is_synthetic=true`; los datos reales solo aparecen en el bloque 5.

**Imagen `tests` al día**: tras cambiar `api/`, `common/` o `pyproject.toml`, `docker compose --profile test build tests` antes de `pytest -m integration`.

Comandos de referencia: unitarias `uv run pytest -m "not integration" -q`; integración `docker compose up -d postgres`, `docker compose --profile test build tests`, `docker compose --profile test run --rm tests pytest -m integration -q`.

## Bloque 1 — Base: configuración, parámetros, cursor, errores y banco de pruebas

**Objetivo**: todo lo puro y el cableado mínimo, sin SQL de eventos. **Dependencias**: ninguna. Orden real: T001, T004 (define `ApiError`), y luego T002, T003 y T005.

- [x] T001 [US4] Configuración y dependencia de pruebas: `common/api_config.py` (`ApiSettings`, `load_api_settings`: `API_MAX_EVENTS` defecto 5000 y mín. 1; `API_DB_TIMEOUT_SECONDS` defecto 5, de 1 a 9), `tests/common/test_api_config.py`; `httpx` fijado en el grupo `dev` de `pyproject.toml` y `uv lock`; variables en el servicio `api` y `DB_API_PASSWORD` en el servicio `tests` de `compose.yaml`; ambas variables en `.env.example`.
  - Cubre: F5, FR-019, constitución §10 y §11.
  - Criterio: la prueba pasa (defectos, valor no entero, fuera de rango -> `ConfigError`); `python scripts/check_env_example.py` sale con 0; `docker compose config` resuelve sin error.

- [x] T002 [P] [US1] `api/timeutil.py` y `api/params.py` con `tests/api/test_params.py`: `parse_filters(raw_params, now_ms)` y `parse_page(raw_params, max_events)` devuelven `QueryFilters`/`PageRequest` (data-model §3). Casos: sin parámetros -> últimas 24 h; solo `start`; solo `end`; solo fecha = 00:00 UTC; sin zona = UTC; con zona; `start >= end`; `min_mag` válido, negativo, `abc`, `nan`, `inf`, vacío; `country_id` `esp` -> `ESP`, `none`, `NONE` -> `none`, `ES`, `E1A`; `mode` `live`/`replay`/`otro`; `limit` 1, máximo, 0, -1, `1.5`, `abc`, máximo+1; parámetro repetido; parámetro desconocido ignorado. Los errores son `ApiError` con `code` y mensaje en español que nombra el parámetro.
  - Cubre: F3, F5, F4 (nunca NaN), FR-004.
  - Criterio: `uv run pytest tests/api/test_params.py -q` pasa; falla antes de implementar; el módulo no importa `fastapi` ni `asyncpg`.

- [x] T003 [P] [US2] `api/cursor.py` con `tests/api/test_cursor.py`: `encode_cursor`/`decode_cursor` ida y vuelta (con `id` que contiene caracteres no ASCII y comillas); cadenas inválidas (no base64, JSON roto, tipos erróneos, vacío) -> `invalid_cursor`.
  - Cubre: F5.
  - Criterio: `uv run pytest tests/api/test_cursor.py -q` pasa; falla antes.

- [x] T004 [US5] `api/errors.py` (`ApiError`, `register_error_handlers`) y `api/main.py` (registra manejadores; `openapi_url=None` además de `docs_url`/`redoc_url` a `None`) con `tests/api/test_errors.py` (cliente `httpx` con `ASGITransport` y una ruta de prueba): `ApiError` -> su estado y cuerpo; 404 -> `not_found`; 405 -> `method_not_allowed` con `Allow`; excepción no controlada -> 500 `internal_error` sin traza; `/openapi.json`, `/docs` y `/redoc` -> 404 con cuerpo común; todas con `Content-Type: application/json`.
  - Cubre: F10, FR-013, pendiente heredado de `002` (404/405).
  - Criterio: `uv run pytest tests/api/test_errors.py -q` pasa; ningún cuerpo contiene `detail`.

- [x] T005 [P] [US1] Banco de pruebas de integración: `tests/support/temp_database.py` (campos `api_user`/`api_password`, `api_pool()`), `tests/integration/conftest.py` (pasa `DB_API_PASSWORD`) y `tests/support/api_seed.py` (inserta eventos `synthetic-…` y países como administrador en `live.current_event` y `replay.current_event`, con `date_dim`), con `tests/integration/test_api_harness.py`.
  - Cubre: base de F1–F8 (pruebas con el rol real, FR-014).
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_harness.py -q` pasa: el pool del rol `observatory_api` lee los eventos sembrados en `live` y `replay`; el resto de la suite de integración sigue en verde.

## Bloque 2 — Eventos: serialización, SQL, endpoint, paginación y modo `replay`

**Objetivo**: `/api/eventos` completo contra la base temporal. **Dependencias**: bloque 1.

- [x] T006 [P] [US1] `api/serializers.py` con `tests/api/test_serializers.py`: `build_feature(row)` y `build_metadata(...)` según `api.md` §3.2–§3.4: once campos de `properties`, `coordinates = [lon, lat, depth]`, nulos como `null`, `Decimal` -> `float`, mag y profundidad negativas, país nulo (ambos campos `null`), `JSON` sin NaN/Infinity (`json.dumps(allow_nan=False)`).
  - Cubre: F1, F2, F4, FR-018.
  - Criterio: `uv run pytest tests/api/test_serializers.py -q` pasa; falla antes.

- [x] T007 [P] [US1] `api/sql_filters.py` con `tests/api/test_sql_filters.py`: `build_where(filters, cursor)` devuelve fragmento y lista de parámetros posicionales; el esquema sale de la lista cerrada (`replay` -> `replay.current_event`); ningún valor del cliente aparece en el texto SQL (se prueba con `country_id` y cursor con comillas); sin `min_mag`/país/cursor no hay condiciones sobrantes.
  - Cubre: F3, F10, FR-014.
  - Criterio: `uv run pytest tests/api/test_sql_filters.py -q` pasa; falla antes.

- [x] T008 [US1] `api/db_access.py` (transacción `REPEATABLE READ` de solo lectura con `acquire(timeout)`) y `api/queries.py` (`fetch_events_page`, `fetch_counts` -> `total` y `null_count`, `fetch_last_ingestion_ms` existente) con `tests/integration/test_api_queries.py`: rango `[start, end)` con eventos justo en `start` y en `end`; `min_mag` con mag nula y negativa; `country_id` y `none`; una revisión (misma `event_id`, mayor `updated`) aparece una vez; el orden es `event_time` e `id` descendentes.
  - Cubre: F1, F3, F4, F11, FR-002, FR-005, FR-006.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_queries.py -q` pasa; falla antes.

- [x] T009 [US1] `api/routers/events.py` y registro en `api/main.py`, con `tests/integration/test_api_events.py` (cliente `httpx` y rol real): sin parámetros -> 200, `application/json`, solo últimas 24 h, `FeatureCollection` con `metadata` de ocho campos; sin eventos -> `features: []`, `count 0`, `total 0`, `truncated false`, `next_cursor null`; `start` solo fecha / con zona / sin zona; `min_mag=0` con mag nula (`null_mag_excluded`) y negativa; `country_id` `esp`/`ESP`/`none`/`ZZZ`; evento con mag, profundidad y país nulos.
  - Cubre: F1, F2, F3, F4, SC-001, SC-006.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_events.py -q` pasa; falla antes; la respuesta pasa `json.dumps(allow_nan=False)`.

- [x] T010 [US2] Paginación en `api/routers/events.py` y `api/queries.py`, con `tests/integration/test_api_pagination.py`: 25 eventos y `limit=10` -> `count` 10, 10 y 5, `total` 25 y `truncated true` en las tres, `next_cursor` nulo solo en la última, unión de 25 ids sin repetidos; eventos con el mismo `time` (desempate por `id`); revisión de un evento entre página 1 y 2 sin repetirlo ni moverlo; `limit` > máximo (`ApiSettings(max_events=…)` bajo en la prueba), `limit=0`, cursor mal formado -> 400; sin `limit` y más eventos que el máximo -> `truncated true` y `total` real.
  - Cubre: F5, SC-002.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_pagination.py -q` pasa; falla antes.

- [x] T011 [US5] Modo `replay` en eventos: `tests/integration/test_api_replay_events.py` (el código ya lo admite por `sql_filters`; la tarea ajusta lo que falte): con `replay.current_event` vacía -> 200, `metadata.mode "replay"`, `features []`, `total 0`; con un evento sintético solo en `replay` aparece con `mode=replay` y no con `live`, y a la inversa; `last_ingestion` igual que en `live`; `mode=otro` -> 400.
  - Cubre: F12 parcial, constitución §7.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_replay_events.py -q` pasa.

## Bloque 3 — Estadísticas

**Objetivo**: `/api/estadisticas` calculado en SQL y coherente con `/api/eventos`. **Dependencias**: bloque 2.

- [x] T012 [P] [US3] `api/stats_builder.py` con `tests/api/test_stats_builder.py` (puro): horas con cero desde la hora de `start` hasta la de `end − 1 ms`; tramos de magnitud (8) y profundidad (5) a partir de filas `width_bucket`, con ceros y `lower`/`upper` nulos en los extremos; `by_country` con el elemento sin país una vez y `no_value` igual a su recuento; comparación (`daily_mean_2025 = n/365`, `diff_abs`, `variation_pct` a 2 decimales y `null` si la media es 0, `min_mag_applied = max(min_mag, 4.0)`, `recent_incomplete true`); ejemplo de `api.md` §5.2 reproducido (24 vs 12 410 -> `-29.41`).
  - Cubre: F7, FR-009.
  - Criterio: `uv run pytest tests/api/test_stats_builder.py -q` pasa; falla antes.

- [x] T013 [US3] `api/stats_queries.py` (por hora, por país, histogramas con `width_bucket`, comparación) con `tests/integration/test_api_stats_queries.py`: cada resultado coincide con una cuenta SQL directa hecha como administrador sobre los mismos eventos sintéticos (incluye magnitud nula, magnitud negativa, profundidad negativa y nula, evento sin país).
  - Cubre: F7, FR-008, constitución §8.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_stats_queries.py -q` pasa; falla antes.

- [x] T014 [US3] `api/routers/stats.py` y registro en `api/main.py`, con `tests/integration/test_api_stats.py`: forma completa de `api.md` §5.1 (`metadata`, `period`, `filters`, `total`, `by_hour`, `by_country`, `histograms`, `comparison`); `limit` y `cursor` se ignoran; `period` = rango efectivo; `filters.country_id` normalizado (`"ESP"`, `"none"` o `null`); `mode=replay` -> `comparison null`, ceros y `total 0`; mismos errores 400 que eventos.
  - Cubre: F7, FR-004, FR-009, US3 escenario 6.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_stats.py -q` pasa; falla antes.

- [x] T015 [US3] Coherencia: `tests/integration/test_api_coherence.py` con cinco combinaciones de filtros (con `min_mag`, con `country_id`, con `none`, con rango, combinados) sobre los mismos eventos: `total` de estadísticas == `metadata.total` de eventos == suma de `by_hour` == suma de `by_country`; identidades de data-model §5 para los histogramas; `magnitude.no_value == null_mag_excluded` con `min_mag`.
  - Cubre: F7, SC-003, FR-010.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_coherence.py -q` pasa en las cinco combinaciones.

- [x] T016 [US3] Comparación con histórico: `tests/integration/test_api_comparison.py` con eventos sintéticos en 2025 y en las últimas 24 h: `n_2025`, `n_recent`, `daily_mean_2025 = n_2025/365`, `diff_abs`, `variation_pct`; `min_mag_applied` con `min_mag` ausente (4.0), 2 (4.0) y 5.5 (5.5); el filtro de país se aplica a ambos lados; media 0 -> `variation_pct null`; `reference_period` y `recent_period` en ms.
  - Cubre: F7, `api.md` §5.1.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_comparison.py -q` pasa.

## Bloque 4 — Salud, fallo de la base, errores y permisos

**Objetivo**: F6, F8 y F10 con pruebas automáticas. **Dependencias**: bloque 3 (T017 y T020 pueden ir en paralelo con el bloque 3 si hace falta).

- [x] T017 [US4] `api/routers/health.py` adaptado a `db_access` (mismo manejo de errores que los otros dos) con `tests/integration/test_api_health.py`: 200 con `status "ok"`, `last_ingestion` en ms con una ejecución correcta sembrada y `null` sin ingestas, `generated` en ms, sin credenciales ni datos de conexión; ignora `mode`.
  - Cubre: F6, FR-011.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_health.py -q` pasa; el healthcheck de `compose.yaml` (`GET /api/salud`) sigue funcionando (se comprueba en T021).

- [x] T018 [US4] 503 en los tres endpoints: `tests/integration/test_api_database_down.py` con un pool hacia un puerto cerrado (y otro cerrado a propósito): `/api/eventos`, `/api/estadisticas` y `/api/salud` -> 503 `database_unavailable` con el mensaje del contrato, en menos de 10 s medidos; ninguna respuesta 200 ni `features: []`; con el pool bueno restaurado, 200 sin reiniciar la app.
  - Cubre: F8, SC-004, FR-012.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_database_down.py -q` pasa.

- [x] T019 [US5] Errores y superficie: `tests/integration/test_api_errors.py`: cada petición inválida de US5 (parámetros erróneos en eventos y estadísticas, `/api/foo`, `/`, `POST/PUT/PATCH/DELETE`) devuelve el estado y el `code` esperados con cuerpo `{"error": {"code", "message"}}`, ninguno 422 ni `detail`; el listado de rutas de la app es exactamente las tres de lectura; todas las respuestas son `application/json`; un fallo inesperado en una consulta (doble que lanza `RuntimeError`) -> 500 `internal_error` sin traza ni SQL.
  - Cubre: F10, SC-005, FR-013, FR-016.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_errors.py -q` pasa.

- [x] T020 [P] [US4] Solo lectura: `tests/integration/test_api_readonly.py`: con el rol `observatory_api` real, `INSERT`, `UPDATE` y `DELETE` sobre `live.current_event`, `replay.current_event`, `public.country` e `ingest.ingest_run` fallan con permiso denegado; una prueba estática comprueba que ninguna cadena SQL de `api/` contiene `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `CREATE` ni `DROP`.
  - Cubre: F10, F11, SC-008, FR-014, FR-017.
  - Criterio: `docker compose --profile test run --rm tests pytest tests/integration/test_api_readonly.py -q` pasa.

## Bloque 5 — Verificación real, evidencias y cierre

**Objetivo**: demostrar lo anterior contra el stack y los datos reales, y cerrar la feature. **Dependencias**: bloques 1 a 4.

- [x] T021 [US1] Recorrido real con `curl` contra datos cargados (quickstart §2): levantar el stack, cargar el histórico 2025 (feature `006`) y dejar al productor en vivo; consultar `/api/eventos` sin parámetros, con `min_mag`, `country_id` (`jpn`, `none`), un día de 2025 y paginando con `next_cursor`; `/api/salud`; `mode=replay` en eventos y estadísticas; confirmar que el healthcheck de la API sigue `healthy`. Guardar cada salida (cabeceras y cuerpo, recortados) en `docs/evidencias/api/`.
  - Cubre: F1–F6, F11, F12 parcial, SC-001, SC-007.
  - Criterio: archivos `recorrido_*.txt` en `docs/evidencias/api/`; 200 con la forma del contrato; solo eventos de 24 h sin ids repetidos; `is_synthetic` false en los reales; `docker compose ps` muestra `api` healthy.

- [x] T022 [US4] Fallo de la base y errores con `curl` (quickstart §3): con la API en marcha, `docker compose stop postgres`; los tres endpoints -> 503 `database_unavailable` en menos de 10 s (`curl -w "%{time_total}"`); `docker compose start postgres` y 200 sin reiniciar la API. Además `curl -i` de `/api/foo` (404), `POST /api/eventos` (405 con `Allow`), `min_mag=abc`, `limit=0`, `cursor=xx`, `mode=otro` (400), `/docs` y `/openapi.json` (404). Guardar en `docs/evidencias/api/`.
  - Cubre: F8, F10, SC-004, SC-005.
  - Criterio: `docs/evidencias/api/fallo_bd_503.txt` y `errores_404_405_400.txt` con estado, cuerpo y tiempo; ninguna respuesta con `detail`.

- [x] T023 [US3] Coherencia contra los datos reales: para cinco combinaciones de filtros (incluidos `min_mag`, `country_id`, `none` y un rango de 2025), `total` de estadísticas == `metadata.total` de eventos == suma de `by_hour` == suma de `by_country`; y una cuenta SQL independiente (administrador, `docker compose exec postgres psql`) de eventos de 2025 con `mag >= 4` coincide con `comparison.n_2025`. Si algo no cuadra, se corrige antes de continuar. Guardar en `docs/evidencias/api/coherencia_real.txt` junto con el SQL usado.
  - Cubre: F7, SC-003, SC-007, FR-010.
  - Criterio: el archivo muestra las cinco comparaciones iguales y la cuenta SQL igual a `n_2025`.

- [x] T024 [US5] Documentación y mapa: sección «API de consulta» en `README.md` (endpoints, parámetros, variables `API_MAX_EVENTS` y `API_DB_TIMEOUT_SECONDS`, comandos de prueba, límites conocidos, CORS en `despliegue`), filas de `CODEMAP.md` (sustituye las previstas de `api/routers/events.py` y `api/queries.py` y añade las nuevas; historial de features), una fila en `docs/evidencias/sprint/decisiones.md` (P1, P2, P3 y la transacción de lectura única), `.env.example` comprobado.
  - Cubre: constitución §10 y §16, FR-019.
  - Criterio: `python scripts/check_env_example.py` sale con 0; cada archivo nuevo de `api/` y `tests/` figura en `CODEMAP.md`; el README enumera las dos variables nuevas.

- [x] T025 [US5] Cierre: pasar toda la suite (`uv run pytest -m "not integration" -q` y la de integración en Compose) y guardar las salidas en `docs/evidencias/api/`; comprobar con `git diff --stat` que `specs/001-contratos-y-modelo/contracts/`, `docs/enunciado/`, `sql/` y `specs/002-infra-compose/contracts/config.md` no cambian; marcar F1–F8, F10, F11 en el checklist según corresponda (F9 -> `despliegue`; F12 se completa en replay); detenerse y esperar la revisión del alumno, sin commit.
  - Cubre: F1–F8, F10, F11, constitución §15, §16 y §19.
  - Criterio: suites en verde; `git diff --stat` sin esas rutas; `docs/evidencias/api/` contiene las evidencias de T021 a T025.

## Dependencias y orden

```text
Bloque 1: T001 -> T004 -> (T002, T003, T005 en paralelo)
Bloque 2: T006, T007 [P] -> T008 -> T009 -> T010 -> T011
Bloque 3: T012 [P] -> T013 -> T014 -> T015 -> T016
Bloque 4: T017 -> T018 -> T019 ; T020 [P] tras T005 y T008
Bloque 5: T021 -> T022 -> T023 -> T024 -> T025
```

T002 y T003 lanzan `ApiError`, que define T004; por eso T004 va antes aunque su número sea mayor. T018 necesita el pool y `db_access` de T008.

## Cobertura de requisitos

| Requisito | Tareas |
|---|---|
| F1, F2 | T006, T008, T009, T021 |
| F3 | T002, T007, T008, T009 |
| F4 | T006, T008, T009 |
| F5 | T001, T002, T003, T010 |
| F6 | T017, T021 |
| F7 | T012–T016, T023 |
| F8 | T018, T022 |
| F9 | Fuera de esta feature (P1) |
| F10 | T004, T007, T019, T020, T022 |
| F11 | T008, T020, T021 |
| F12 (parcial) | T011, T014, T021 |
| FR-001 a FR-020 | Ver «Cubre» de cada tarea |
