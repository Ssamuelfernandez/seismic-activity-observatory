# Plan de implementación: Histórico 2025

**Rama**: `006-historico-2025` | **Spec**: [spec.md](spec.md) | **Cubre**: B13–B18 y el procedimiento de hueco >24 h (B12).

Solo diseño: este plan no contiene código de aplicación, Dockerfile ni compose (constitución §19). La implementación espera a la revisión del alumno.

## 1. Resumen

Dos programas pequeños en un paquete nuevo `historical/`: (1) un **descargador** que trae 2025 de USGS por meses (con `count`, división >20000, reintentos, dedup, manifiesto y sha256) o un intervalo `--start/--end` para recuperar un hueco; (2) un **cargador** que lee los archivos verificados con el manifiesto y llama a `consumer.pipeline.process_record` para cada evento, con `source=usgs_historical`, sin referencia Kafka. El procesamiento no se duplica (research D1). Detalle en [research.md](research.md) y [data-model.md](data-model.md).

## 2. Contexto técnico

- **Lenguaje**: Python 3.12 (ya fijado). **Dependencias nuevas**: ninguna (HTTP con `producer/usgs_client.py`, JSON y `hashlib` de la biblioteca estándar).
- **Almacenamiento**: PostgreSQL 16 sin cambios de DDL ni roles; el cargador usa el rol `observatory_consumer`.
- **Cambio en código compartido**: `common/records.py`, `common/transform.py`, `common/quarantine_row.py` y dos formatos de log para admitir referencia Kafka `None` (research D1). Comportamiento con referencia real intacto.
- **Pruebas**: unitarias sin red ni base (funciones puras, descargador con USGS simulado); integración con base temporal (servicio `tests`) con fixtures sintéticos `synthetic-…`; la descarga y carga reales de 2025 en un bloque propio.
- **Rendimiento**: ~16 000 eventos; `process_record` evento a evento (una transacción por evento, como en vivo). No es un objetivo optimizar.
- **Restricciones**: `kafka-message.md`, `db-schema.md`, `sql/001_schema.sql` y `docs/enunciado/` sin tocar (SC-009); sin variables de entorno nuevas ni cambios en `compose.yaml`; sin secretos.

## 3. Revisión contra la constitución

| Principio | Cumple | Cómo |
|---|---|---|
| §1 Idempotencia | Sí | Recarga sin diferencias por las restricciones únicas ya existentes (D8); prueba x3 |
| §2 Versionado por `updated` | Sí | Dedup conserva el mayor; la base nunca retrocede una versión (D2, D6) |
| §3 Tiempos | Sí | Mismo `build_event_rows`; el `event` va sin tocar |
| §4 País por geometría | Sí | Mismo localizador de `geografia-pais` |
| §5 Nulos y negativos | Sí | Misma validación; casos sintéticos en T016 |
| §6 Cuarentena | Sí | Sin motivos nuevos; el evento inválido no detiene la carga |
| §7 Sintéticos separados | Sí | Fixtures `synthetic-…` con `is_synthetic=true`; los datos reales, `false` |
| §8 Agregaciones desde estado actual | Sí | Verificación por SQL sobre `current_event` (D7) |
| §9, §10 Servicios y secretos | Sí | La carga usa el servicio `consumer` de Compose; contraseña del `.env`; nada en Git |
| §11 Versiones fijadas | Sí | Sin dependencias nuevas |
| §12 Alcance cerrado | Sí | Sin replay, API, frontend, reconciliación (B11) ni Kafka para el histórico |
| §13 Idioma | Sí | Identificadores en inglés; docstrings y docs en español |
| §14 Una responsabilidad; lo puro separado | Sí | Intervalos, dedup, manifiesto y mensaje puros; E/S aparte; SQL en `consumer/queries.py` |
| §15 Contratos únicos | Sí | No se duplican ni modifican; se citan |
| §16 Cierre | Prevista | T022–T025 |
| §19 Una feature cada vez | Sí | Este plan no contiene código |

Sin violaciones; la tabla de complejidad no hace falta.

## 4. Estructura (rutas que se tocan)

```text
historical/__init__.py
historical/intervals.py       NUEVO  Interval, month_intervals, split_interval, build_query_url (puro)
historical/dedup.py           NUEVO  dedup_features (puro)
historical/manifest.py        NUEVO  estructuras, sha256_of, read/write atómico, verify_file
historical/envelope.py        NUEVO  build_message_bytes (puro): mensaje del contrato
historical/fetch_interval.py  NUEVO  count + descarga + división recursiva + reintentos (E/S inyectable)
historical/download.py        NUEVO  download_year, download_gap: reutiliza archivos por sha, totales, comprobación del count
historical/download_main.py   NUEVO  CLI: configura y arranca (--force, --start, --end)
historical/loader.py          NUEVO  load_historical: lee manifiesto, verifica sha, dedup, process_record
historical/verify.py          NUEVO  verify_load(pool, unique_ids, quarantined_ids): fórmula únicos − cuarentena (Q sale de los resultados de process_record, no de leer live.quarantine); huella de «0 diferencias»
historical/load_main.py       NUEVO  CLI: pool, esquema, catálogo, carga, verificación, código de salida
common/records.py             MessageRef admite None; kafka_columns(ref)
common/transform.py, common/quarantine_row.py   usan kafka_columns
consumer/pipeline.py, consumer/resilience.py    formatos de log %d -> %s
consumer/queries.py           consultas de verificación (data-model §6)
Dockerfile                    COPY historical ./historical (única línea nueva)
.gitignore                    solo si los archivos superan ~50 MB (T019)
tests/historical/, tests/integration/test_historical*.py, tests/support/ (doble de USGS y fixtures sintéticos)
data/historical/, docs/evidencias/historico-2025/, docs/borradores/historico-2025.md, README.md, CODEMAP.md
```

Cada archivo respeta 250 líneas y funciones de ~30 (CC-14 de `003`).

## 5. Flujo

```text
Descarga:  meses UTC -> count -> (¿>20000? dividir) -> GET -> comprobar registros == count
           -> escribir usgs_2025-MM.geojson -> sha256 -> manifest.json
           -> dedup entre archivos -> total único == count anual (si no: error, código != 0)
Carga:     manifest.json -> verificar sha256 -> dedup -> por evento: build_message_bytes
           -> process_record(RawRecord topic=live, partition=None) -> cuarentena o current_event/event_version
           -> resumen + verify_load (|U| - |Q| == eventos en BD)
```

## 6. Pregunta 3 y reparto de riesgos

- Versionado de archivos: regla de FR-019, decidida en T019 con el tamaño real.
- Riesgo principal: que `count` de USGS no coincida con la descarga (revisión intermedia). Se trata como error reintentable, no se corrige en silencio.
- Segundo riesgo: el cambio de `MessageRef` toque algo de 003–005. Se acota con T010 (suite completa antes y después).
