# Plan de implementación: mediciones-costes (011)

**Rama**: `011-mediciones-costes` | **Fecha**: 2026-11-13 | **Spec**: `specs/011-mediciones-costes/spec.md`
**Requisitos**: K1 a K7 y E6 (K8 y ROI fuera de alcance).

Solo documentos de diseño (constitución §19). Los contratos de `specs/001-contratos-y-modelo/contracts/` (`db-schema.md` §3.3 y §4) se citan, no se copian ni se modifican. Es trabajo de clase: se corrige lo que haga fallar un requisito obligatorio, contradiga un contrato o la constitución, pierda datos reales o deje una decisión inexplicable; lo demás es un límite conocido de una línea. Las 6 decisiones de «Preguntas para el alumno» de la spec están **adoptadas como provisionales** (marcadas «(prov. n)» abajo) y el alumno las confirma en la revisión.

## Resumen

Un CLI en `scripts/benchmarks/` que, desde el servicio `tests` (administrador de la base), crea el esquema temporal `bench` con datos SINTÉTICOS derivados de los 18.302 eventos reales de 2025, mide tres operaciones (búsqueda por id, integración geográfica, agregación por ventanas más las consultas de E6) con tres tamaños (1.000, 10.000, 100.000), lee tamaños y transferencia reales, calcula la tabla de costes con campos «PENDIENTE (alumno)» y guarda todo en `docs/evidencias/mediciones/`. El razonamiento a 100 M y las propuestas (K7) se redactan **después** de medir, citando identificadores de medición. El borrador del README §7 va a `docs/borradores/mediciones-costes.md`.

Sin cambios de contrato, de `sql/001_schema.sql`, de `pyproject.toml`/`uv.lock` (prov. 2) ni de servicios de Compose; la única modificación de `compose.yaml` es un montaje de escritura de `docs/evidencias/mediciones` en el servicio `tests` (prov. 1). Decisiones y alternativas: `research.md` (D1 a D11).

## Technical Context

| Pieza | Valor |
|---|---|
| Lenguaje | Python 3.12.16, solo lo ya fijado: `asyncpg` (base), `shapely` (vía `common/geo.py`), `httpx` (transferencia) y biblioteca estándar (`time.perf_counter`, `tracemalloc`, `statistics`, `platform`, `os`, `/proc`); **sin dependencias nuevas** (prov. 2) |
| Almacenamiento | Esquema temporal `bench` en la base del stack (prov. 3); resultados en `docs/evidencias/mediciones/` |
| Ejecución | `docker compose --profile test run --rm tests python -m scripts.benchmarks.run_benchmarks …` con el stack levantado y sin pararlo (prov. 1 y 5) |
| Pruebas | `pytest` sin Docker para lo puro (estadísticos, generador, costes, tablas, análisis estático de SQL); `pytest -m integration` en el servicio `tests` para el ciclo de vida de `bench` |
| Tamaños | 1.000, 10.000, 100.000 (fijos por la spec) |
| Restricciones | Una feature cada vez; archivos de 250 líneas máx., funciones de ~30; docstrings de `03 §7.4`; identificadores en inglés; lógica pura separada del I/O; sin psutil |

## Constitución (comprobación)

| Principio | Cumple | Cómo |
|---|---|---|
| §4 País por geometría | Sí | El método con `STRtree` usa `common/geo.py`; el bucle ingenuo es solo línea base y aplica la misma regla (D4) |
| §7 Sintéticos separados | Sí | Esquema `bench` temporal, filas `is_synthetic = true` e id `synthetic-bench-`, comprobación final y etiqueta SINTÉTICO en toda cifra derivada |
| §9 Nombres de servicio | Sí | Se ejecuta en la red de Compose: `DB_HOST` y `api:8000`, nunca `localhost` |
| §10 Secretos | Sí | Las credenciales vienen del entorno del servicio `tests`; no se escriben en evidencias (el JSON no las guarda) |
| §11 Versiones fijadas | Sí | Sin dependencias nuevas (prov. 2) |
| §12 Alcance cerrado | Sí | Sin ROI, Spark, Flink, Kubernetes ni ML; las propuestas se limitan a PostgreSQL, Kafka y Python |
| §13 Idioma | Sí | Identificadores en inglés, documentación en español |
| §14 Una responsabilidad | Sí | Módulos puros (`stats`, `synth`, `costs`, `report`) separados de los de I/O (`bench_schema`, `seed`, `hardware`, `storage`, `transfer`, `op_*`) |
| §15 Contratos únicos | Sí | La estructura de `bench` sale de `LIKE live.current_event` y los índices de `pg_indexes`; no se copia el DDL |
| §16 Cierre | Sí | Pruebas ejecutadas, evidencias, borrador del README y `CODEMAP.md` (T093) |
| §17 Frontend | Sí | No se toca |
| §18 Enunciado | Sí | No se toca |
| §19 Una feature cada vez | Sí | Implementar solo tras la revisión del alumno |
| §20 Commits | Sí | Sin commits ni trailers |
| §21 Sin predicción | Sí | La extrapolación a 100 M se redacta como cálculo SUPUESTO con fórmula |

