# Modelo de datos: Geografía y país

Esta feature **no crea ni cambia tablas**: usa `public.country` y `live/replay.current_event.country_id` tal como están en `sql/001_schema.sql` y `db-schema.md` (que no se tocan). Este documento define lo que el contrato no cubre: estructuras en memoria, mapeo y registros de log.

## 1. Estructuras en memoria

`CountryRow` va en `common/records.py` (inmutable, como el resto). Las demás en `common/geo.py`. Las firmas son de diseño; el código lo escriben las tareas.

| Estructura | Campos | Para qué |
|---|---|---|
| `CountryRow` | `country_id`, `name_es`, `admin`, `continent`, `subregion` (todos `str`) | Fila de `public.country` |
| `CountryEntry` | `row: CountryRow`, `geometry` (Shapely `Polygon`/`MultiPolygon`) | Una entidad del catálogo parseada |
| `CountryCatalog` | `entries: tuple[CountryEntry, ...]` | Resultado de `parse_country_catalog`; garantiza `ADM0_A3` único |
| `CountryIndex` | árbol `STRtree`, geometrías y códigos alineados | Índice espacial construido una vez |
| `CountryMatch` | `country_id: str \| None`, `candidates: tuple[str, ...]` | Resultado de asignar un punto; `candidates` ordenados |
| `CatalogLoadResult` | `total`, `inserted`, `updated` (enteros) | Resultado de la carga en base (en `consumer/catalog_loader.py`) |

Funciones puras (`common/geo.py`):

- `parse_country_catalog(geojson: dict) -> CountryCatalog`: valida y mapea; lanza `CatalogError` (nombra código o campo y posición).
- `build_country_index(catalog: CountryCatalog) -> CountryIndex`.
- `assign_country(index: CountryIndex, lon: float, lat: float) -> CountryMatch`: sin E/S, determinista.

E/S (`consumer/`): `schema_check.ensure_schema_ready(pool)` (lanza `SchemaNotReadyError`) y `catalog_loader.load_country_catalog(pool, path) -> tuple[CountryIndex, CatalogLoadResult]`.

## 2. Mapeo catálogo -> `public.country`

| Propiedad del GeoJSON | Columna | Comprobación |
|---|---|---|
| `ADM0_A3` | `country_id` | presente, `^[A-Z]{3}$`, único (C10) |
| `NAME_ES` | `name_es` | presente, no vacía |
| `ADMIN` | `admin` | presente, no vacía |
| `CONTINENT` | `continent` | presente, no vacía |
| `SUBREGION` | `subregion` | presente, no vacía |
| geometría | (no se guarda) | `Polygon` o `MultiPolygon`, válida y no vacía |

El CRS del archivo es CRS84 (lon, lat); Shapely recibe `Point(lon, lat)`, sin reproyectar.

## 3. Regla de asignación

1. `punto = Point(lon, lat)`.
2. Candidatos = polígonos del índice con `punto covered_by polígono` (borde incluido).
3. Ningún candidato -> `country_id = None`.
4. Uno -> ese. Varios -> `min(ADM0_A3)`; el resultado lleva todos los candidatos para el log.

## 4. Escritura (sin cambios de SQL, salvo la columna)

- `queries.CURRENT_COLUMNS` incorpora `country_id` (después de `date_id`; el orden solo importa para los `$n`). El `DO UPDATE SET` ya asigna todas las columnas salvo `event_id`, así que `country_id` se sustituye cuando gana la versión nueva (también a `NULL`) y no cambia cuando la versión es antigua o repetida.
- `event_version` no tiene `country_id` (el contrato no lo prevé): sin cambio.
- `EventRows.current` incluye siempre la clave `country_id` (valor `None` si no hay país).

## 5. Registros de log nuevos (formato fijo)

| Línea | Nivel | Cuándo |
|---|---|---|
| `catalog loaded total=<n> inserted=<n> updated=<n>` | INFO | una vez por arranque, tras cargar |
| `country_tie event_id=<id> candidates=<A,B,…> chosen=<A>` | INFO | solo si hay más de un candidato |
| error de arranque: `SchemaNotReadyError: falta la tabla <esquema.tabla>` | ERROR (termina el proceso) | `to_regclass` devuelve `NULL` |
| error de arranque: `CatalogError: ADM0_A3 repetido '<XXX>' (entidades i y j)` / `falta el campo '<P>' en la entidad <i>` | ERROR (termina el proceso) | catálogo inválido |

No hay contadores nuevos ni motivos de cuarentena nuevos. Los recuentos "con país" y "sin país" salen de SQL sobre `current_event` (consulta de `quickstart.md`).

## 6. Consultas de comprobación (para la evidencia)

- Total, con país y sin país (la suma debe cuadrar): `SELECT count(*), count(country_id), count(*) - count(country_id) FROM live.current_event;`
- País de un evento sintético: `SELECT event_id, country_id, mag FROM live.current_event WHERE event_id LIKE 'synthetic-geo-%' ORDER BY event_id;`
- Catálogo: `SELECT count(*) FROM public.country;` (177).
- Cuarentena de la latitud 145: `SELECT event_id, reason, kafka_topic, kafka_partition, kafka_offset FROM live.quarantine WHERE event_id LIKE 'synthetic-geo-%';` (con el rol administrador).
