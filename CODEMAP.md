# Mapa del código

Estado: feature `contratos-y-modelo` cerrada (2026-11-02): existen los contratos, el DDL, el modelo de datos y sus evidencias. Las demás rutas de la tabla son las **previstas**; se confirman al cerrar cada feature.

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
| Cómo se decide qué se publica | producer/ingest_state.py, producer/main.py | B6 |
| Qué versión gana | common/processing.py::is_newer_version | C4 |
| Cómo se asigna el país | common/geo.py | C9–C12 |
| Qué va a cuarentena y por qué | common/validation.py, consumer/writer.py | C5 |
| Qué devuelve la API de eventos | api/routers/events.py, api/queries.py | F1–F3 |
| Cómo el panel consume la API | frontend/src/app/core/api.service.ts | G1, G9 |

## Flujo de un evento (de USGS al mapa)
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