Resultado del gate: sin violaciones. Se repite tras el diseño: igual.

## Estructura (diseño)

Ubicación decidida por `CODEMAP.md`: `scripts/` aloja los CLI de verificación y el servicio `tests` ya lo monta en solo lectura; así no se toca la imagen (el `Dockerfile` no copia `scripts/`).

| Archivo (nuevo) | Responsabilidad | Pureza |
|---|---|---|
| `scripts/benchmarks/stats.py` | mediana, rango intercuartílico, mínimo, máximo; `plan_repetitions` (D6) | puro |
| `scripts/benchmarks/measure.py` | repite una función con calentamiento, `perf_counter` y pico de `tracemalloc`; devuelve la serie | I/O mínimo (reloj) |
| `scripts/benchmarks/hardware.py` | lee CPU, núcleos, RAM, SO, límites del contenedor y versiones; funciones puras que parsean `/proc/cpuinfo` y `/proc/meminfo` | I/O + puro |
| `scripts/benchmarks/seed.py` | lee `data/historical/`, verifica 13 sha256 con `historical/manifest.py` y deduplica con `historical/dedup.py` | I/O |
| `scripts/benchmarks/synth.py` | filas sintéticas deterministas (submuestra o replicación) con coherencia de tiempos | puro |
| `scripts/benchmarks/bench_schema.py` | crea, limpia y verifica `bench` (lista cerrada de SQL, guardas) | I/O |
| `scripts/benchmarks/bench_load.py` | carga con `COPY`, `ANALYZE`, índices desde `pg_indexes`, `EXPLAIN` | I/O |
| `scripts/benchmarks/op_search.py` | operación a: lista, `dict`, Postgres sin/con índice | I/O + puro |
| `scripts/benchmarks/op_geo.py` | operación b: bucle ingenuo y `STRtree` | puro + reloj |
| `scripts/benchmarks/op_agg.py` | operación c y E6: Q4, Q3, Q2 sin/con índice | I/O |
| `scripts/benchmarks/verdicts.py` | veredicto por índice a partir de planes y tiempos (D8) | puro |
| `scripts/benchmarks/storage.py`, `transfer.py` | tamaños (`pg_total_relation_size`, archivos) y bytes de respuestas de la API | I/O |
| `scripts/benchmarks/costs.py` | filas de coste MEDIDO/SUPUESTO con «PENDIENTE (alumno)» | puro |
| `scripts/benchmarks/report.py` | tablas Markdown y JSON de resultados | puro |
| `scripts/benchmarks/run_benchmarks.py` | CLI: `--sizes`, `--repeats`, `--budget`, `--clean`, `--yes`; solo orquesta | I/O |

Pruebas en `tests/scripts/` (`test_bench_stats.py`, `test_bench_measure.py`, `test_bench_hardware.py`, `test_bench_synth.py`, `test_bench_seed.py`, `test_bench_sql_static.py`, `test_bench_verdicts.py`, `test_bench_costs.py`, `test_bench_report.py`, `test_bench_ops_pure.py`) y `tests/integration/test_bench_schema.py`.

### Lo que cambia fuera de `scripts/benchmarks/`

| Archivo | Cambio | Tarea |
|---|---|---|
| `compose.yaml` (servicio `tests`) | montaje `./docs/evidencias/mediciones:/app/evidence-mediciones` de escritura; ningún servicio nuevo | T087 |
| `README.md` | enlace al borrador y una línea de estado | T092 |
| `CODEMAP.md` | filas de los módulos y de las evidencias | T093 |
| `docs/borradores/mediciones-costes.md` | borrador de §7 de la memoria | T092 |

### Lo que NO cambia

Contratos, `sql/001_schema.sql`, `docs/enunciado/`, constitución, `pyproject.toml` y `uv.lock`, `Dockerfile`, el checklist, las specs cerradas, ningún servicio de Compose, `docs/memoria.md`.

## Flujo de la ejecución

```
tests (admin) -> run_benchmarks
  1. hardware.py -> equipo.md ; seed.py (13 sha256, dedup -> 18.302)
  2. guardas: stack accesible, `bench` no existe (o --clean con marca); recuentos iniciales (replay.*, usgs_historical)
  3. bench_schema: CREATE SCHEMA bench + COMMENT marca SINTÉTICO
  4. por tamaño N: synth -> COPY bench.event_N -> ANALYZE -> op_search / op_geo / op_agg (sin índice, con un índice cada vez, ANALYZE tras cada cambio)
  5. lecturas reales (rol observatory_api, solo lectura): pg_indexes, idx_scan, tamaños, recuentos ; transfer.py (API por nombre de servicio)
  6. finally: DROP SCHEMA bench CASCADE ; verificación final (FR-017)
  7. report.py -> docs/evidencias/mediciones/ (JSON, tablas, planes, equipo.md, costes.md)
```

## Cierre

T093: pruebas unitarias y de integración ejecutadas, evidencia, `CODEMAP.md` y README. Después, detenerse y esperar revisión (constitución §19); `docs/memoria.md` y el checklist los edita el alumno.
