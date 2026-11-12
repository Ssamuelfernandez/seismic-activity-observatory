# Verificación bloque 3 (T084-T087), mediciones-costes

Pruebas: `pytest -m "not integration"` en venv: 832 passed, 227 deselected. Servicio `tests`, `tests/integration/test_bench_*.py` (ops, run, schema, storage, transfer): 17 passed, 0 skipped.

| Tarea | Veredicto | Prueba ejecutada |
|---|---|---|
| T084 | VERIFICADA | `almacenamiento.md`: tablas reales con filas, total, índices y bytes/fila, tamaño de `data/`, volumen Docker «no disponible»; `test_bench_storage` pasa |
| T085 | VERIFICADA | `transferencia.md`: bytes medidos de 4 rutas (HTTP 200); visitas «PENDIENTE (alumno)», volumen «no calculable»; `test_bench_transfer` pasa |
| T086 | VERIFICADA | `costes.md`: 6 categorías con etiqueta y fórmula; todo sin dato = PENDIENTE (alumno) / «no calculable»; fila de cuotas con «cuota gratuita ≠ coste cero». Solo hay 2 cifras MEDIDAS (GiB, GiB por visita) |
| T087 | VERIFICADA | `resultados.json` tiene 102 mediciones: a (17), b (5) y c/E6 (12) por cada tamaño 1.000/10.000/100.000. Las 102 medianas coinciden con `tablas.md` (script propio, 0 discrepancias). N real 15 (15) y mediana, Q1-Q3, IQR y mín-máx con unidades ms/KiB. Etiqueta SINTÉTICO. 0 celdas vacías (usa «no aplica»). 60 planes EXPLAIN (24 search + 36 agg), uno por consulta de Postgres. `equipo.md` leído de la máquina, con anfitrión y potencia «PENDIENTE (alumno)». |

Aislamiento, comprobado por mí en la base real: `to_regnamespace('bench')` es NULL; `usgs_historical` = 18302; `replay.current_event` 22 y `replay.event_version` 24, iguales antes y después (`T087_corrida.txt`, `aislamiento.md`); 0 filas de bench en live, replay, quarantine y exclusion. Corrida completa con código 0, ~117 s; `docker compose config --services` anotado (5 servicios).

Diff: `compose.yaml` solo añade el montaje `./docs/evidencias/mediciones:/app/evidence-mediciones` en `tests`. Sin cambios en contratos, `sql/`, `pyproject.toml`, `uv.lock` ni `docs/enunciado`. Los módulos de `scripts/benchmarks` tienen ≤216 líneas; no hay secretos (solo nombres de variables de entorno) ni atribución a Claude. `docs/evidencias/mediciones` pesa 492 KB.

Hallazgos bloqueantes o importantes: ninguno.
Límites conocidos: la máquina medida es la VM de Docker, no el anfitrión. El límite de CPU/memoria del contenedor es «no disponible». La corrida de 100.000 usó el presupuesto sin recortar N (15 de 15).
