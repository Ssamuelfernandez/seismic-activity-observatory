# Investigación: Histórico 2025

Decisiones de diseño con su motivo. D1 resuelve la pregunta 2 de la spec; D2 aplica la decisión provisional de la pregunta 1; D13 aplica la de la pregunta 3. Si el alumno cambia alguna, se revisa aquí.

## D1. Cómo se reutiliza el procesamiento (pregunta 2)

- **Hallazgo**: `common.processing.process_event()` del roadmap no existe. La canalización real es `consumer/pipeline.py::process_record(RawRecord, PipelineDeps)`: decodifica, valida (`validate_message`), asigna país (`deps.locate`), construye filas (`build_event_rows`), escribe con reintento (`writer.write_event`) o manda a cuarentena (`build_quarantine_row`, `writer.write_quarantine`). No importa `aiokafka` (solo `asyncpg`), así que se puede llamar desde un proceso sin Kafka.
- **Decisión**: el cargador llama a **`process_record` tal cual**, con un `RawRecord` cuyo `value` son los bytes de un mensaje con el formato del contrato (`source=usgs_historical`, `mode=live`, `ingested_at` = fecha de extracción, `replay_at=null`, `is_synthetic=false`, `event` = la feature sin tocar). Las dependencias son las mismas: `bind_pool_writers(pool)`, `RetryControl`, el localizador de `catalog_loader.load_country_catalog`. No se crea una segunda función de procesamiento ni se copia `validate_message` ni `build_event_rows` (B16, constitución §14).
- **Único cambio en código compartido**: hoy `MessageRef(topic, partition, offset)` se copia siempre a `kafka_topic/partition/offset`. El contrato admite `NULL` en la carga por lote (`db-schema.md` §3.2 y §3.5). Cambio mínimo:
  1. `MessageRef.partition` y `.offset` admiten `None`. `None` significa «carga por lote, sin referencia Kafka». El `topic` del `RawRecord` sigue siendo `earthquakes.live`, porque `process_record` lo usa para derivar `mode=live` y el esquema `live` y para la comprobación `mode`↔tema.
  2. Una función pura `kafka_columns(ref) -> (topic, partition, offset)` en `common/records.py` devuelve `(None, None, None)` si `ref.partition is None`. La usan `common/transform.py::_build_version` y `common/quarantine_row.py::build_quarantine_row` en lugar de copiar `ref.*`.
  3. Los formatos de log que usan `%d` con partición/offset (`consumer/pipeline.py::_log_validation_gap`, `consumer/resilience.py` líneas de `retry`) pasan a `%s`; `QuarantineRow.kafka_topic` pasa a `str | None`. `consumer/reporting.py` y `commit_offset_with_retry` no se tocan: el cargador no los usa.
  Los tests de 003–005 siguen en verde porque el comportamiento con referencia Kafka real no cambia; se comprueba ejecutando toda la suite (T010).
- **Alternativas descartadas**: (a) publicar el histórico en Kafka: el contrato dice que va por lote; (b) escribir una función `process_batch_event` paralela: duplicaría la lógica (B16); (c) pasar `topic=None`: rompería `topic_mode` y la comprobación de modo.
- **Idempotencia del mensaje construido**: los bytes del mensaje se serializan siempre igual (`json.dumps` con separadores fijos y `ingested_at` tomado del manifiesto), de modo que `original_sha256` de la cuarentena es estable y `UNIQUE (original_sha256, reason)` evita duplicados al recargar.
- **Catálogo de países**: el cargador reutiliza `consumer.schema_check.ensure_schema_ready` y `consumer.catalog_loader.load_country_catalog` (upsert repetible; devuelve el índice). Esto es más simple y robusto que exigir que el consumidor haya arrancado antes; la suposición de la spec («si no está cargado, falla») se cumple igualmente si el archivo del catálogo falta.

## D2. Hueco de más de 24 h (B12, pregunta 1)

