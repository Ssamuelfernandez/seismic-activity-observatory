# Mapa del código

Estado: features `contratos-y-modelo` (2026-11-02) e `infra-compose` (2026-11-04) cerradas: existen los contratos, el DDL, el modelo de datos, el stack de Compose con productor, consumidor y API **mínimos** y sus evidencias. Las filas de `infra-compose` son rutas reales; las demás filas de la tabla son las **previstas** y se confirman al cerrar cada feature.

## Dónde está cada cosa
| Quiero entender… | Mira… | Requisito |
|---|---|---|
| Cómo se explora el feed de USGS | scripts/explore_usgs.py | B2 |
| Qué mensaje viaja por Kafka y qué motivos de cuarentena existen | specs/001-contratos-y-modelo/contracts/kafka-message.md | C4 |
| Qué tablas e índices tiene la base y por qué | specs/001-contratos-y-modelo/contracts/db-schema.md | E2, E3, E7 |
| Qué contrato tiene la API con el panel | specs/001-contratos-y-modelo/contracts/api.md | F1–F3 |
| El DDL del esquema (`public`, `live`, `replay`, `ingest`) | sql/001_schema.sql | E5 |
| Los modelos conceptual, lógico y físico | specs/001-contratos-y-modelo/data-model.md (borrador); docs/memoria.md §5 | E1, E4 |
| Las pruebas del esquema en PostgreSQL 16 y la revisión de la API | docs/evidencias/contratos-y-modelo/ | E5, SC-005 |
| Cómo se levantan, comprueban y reinician los cinco servicios | compose.yaml; README.md (sección «Ejecución con Docker Compose»); specs/002-infra-compose/quickstart.md | A1, A2, A8, A9, A12 |
| Qué imagen Python usan productor, consumidor y API y cómo se fijan las versiones | Dockerfile, pyproject.toml, uv.lock, .python-version, .dockerignore | A3, A11 |
| Qué variables de entorno hay y cuáles lee el código | .env.example; specs/002-infra-compose/contracts/config.md; common/config.py; scripts/check_env_example.py | A10 |
| Cómo se reintenta la conexión a Kafka y PostgreSQL | common/retry.py, common/db.py | A4 |
| Cómo se calcula la salud de productor y consumidor (latido) y los umbrales | common/health.py; consumer/loop.py::broker_reachable; specs/002-infra-compose/contracts/config.md §E | A4 |
| Cómo se crean los temas y su retención de 7 días | common/kafka_topics.py; compose.yaml (broker); README.md (sección «Retención de Kafka») | A6 |
| El evento sintético de prueba (`is_synthetic = true`) | common/synthetic_event.py | A1 |
| El productor mínimo | producer/ (`main.py`, `loop.py`, `publisher.py`) | A1, A4, A10 |
| El consumidor mínimo (solo registra, no escribe) | consumer/ (`main.py`, `loop.py`) | A1, A4 |
| La API mínima (`GET /api/salud`) | api/ (`main.py`, `queries.py`, `routers/health.py`) | A1, A9 |
| Los roles de base de datos y sus permisos | sql/002_roles.sql; specs/002-infra-compose/data-model.md | E5 (db-schema.md §1.1) |
| Cómo se inicializa PostgreSQL (esquema y roles) la primera vez | scripts/postgres_init.sh | A5 |
| Las pruebas unitarias | tests/ (`common/`, `producer/`, `consumer/`); `uv run pytest` | A4, A10 |
| La verificación de punta a punta del stack | scripts/verify_stack.py | A1–A12 |
| Las evidencias de infra-compose (arranque, clon limpio, reintentos, latido, 503, M7–M9, secretos…) | docs/evidencias/infra-compose/ | A1–A12, M7–M9 |
| La spec, el plan y las tareas de infra-compose | specs/002-infra-compose/ | A1–A12 |
| Cómo se decide qué se publica | producer/ingest_state.py, producer/main.py | B6 |
| Qué versión gana | common/processing.py::is_newer_version | C4 |
| Cómo se asigna el país | common/geo.py | C9–C12 |
| Qué va a cuarentena y por qué | common/validation.py, consumer/writer.py | C5 |
| Qué devuelve la API de eventos | api/routers/events.py, api/queries.py | F1–F3 |
| Cómo el panel consume la API | frontend/src/app/core/api.service.ts | G1, G9 |

## Flujo actual (infra-compose, eventos sintéticos)
common/synthetic_event.py -> producer/loop.py -> producer/publisher.py -> Kafka (`earthquakes.live`)
     -> consumer/loop.py (solo registra) ; API: api/routers/health.py -> api/queries.py -> PostgreSQL (rol de solo lectura)

## Flujo previsto de un evento (de USGS al mapa)
USGS -> producer/usgs_client.py -> producer/publisher.py -> Kafka
     -> consumer/pipeline.py -> common/validation.py -> common/geo.py
     -> consumer/writer.py -> PostgreSQL -> api/queries.py -> frontend/features/map

## Convenciones
Reglas completas en `docs/planificacion/03-procedimiento-ejecucion.md` §7.3. Resumen:
- Una función, una responsabilidad; unas 30 líneas como máximo por función y 250 por archivo.
- La lógica pura (validar, transformar) va separada del I/O (BD, Kafka, HTTP).
- `main.py` solo configura y arranca; no contiene lógica.
- Sin números ni textos mágicos: van a `config.py` o a constantes con nombre.
- Logging en vez de `print`, y errores con nombre en vez de `except Exception: pass`.

## Historial de features cerradas
| Feature | Qué añadió | Fecha |
|---|---|---|
| contratos-y-modelo | Contratos del mensaje Kafka, de la base de datos y de la API; `sql/001_schema.sql`; modelo de datos conceptual, lógico y físico; evidencias de las pruebas del esquema (E1–E5, E7, C4) | 2026-11-02 |
| infra-compose | `compose.yaml` con Kafka (KRaft), PostgreSQL 16, productor, consumidor y API; imagen Python compartida con `uv.lock`; `.env.example`; reintentos, latido y healthchecks; temas con retención de 7 días; roles de base de datos (`sql/002_roles.sql`); productor, consumidor y API mínimos con eventos sintéticos; `verify_stack.py` y `check_env_example.py`; pruebas unitarias; evidencias en `docs/evidencias/infra-compose/` (A1–A12; M7–M9 verificados) | 2026-11-04 |
