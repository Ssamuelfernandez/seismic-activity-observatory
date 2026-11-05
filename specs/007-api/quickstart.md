# Quickstart: validar la API de consulta

Guía de validación; no contiene código de la feature. Contratos: `specs/001-contratos-y-modelo/contracts/api.md` y `db-schema.md`. Modelo interno: [data-model.md](data-model.md). Las evidencias se guardan en `docs/evidencias/api/`.

## 0. Requisitos

- `.env` copiado de `.env.example` (con `API_MAX_EVENTS` y `API_DB_TIMEOUT_SECONDS`), Docker Desktop en marcha.
- Imagen reconstruida tras los cambios: `docker compose build producer` (la reutilizan `consumer` y `api`) y `docker compose --profile test build tests`.
- Volumen de PostgreSQL con los roles de `002`. Si es antiguo: `docker compose down -v` (borra datos) y volver a cargar el histórico.

## 1. Pruebas automáticas

1. Unitarias (sin Docker): `uv run pytest -m "not integration" -q`.
2. Integración (base temporal, rol `observatory_api`): `docker compose up -d postgres` y `docker compose --profile test run --rm tests pytest -m integration -q`.
3. Salida esperada: todo en verde, sin saltos. La evidencia de cada bloque va a `docs/evidencias/api/`.

## 2. Recorrido real con datos cargados

1. `docker compose up -d` (postgres, kafka, productor, consumidor, api); esperar a `healthy` (`docker compose ps`).
2. Cargar el histórico 2025 con los comandos de la sección «Histórico 2025» del README (feature `006`); dejar al productor en vivo unos minutos.
3. Consultas (en `http://127.0.0.1:8000`, lo único publicado). Esperado entre paréntesis:
   - `/api/eventos` sin parámetros (200, solo últimas 24 h, `count` ≤ `total`, sin ids repetidos).
   - `/api/eventos?min_mag=4&country_id=jpn&limit=20` (países normalizados; paginar con `next_cursor`).
   - `/api/eventos?country_id=none` (solo «Sin país asignado»).
   - `/api/eventos?start=2025-03-01&end=2025-03-02` (histórico; `is_synthetic: false`).
   - `/api/estadisticas` y con los mismos filtros que arriba (`total` igual que `metadata.total`).
   - `/api/salud` (`status: ok`, `last_ingestion` reciente).
   - `mode=replay` en eventos y estadísticas (`features: []`, `total: 0`, `comparison: null`).
4. Coherencia: comparar `total` de ambos endpoints y `comparison.n_2025` con una cuenta SQL independiente (administrador) de eventos de 2025 con `mag >= 4`.

## 3. Fallos y errores

1. Con la API en marcha: `docker compose stop postgres`; `curl` a los tres endpoints -> 503 `database_unavailable` en menos de 10 s (medir con `curl -w`). `docker compose start postgres`; repetir -> 200 sin reiniciar la API.
2. `curl -i` a `/api/foo` (404 `not_found`), `POST /api/eventos` (405 `method_not_allowed` con `Allow`), `?min_mag=abc`, `?limit=0`, `?cursor=xx`, `?mode=otro` (400 con el código del contrato). Ningún cuerpo es `{"detail": …}`.
3. `/docs` y `/openapi.json` no existen (404); no hay rutas de administración.

## 4. Cierre

`python scripts/check_env_example.py` sin problemas; `git diff` sin cambios en contratos, `docs/enunciado/` ni `sql/001_schema.sql`; `CODEMAP.md` y README actualizados. Después, parar y esperar la revisión del alumno.
