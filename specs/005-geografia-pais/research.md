# Investigación: Geografía y país

Decisiones de diseño con su motivo. Las tres primeras aplican las decisiones provisionales de la spec ("Preguntas para el alumno"); si el alumno las cambia, se revisa aquí.

## D1. Librería de geometría: Shapely 2 solo, sin GeoPandas

- **Decisión**: dependencia nueva `shapely` (rama 2.x), fijada con versión exacta en `pyproject.toml` y `uv.lock` (constitución §11). La versión exacta la fija `uv lock` en la tarea T001, no se inventa aquí.
- **Motivo**: Shapely 2 trae `STRtree`, `Point` y los predicados que hacen falta. GeoPandas añadiría pandas, numpy extra y más ruedas a una imagen que ya comparten productor, consumidor y API, sin aportar nada que el consumidor use (no hay tablas de geometrías, solo un punto por mensaje).
- **Alternativas descartadas**: GeoPandas (peso y superficie sin beneficio); PostGIS (el DDL y la imagen de PostgreSQL ya están fijados, `db-schema.md` no lo prevé); algoritmo propio de punto en polígono (más código que defender y más fallos en bordes).
- **Impacto**: la imagen es una sola (`Dockerfile` hace `uv sync --frozen`), así que el cambio de `uv.lock` basta para que entre en producción y en `tests`. Las ruedas de Shapely incluyen GEOS; se comprueba en T001 que importa dentro de la imagen `production`.

## D2. Frontera: el borde cuenta como dentro

- **Decisión**: un punto pertenece a un país si el polígono lo **cubre** (`covers`): el borde incluido. Con `STRtree.query(punto, predicate="covered_by")` (el punto está cubierto por el polígono; equivale a "el polígono cubre el punto"). Para un punto, `intersects` da el mismo resultado; se mantiene `covered_by` por ser el nombre del roadmap y del contrato. Una prueba con un punto en la arista compartida de dos cuadrados lo confirma.
- **Motivo**: con `within`/`contains` un punto en la frontera caería en "sin país" (C11). El comportamiento de borde se documenta en una línea en `docs/borradores/geografia-pais.md`.

## D3. Empate: `ADM0_A3` menor en orden alfabético

- **Decisión**: si el punto está cubierto por varios polígonos (frontera compartida, territorios solapados), se elige el menor `ADM0_A3`. Se ordena la lista de candidatos y se toma el primero.
- **Motivo**: determinista y independiente del orden del archivo y del orden en que devuelva los índices el `STRtree` (la prueba invierte el orden del catálogo y comprueba el mismo resultado). Sirve igual en el histórico y el replay (constitución §14).
- **Trazabilidad**: si hay más de un candidato, el consumidor escribe una línea de log (`country_tie event_id=… candidates=… chosen=…`). No es un contador nuevo (C8 no se amplía).

## D4. Sin polígono: `NULL`, nunca el país más cercano

- **Decisión**: ningún candidato → `country_id = NULL`; el evento se guarda y cuenta (C12, prueba 7). Se apoya en el DDL ya existente (`current_event.country_id` es nullable y tiene FK a `public.country`).
- **Límite conocido**: el catálogo es `ne_110m` (simplificado). Costas y territorios pequeños pueden salir sin país. No se afirma precisión cartográfica.

## D5. Dónde se calcula: en `process_record`, después de validar y antes de escribir

- **Decisión**: `pipeline._write_valid` llama a un localizador inyectado (`deps.locate(lon, lat)`) justo antes de `build_event_rows`, solo para mensajes válidos. El país viaja en `EventRows.current["country_id"]` y se escribe en el mismo `INSERT … ON CONFLICT DO UPDATE` de `current_event`.
- **Motivo**: la regla "gana el `updated` mayor" ya está en el `WHERE EXCLUDED.updated_ms > current_event.updated_ms` del upsert. Si la versión nueva gana, sus columnas (incluido `country_id`, también `NULL`) sustituyen a las anteriores; si pierde, no se toca nada (constitución §2). No hace falta lógica nueva de versiones.
- **Pureza**: `common/geo.py` no importa `asyncpg` ni `aiokafka` ni lee archivos; recibe un `dict` GeoJSON ya cargado. La lectura del archivo y la carga a la base viven en `consumer/catalog_loader.py` (E/S). `build_event_rows` sigue puro: recibe el `country_id` ya calculado como parámetro.
- **Inyección**: el localizador es un parámetro de `PipelineDeps`, así las pruebas unitarias usan un doble y la integración usa el índice real.
- **Cambios en pruebas existentes**: `tests/common/test_transform.py::test_country_id_is_absent` y `tests/consumer/test_queries.py::test_current_event_upsert_is_conditional_and_ignores_country` afirman lo contrario de esta feature (FR-021 de `003`). Se reescriben en T010.

