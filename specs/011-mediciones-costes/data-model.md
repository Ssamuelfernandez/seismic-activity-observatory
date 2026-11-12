# Modelo de datos: mediciones-costes (011)

No hay tablas permanentes nuevas ni cambios de `sql/001_schema.sql`. Esta feature define (1) tablas temporales SINTÉTICAS en `bench`, (2) la forma de los resultados en `docs/evidencias/mediciones/` y (3) las filas de coste. Los contratos (`db-schema.md` §3.3 y §4) se citan, no se copian.

## 1. Esquema temporal `bench` (SINTÉTICO)

| Elemento | Definición |
|---|---|
| Esquema | `bench`, creado por el administrador al empezar y eliminado con `DROP SCHEMA bench CASCADE` al terminar |
| Marca | `COMMENT ON SCHEMA bench IS 'SINTETICO-BENCH-TEMPORAL: datos sinteticos de mediciones-costes'`; `--clean` solo elimina un `bench` que lleve esta marca |
| Tablas | `bench.event_1000`, `bench.event_10000`, `bench.event_100000`: `CREATE TABLE … (LIKE live.current_event INCLUDING DEFAULTS)` (sin `CHECK` ni índices, ver `research.md` D5) |
| Índices | los 4 de `pg_indexes` de `live.current_event` (clave primaria, `ix_current_event_time`, `ix_current_event_country_time`, `ix_current_event_mag`) con la definición leída y reescrita; uno cada vez, creado y borrado durante la medición |

### Reglas de las filas (validadas por pruebas de `synth.py`)

| Campo | Regla |
|---|---|
| `event_id` | `synthetic-bench-<n>`, único |
| `source` | `synthetic_bench` (distinto de los orígenes reales) |
| `is_synthetic` | `true` en el 100 % de las filas |
| `event_time_ms`, `event_time` | ms dentro de 2025; `event_time = epoch + ms` |
| `updated_ms`, `updated_at` | `updated_ms >= event_time_ms`; `updated_at` coherente con `updated_ms` |
| `date_id` | `(event_time AT TIME ZONE 'UTC')::date` |
| `lon`, `lat` | dentro de [-180, 180] y [-90, 90] |
| `mag`, `depth_km` | dentro de [-10, 15] y [-100, 1000] (los nulos de la semilla se conservan como nulos, no se rellenan con 0; §5) |
| `country_id` | resultado de `assign_country` con el catálogo real, o `NULL` |

Siembra: los 18.302 eventos únicos de `data/historical/` (13 sha256 del manifiesto verificados, deduplicados con `historical/dedup.py`) con `random.Random(20251113)`.

## 2. Resultados (`docs/evidencias/mediciones/`)

### 2.1 `resultados.json`

```
{
  "etiqueta": "SINTETICO",
  "seed": 20251113, "run_at": "<UTC>", "params": {"sizes": [...], "repeats": 15, "budget_seconds": 90},
  "measurements": [ Measurement, ... ]
}
```

| Medición (`Measurement`) | Tipo | Notas |
|---|---|---|
| `id` | texto | `<op>.<strategy>.<size>.<case>`, p. ej. `search.dict.100000.absent`, `geo.naive.10000.ocean`, `agg.q4_time_index.100000.day`; es el identificador que citan las propuestas |
| `operation`, `strategy`, `size`, `case` | texto, texto, entero, texto | `size` ∈ {1000, 10000, 100000} |
| `samples_ms` | lista de reales | cada repetición, sin el calentamiento |
| `n_requested`, `n_real` | enteros | `n_real` ≥ 3 |
| `median_ms`, `q1_ms`, `q3_ms`, `iqr_ms`, `min_ms`, `max_ms` | reales | ms, base decimal |
| `peak_kib` | real o nulo | pico de `tracemalloc` en KiB (base 1024); nulo en las consultas de Postgres |
| `plan_ref` | ruta o nulo | `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` guardado en `planes/` |
| `server_ms`, `shared_hit`, `shared_read` | real/entero o nulos | del plan |
| `notes` | texto | p. ej. el planificador no usó el índice |

### 2.2 Otros archivos

| Archivo | Contenido | Requisito |
|---|---|---|
| `equipo.md` | CPU, núcleos físicos/lógicos, RAM, SO, versiones (Python, PostgreSQL, `shapely`), límites del contenedor; campos del anfitrión «PENDIENTE (alumno)» | K2, FR-010 |
| `tablas.md` | tablas por operación: unidades, N real, mediana, dispersión, memoria; todas con la etiqueta «SINTÉTICO» | K1, K2, K3 |
| `teoria_vs_observado.md` | coste medio, peor caso teórico y observado por operación; discrepancias explicadas | K1, FR-006 |
| `planes/*.json` | un plan por consulta de Postgres | E6, SC-001 |
| `indices.md` | por índice: definición leída, tamaño, `idx_scan` real, medición sin/con, veredicto (recomendación) | E6 |
| `aislamiento.md` | antes/después: `bench` inexistente, 0 filas de bench fuera, recuentos de `replay.*` y `usgs_historical` iguales | K4, FR-017 |
| `almacenamiento.md`, `transferencia.md` | tamaños y bytes por fila medidos; bytes de respuestas de la API | K6 |
| `costes.md` | seis filas de coste (MEDIDO/SUPUESTO) y nota de cuotas gratuitas | K6 |
| `escalado.md` | 100 M y propuestas K7 | K5, K7 |
| `procedimiento.md` | comandos, requisitos y tiempo estimado | FR-011 |
| `README.md` | índice y veredicto SC-001 a SC-007 | §16 |

## 3. Fila de coste (`CostRow`)

| Campo | Regla |
|---|---|
| `category` | una de: hardware, electricidad, almacenamiento, transferencia, mantenimiento, horas de desarrollo (exactamente 6) |
| `label` | `MEDIDO` o `SUPUESTO` |
| `formula` | texto con la fórmula |
| `inputs` | lista de (nombre, valor o `PENDIENTE (alumno)`, origen, unidad) |
| `result` | número con unidad, o `no calculable` si alguna entrada es `PENDIENTE` |

Transiciones: una entrada pasa de `PENDIENTE (alumno)` a valor solo por edición del alumno; el código no rellena por defecto.

## 4. Veredicto de índice y propuesta

| Entidad | Campos |
|---|---|
| Veredicto | índice, consulta, `justificado` / `no justificado con estos datos` / `no concluyente`, ids de medición citados, selectividad, tamaño del índice, `idx_scan` real |
| Propuesta (K7) | problema observado (id de medición + cifra) → mejora → medición que la confirmaría |
