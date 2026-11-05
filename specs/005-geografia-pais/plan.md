# Plan de implementación: Geografía y país

**Rama**: `005-geografia-pais` | **Spec**: [spec.md](spec.md) | **Cubre**: C9–C12; pruebas de aceptación 5 y 7 (y refuerzo de la 6).

Solo diseño: este plan no contiene código de aplicación, Dockerfile ni compose (constitución §19). La implementación espera a la revisión del alumno.

## 1. Resumen

El consumidor ya valida, versiona y escribe (`003`). Esta feature añade tres cosas: (1) una función pura que da el país de un punto por geometría (`common/geo.py`); (2) la carga del catálogo en `public.country` y la comprobación del esquema al arrancar (lo diferido de `003`); (3) el `country_id` en la fila de `current_event`. Todo lo demás (validez, cuarentena, versiones) se reutiliza. Detalle en [research.md](research.md) y [data-model.md](data-model.md).

## 2. Contexto técnico

- **Lenguaje y runtime**: Python 3.12 (ya fijado). **Dependencia nueva**: `shapely` 2.x (D1). Sin GeoPandas.
- **Almacenamiento**: PostgreSQL 16, sin cambios de DDL ni de permisos (el rol del consumidor ya tiene `SELECT, INSERT, UPDATE` sobre `public.country`).
- **Pruebas**: `pytest` unitarias sin red; integración con base temporal en el servicio `tests` (como `003`).
- **Rendimiento**: índice `STRtree` construido una vez al arrancar (FR-019).
- **Restricciones**: `kafka-message.md`, `db-schema.md` y `sql/001_schema.sql` sin tocar (FR-017, SC-009); sin variables de entorno nuevas (`COUNTRY_CATALOG_PATH` ya está en `compose.yaml`); sin secretos.
- **Escala**: 177 polígonos, unas decenas de eventos por minuto: sin riesgo de rendimiento.

## 3. Revisión contra la constitución

| Principio | Cumple | Cómo |
|---|---|---|
| §1 Idempotencia | Sí | Asignar país es determinista; reprocesar da el mismo `country_id` (SC-001) |
| §2 Versionado por `updated` | Sí | El país viaja en la fila que el upsert condicional ya protege (D5) |
| §4 País por geometría, `NULL` = sin país | Sí | `place` no interviene; sin polígono = `NULL`, el evento cuenta |
| §5 Nulos y negativos | Sí | `mag` nula se conserva; se añade la prueba (T017) |
| §6 Cuarentena | Sí | Sin motivos nuevos; lat 145 va a cuarentena sin país |
| §7 Sintéticos separados | Sí | `is_synthetic = true`, ids `synthetic-geo-…` |
| §8 Agregaciones desde estado actual | Sí | Recuentos con/sin país por SQL sobre `current_event` |
| §9, §10 Servicios y secretos | Sí | Sin servicios ni secretos nuevos |
| §11 Versiones fijadas | Sí | `shapely` en `pyproject.toml` + `uv.lock`; imagen por `uv sync --frozen` |
| §12 Alcance cerrado | Sí | Sin histórico, replay, API, frontend ni contadores nuevos |
| §14 Una responsabilidad; lo puro separado | Sí | `common/geo.py` puro; E/S en `consumer/schema_check.py` y `catalog_loader.py`; SQL en `queries.py` |
| §15 Contratos únicos | Sí | No se duplican ni se modifican; se cita `db-schema.md` §1.1 |
| §16 Cierre | Prevista | Evidencias, `CODEMAP.md` y README (T022–T023) |
| §19 Una feature cada vez | Sí | Este plan no contiene código |

Sin violaciones; la tabla de complejidad no hace falta.

## 4. Estructura (rutas que se tocan)

```text
common/geo.py              NUEVO  parse_country_catalog, build_country_index, assign_country (puro)
common/records.py          CountryRow (+ docstring de EventRows)
common/transform.py        build_event_rows recibe country_id (puro)
consumer/schema_check.py   NUEVO  ensure_schema_ready, SchemaNotReadyError (E/S)
consumer/catalog_loader.py NUEVO  load_country_catalog: lee el archivo, parsea, upsert, devuelve el índice (E/S)
consumer/queries.py        country_id en CURRENT_COLUMNS; consulta de recuento de country; consulta to_regclass
consumer/pipeline.py       PipelineDeps.locate; llamada antes de build_event_rows; línea country_tie
consumer/loop.py, main.py  orden de arranque y ruta del catálogo (COUNTRY_CATALOG_PATH)
pyproject.toml, uv.lock    dependencia shapely fijada
scripts/geo_real_day.py    NUEVO  muestra real de un día (SC-007)
scripts/consumer_scenarios/geo.py + scripts/verify_consumer.py   escenario `geo` con Kafka real (pruebas 5 y 7)
tests/...                  ver tasks.md
docs/evidencias/geografia-pais/, docs/borradores/geografia-pais.md, CODEMAP.md, README.md
```

Los archivos de código nuevos respetan el límite de 250 líneas y el de 30 líneas por función (CC-14 de `003`); si `common/geo.py` creciera, se divide el parseo del catálogo en otro archivo.

## 5. Flujo

```text
Arranque:  check_database -> pool -> ensure_schema_ready -> load_country_catalog (parsea, unicidad, upsert, índice)
           -> start_consumer -> bucle
Mensaje:   decode -> validate -> [válido] assign_country(lon, lat) -> build_event_rows(country_id) -> write_event
                              -> [inválido] cuarentena (sin país)
```

## 6. Orden de implementación

1. `common/geo.py` y su prueba, con el catálogo real y catálogos sintéticos mínimos (bloque 1).
2. Esquema y carga del catálogo (bloque 2).
3. País en la fila y en el pipeline, y arranque conectado (bloque 3).
4. Casos sintéticos, pruebas de aceptación y escenario con Kafka real (bloque 4).
5. Evidencias, `CODEMAP.md`, README, borrador y comprobación de contratos (bloque 5).

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Las ruedas de Shapely no entran en la imagen `slim` | T001 lo comprueba antes de seguir; si falla se escala al alumno |
| `covered_by` no incluye el borde como se espera | T004 lo prueba con aristas compartidas y con un vértice real del catálogo |
| Madrid o el Atlántico no dan lo esperado con el catálogo 110m | Los casos reales se prueban en T005; el catálogo no se modifica, se ajusta el punto del caso y se anota |
| Dos pruebas existentes afirman "sin `country_id`" | Se reescriben en T010 (D5) |
| El stack no arranca entre T013 y T014 (`PipelineDeps.locate` obligatorio antes del cableado) | Ambas tareas se hacen seguidas; no se levanta Compose entre ellas |

## 8. Preguntas para el alumno

Siguen abiertas las tres de la spec con su decisión provisional aplicada en este plan: (1) Shapely 2 sin GeoPandas; (2) sin motivo nuevo para `type != earthquake` en el consumidor; (3) catálogo cargado por el consumidor al arrancar. No surgen preguntas nuevas que toquen contratos.
