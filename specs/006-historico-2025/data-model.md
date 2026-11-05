# Modelo de datos: Histórico 2025

Esta feature **no crea ni cambia tablas**: escribe en `live.current_event`, `live.event_version`, `live.quarantine` y `public.date_dim` tal como están en `sql/001_schema.sql` y `db-schema.md` (que no se tocan). Define lo que el contrato no cubre: el manifiesto en disco, las estructuras en memoria y la correspondencia con las columnas. Las firmas son de diseño; el código lo escriben las tareas.

## 1. Archivos en `data/historical/`

| Archivo | Contenido |
|---|---|
| `usgs_2025-MM.geojson` (MM = 01…12) | `FeatureCollection` crudo de USGS para el mes (si se dividió, los trozos concatenados) |
| `usgs_gap_<start>_<end>.geojson` | Igual, para un hueco (B12); `<start>`/`<end>` = `AAAAMMDDThhmmss` UTC |
| `manifest.json` | Procedencia (sección 2) |
| `checksums.sha256` | Una línea `sha256  archivo` por archivo (solo si los `.geojson` no se versionan, FR-019) |

## 2. `manifest.json`

```text
{
  "version": 1,
  "year": 2025,
  "parameters": { "minmagnitude": 4, "eventtype": "earthquake", "orderby": "time-asc", "format": "geojson" },
  "files": [
    {
      "name": "usgs_2025-01.geojson",
      "sha256": "<hex 64>",
      "records": <int>,                       // features del archivo
      "extracted_at": "AAAA-MM-DDThh:mm:ssZ", // de la primera consulta
      "queries": [
        { "url": "<URL completa>", "start": "...", "end": "...", "usgs_count": <int>, "records": <int> }
      ]
    }
  ],
  "gaps": [ { ...misma forma que un file... } ],
  "totals": { "records": <int>, "duplicates_discarded": <int>, "unique": <int>, "usgs_count_year": <int> }
}
```

Reglas: cada `queries[].records == usgs_count`; `files[].records == Σ queries[].records`; `totals.unique == totals.usgs_count_year`. `totals` se refiere a `files` (2025); los `gaps` no suman. Sin secretos ni rutas absolutas.

## 3. Estructuras en memoria (`historical/`)

| Estructura | Campos | Para qué |
|---|---|---|
| `Interval` | `start`, `end` (`datetime` UTC) | Un intervalo de consulta; `split()` da dos mitades contiguas |
| `QueryRecord` | `url`, `start`, `end`, `usgs_count`, `records` | Una consulta ya hecha |
| `FileRecord` | `name`, `sha256`, `records`, `extracted_at`, `queries` | Un archivo del manifiesto |
| `Manifest` | `files`, `gaps`, `totals`, parámetros | Procedencia completa |
| `DedupResult` | `features` (únicas), `discarded` (int) | Salida de `dedup_features` |
| `LoadSummary` | `unique`, `new_event`, `newer_version`, `unchanged`, `quarantined`, `by_file` | Resumen del cargador (FR-013) |

Funciones puras: `month_intervals(year)`, `split_interval(interval)`, `build_query_url(interval, base, kind)`, `dedup_features(feature_lists)`, `build_message_bytes(feature, extracted_at)` (arma el mensaje del contrato; serialización fija), `sha256_of(bytes)`.
E/S: `download_year(...)`, `download_gap(...)`, `read_manifest/write_manifest`, `load_historical(pool, manifest_dir, ...)`, `verify_load(pool, unique_ids, ...)`.

## 4. Mensaje construido por el cargador (contrato `kafka-message.md` §3, sin Kafka)

| Campo | Valor |
|---|---|
| `source` | `usgs_historical` |
| `mode` | `live` |
| `ingested_at` | `extracted_at` del archivo (UTC, sufijo `Z`) |
| `replay_at` | `null` |
| `is_synthetic` | `false` (las pruebas usan `true` con ids `synthetic-…`) |
| `event` | la feature tal cual está en el archivo |

Se entrega a `process_record` como `RawRecord(topic="earthquakes.live", partition=None, offset=None, key=None, value=<bytes>)`.

## 5. Correspondencia con las tablas

| Columna | Valor en la carga histórica |
|---|---|
| `current_event.source` / `event_version.source` | `usgs_historical` |
| `current_event.ingested_at` | fecha de extracción del archivo |
| `current_event.replay_at` | `NULL` |
| `current_event.is_synthetic` | `false` |
| `country_id` | geometría (`common/geo.py`), `NULL` sin polígono |
| `event_version.original` | feature íntegra |
| `event_version.received_at`, `quarantine.received_at` | reloj del cargador |
| `kafka_topic`, `kafka_partition`, `kafka_offset` (versión y cuarentena) | `NULL` |
| `quarantine.original_sha256` | sha256 de los bytes del mensaje construido |

## 6. Consultas de verificación (viven en `consumer/queries.py`)

- Eventos cargados del conjunto `U`: `SELECT count(*) FROM live.current_event WHERE event_id = ANY($1)`.
- Cuarentena del conjunto: `SELECT count(DISTINCT event_id) FROM live.quarantine WHERE event_id = ANY($1)`.
- Histórico sobre base limpia: `SELECT count(*) FROM live.current_event WHERE source = 'usgs_historical'`.
- Huella para «0 diferencias»: recuento y `md5(string_agg(... ORDER BY ...))` de `current_event`, `event_version` y `quarantine` (sin `id` identidad de cuarentena).

## 7. Registros de log

- Descarga: `query interval=… usgs_count=… records=…` por consulta; `file name=… records=… sha256=…`; `dedup duplicates=… unique=… usgs_count_year=…`.
- Carga: `historical_load file=… events=…`; resumen final `historical_summary unique=… new=… newer=… unchanged=… quarantined=… ok=true|false`.