- **Decisión**: el descargador acepta `--start` y `--end` (UTC, `AAAA-MM-DDThh:mm:ss`). Con ellos no descarga 2025: pide ese intervalo con los mismos parámetros y las mismas reglas (`count`, división >20000, reintentos), guarda `data/historical/usgs_gap_<start>_<end>.geojson` y lo añade a la lista `gaps` del manifiesto. Las comprobaciones de totales de 2025 no cambian (los huecos no entran en el `count` anual); cada hueco se contrasta con su propio `count`.
- **Cargador**: carga todos los archivos del manifiesto (`files` y `gaps`), deduplica entre ellos y aplica las reglas de versión de la base. Un evento del hueco que ya está en la base con el mismo `updated` no cambia nada; uno con `updated` menor no retrocede (constitución §2).
- **Límite conocido**: si un evento del hueco ya existía con `source=usgs_feed` y el hueco trae un `updated` estrictamente mayor, la fila actual pasa a `source=usgs_historical` (es la versión más reciente conocida). Es coherente con el contrato.
- **Procedimiento (se documenta en README y borrador)**: (1) averiguar el intervalo sin datos (último `ingest_run` correcto y reanudación del productor); (2) `download --start … --end …`; (3) cargar; (4) comprobar el resumen. Solo hace falta desde USGS cuando el hueco supera lo que cubre el feed reciente (24 h).

## D3. Dónde se escribe y qué se versiona

- Archivos en `data/historical/` (no `data/raw/`, ignorado por Git). Versionados si los 12 archivos + manifiesto < ~50 MB, medido tras T019 (pregunta 3); si no, `.gitignore` de `data/historical/*.geojson` y se versionan script, `manifest.json` y `checksums.sha256`.
- Estimación: ~16 000 eventos a ~1 KB cada uno = ~16 MB. Se decide con el dato real, no con la estimación.

## D4. Manifiesto

`data/historical/manifest.json` (estructura en `data-model.md`): por archivo, lista de consultas (URL completa con parámetros, `count` de USGS, registros devueltos, fecha de extracción UTC), registros del archivo y sha256; en total, duplicados descartados, únicos y `count` anual. El sha256 es del archivo en disco (respuesta cruda). Se escribe de forma atómica (archivo temporal + `rename`) para no dejar un manifiesto a medias.

## D5. Cómo se forma un archivo mensual

- Meses naturales UTC: `starttime = AAAA-MM-01T00:00:00`, `endtime` = primer instante del mes siguiente. USGS trata `endtime` como exclusivo en la práctica, pero no se confía en ello: si un evento aparece en dos consultas, la deduplicación lo resuelve (B14).
- Antes de descargar: `count` del intervalo. Si `count <= 20000`, una consulta. Si no, se parte por el punto medio temporal en dos intervalos contiguos y se aplica la misma regla a cada uno (recursivo). Los trozos se fusionan en un único `FeatureCollection` por mes (`features` concatenadas en el orden de las consultas; `metadata` del primer trozo); el archivo conserva su nombre.
- Verificación por consulta: registros devueltos == `count` de esa consulta. Si no, error (nunca se trunca en silencio).
- Límite conocido: muchos eventos con el mismo milisegundo no se pueden separar por tiempo; con M>=4 mundial no ocurre (~1300 eventos/mes). Si un intervalo de 1 ms superara 20000, se termina con error que lo dice.

## D6. Deduplicación (B14)

`dedup_features(lists)` es pura: recorre las features de todos los archivos en el orden del manifiesto, agrupa por `id` y conserva la de `properties.updated` mayor; con `updated` igual, la primera. Devuelve las únicas y el nº de descartadas. Features sin `id` o con `updated` no entero no se agrupan: pasan tal cual y la validación las manda a cuarentena (`missing_id`, `missing_updated`), así no se pierden ni se ocultan. Comprobación: nº de `id` distintos de las únicas con `id` == nº de únicas con `id`. El cargador aplica la misma función; no depende de que el descargador la haya ejecutado.

## D7. Verificación de conteos

Descarga: Σ registros únicos de los 12 meses == `count` de USGS para todo 2025 (consulta aparte); si no, error con código ≠ 0 y las dos cifras. Carga: con `U` = conjunto de `id` únicos de los archivos y `Q` = `id` de los eventos que `process_record` mandó a cuarentena en esa misma carga (el rol `observatory_consumer` solo tiene INSERT en `live.quarantine`, así que no se lee de la tabla), se exige `count(live.current_event WHERE event_id = ANY(U)) == |U| − |Q|` y, sobre base limpia, `count(source='usgs_historical') == |U| − |Q|`. La verificación se calcula con SQL sobre el estado actual (constitución §8). Si hay features sin `id`, van a cuarentena y no entran en `U`.