## D6. Carga del catálogo y comprobación del esquema al arrancar (retoma T062–T067, T069, T080 de `003`)

- **Orden de arranque**: `check_database` → abrir pool → `ensure_schema_ready` → `load_country_catalog` (que parsea, comprueba unicidad, hace el upsert y devuelve el índice) → `start_consumer` → bucle. Si cualquiera de los dos primeros pasos falla, el proceso termina con error y Compose lo reinicia (A4); no se consume ningún mensaje.
- **Esquema**: `to_regclass` sobre las 8 tablas que usa el consumidor (`public.country`, `public.date_dim` y las tres de `live` y de `replay`); el error nombra la tabla que falta. No se comprueban columnas (el DDL lo aplica `postgres_init.sh`; límite conocido).
- **Carga**: una transacción con 177 `INSERT … ON CONFLICT (country_id) DO UPDATE … WHERE … IS DISTINCT FROM`. Ya existe `queries.COUNTRY_UPSERT`. La etiqueta del comando (`INSERT 0 1`/`INSERT 0 0`) no distingue insertada de actualizada; se calcula `inserted = count(*) después − count(*) antes` y `updated = cambiadas − inserted` (el rol tiene `SELECT` sobre `public.country`). Línea de log: `catalog loaded total=177 inserted=… updated=…`.
- **Unicidad y propiedades (C10)**: antes de tocar la base, `parse_country_catalog` comprueba que `ADM0_A3` existe, es único y cumple `^[A-Z]{3}$` (el `CHECK` del DDL), y que `NAME_ES`, `ADMIN`, `CONTINENT` y `SUBREGION` existen. El error nombra el código o campo y la posición. En el archivo real hay 177 distintos y 0 nulos (comprobado al diseñar).
- **Geometría**: solo `Polygon` y `MultiPolygon`; cualquier otra o una geometría vacía/inválida detiene el arranque con error nombrando la entidad. No se "repara" nada con `buffer(0)`: el archivo se usa tal cual.
- **Ruta**: `COUNTRY_CATALOG_PATH` ya está en `compose.yaml` (consumer) con el montaje de solo lectura; no hay variable nueva ni cambio en `.env.example`.

## D7. Reglas de validez (FR-013): sin código nuevo, solo pruebas

`common/validation.py` ya cubre `Point`, `lon`/`lat` finitos y en rango, `time`/`updated` enteros, `mag` nula y negativos (14 motivos de `kafka-message.md` §6). Esta feature añade pruebas de aceptación con los casos del brief (T017). Si una prueba descubriera un hueco, se corrige dentro de los motivos existentes (FR-013); un motivo nuevo exigiría tocar el contrato y se escala al alumno.

## D8. `type != earthquake` (pregunta 2 de la spec)

Se mantiene la decisión provisional: el consumidor no añade regla ni motivo nuevo. El caso sintético se demuestra en el productor con el mock de USGS (`tests/support/mock_usgs.py::synthetic_feature(event_type=…)`), que escribe una fila en `live.exclusion` y no publica (T018).

## D9. Datos reales de un día (SC-007)

Sin Kafka ni base: un script CLI (`scripts/geo_real_day.py`, `print` permitido en `scripts/`) lee un GeoJSON del feed `all_day` guardado en `docs/evidencias/geografia-pais/` (descargado una vez, real, sin marcar sintético), asigna país a cada punto con el mismo código de `common/geo.py` y escribe cuántos tienen país, cuántos no, y que todo `country_id` está en el catálogo. La prueba contra la base y el FK la cubren los casos sintéticos. Es una muestra de un momento; no se afirma cobertura general.

## D10. Rendimiento (FR-019)

El índice `STRtree` se construye una vez en el arranque y vive en el proceso (177 geometrías: milisegundos de construcción y microsegundos por consulta). Sin caché por mensaje. No se mide: es un hecho de diseño, no un requisito con umbral.

## Límites conocidos (una línea cada uno)

- Sin recálculo retroactivo de eventos ya guardados sin país (parte de base limpia).
- Catálogo simplificado (110m): costas y territorios pequeños pueden salir como "sin país".
- Antimeridiano: se usa el punto tal cual en [-180, 180] y el resultado del catálogo.
- Cambiar el catálogo entre arranques actualiza `public.country` pero no borra filas que ya no estén en el archivo (FR-009 no pide borrado).
- No se comprueban columnas del esquema al arrancar, solo que existan las tablas.