## D8. Idempotencia de la recarga

Se apoya en lo que ya garantiza `003`: `event_version` con `ON CONFLICT (event_id, updated_ms) DO NOTHING`, `current_event` con upsert condicional por `updated_ms` estrictamente mayor y cuarentena con `UNIQUE (original_sha256, reason)`. La prueba compara, antes y después de recargar, el recuento y un hash agregado (`md5(string_agg(...))`) de `current_event`, `event_version` (menos `received_at`, que no cambia porque el conflicto no actualiza) y `quarantine`. El resumen del cargador cuenta resultados por `VersionOutcome`; en una recarga todo es `redelivery_ignored`.

## D9. `ingested_at` y `received_at`

`ingested_at` = fecha de extracción de la **primera consulta** del archivo (manifiesto), formateada `AAAA-MM-DDThh:mm:ssZ` (B18). `received_at` (versión y cuarentena) = reloj del cargador, como en vivo.

## D10. Lote frente a Kafka (B16, texto para el borrador)

Se elige lote porque: el contrato lo fija (`kafka-message.md` §1, `db-schema.md` §1); son ~16 000 eventos de una vez, que superan con sentido la ventana de retención de 7 días y el ritmo del feed; no hay requisito de tiempo real; y se reutiliza la misma lógica (`process_record`), así que las reglas son idénticas. Coste: no se ejerce el camino Kafka, pero la prueba de aceptación del cargador usa la misma función que el consumidor.

## D11. Cómo se ejecuta (sin tocar `compose.yaml`)

- **Descarga**: solo usa la biblioteca estándar y `producer/usgs_client.py`; se ejecuta en el equipo con `uv run python -m historical.download_main` (la red es de USGS; no hay base). Equivalente en contenedor: `docker compose run --rm --no-deps -v ./data/historical:/app/data/historical producer python -m historical.download_main`.
- **Carga**: necesita la base por nombre de servicio (constitución §9): `docker compose run --rm --no-deps -v ./data/historical:/app/data/historical:ro consumer python -m historical.load_main`. Reutiliza el servicio `consumer` (rol `observatory_consumer`, `DB_PASSWORD` desde `.env`, `COUNTRY_CATALOG_PATH` ya montado). Requiere `COPY historical ./historical` en el `Dockerfile` (T013); no se añade servicio ni variable nueva al `compose.yaml`. `data/` está en `.dockerignore`, por eso la carpeta entra por el `-v`.
- Comprobación pendiente de la tarea: que `-v ./ruta` relativo funcione en Git Bash/PowerShell de este equipo; si no, se usa la ruta absoluta en el README.

## D12. Reintentos de la descarga (FR-007)

Se reutiliza `producer/usgs_client.fetch_feed` (timeout, 429/5xx → `FeedFetchError`) y `common/backoff.compute_backoff_seconds` con un máximo de intentos (5, constante con nombre). Al agotarlos: error que nombra el mes; los archivos ya buenos se conservan y el manifiesto se actualiza tras cada mes terminado, de modo que la siguiente ejecución reanuda.

## D13. Tamaño de archivos (pregunta 3)

Se mide en T019. Regla de FR-019. El README dice en cada caso si el clon necesita ejecutar la descarga.

## Límites conocidos (una línea cada uno)

- Instantánea a la fecha de extracción: no se reconcilian revisiones posteriores (B11, B18).
- País con el catálogo simplificado `ne_110m` (límite de `geografia-pais`).
- USGS puede publicar una revisión entre `count` y descarga: el error pide repetir.
- Sin fuzz de archivos corruptos más allá de sha256 distinto/ausente.
- Evidencia TDD «falla antes» solo en T010–T011 y parcial en los bloques 1–2.
- La carrera entre `count` y descarga se resuelve repitiendo la descarga.
- La cuarentena de la carga no se contrasta de forma independiente en BD por falta de permiso SELECT de `observatory_consumer`.
