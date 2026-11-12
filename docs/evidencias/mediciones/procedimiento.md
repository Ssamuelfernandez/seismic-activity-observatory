# Procedimiento reproducible de las mediciones (K2, FR-011, SC-007)

Los comandos son los de `specs/011-mediciones-costes/quickstart.md` y los usados en `T087_corrida.txt`. Las cifras de las tablas son SINTÉTICO (esquema temporal `bench`, semilla 20251113); lo marcado REAL viene de las tablas reales en solo lectura.

## Requisitos

- Stack levantado y sano: `docker compose up -d` (servicios `kafka`, `postgres`, `producer`, `api`, `consumer`; `docker compose config --services` no debe mostrar ninguno más).
- Base cargada: `usgs_historical` = 18.302 en `live.current_event` (features `historico-2025` y `api` cerradas).
- `.env` con `POSTGRES_USER`/`POSTGRES_PASSWORD` y las contraseñas de los roles (el servicio `tests` las toma de ahí). Sin secretos en el repositorio.
- Carpeta `docs/evidencias/mediciones/` montada en escritura en el servicio `tests` (`compose.yaml`, `/app/evidence-mediciones`).

## Orden

1. Pruebas sin Docker (estadísticos, generador, costes, SQL estático):
   `.venv/Scripts/python.exe -m pytest -m "not integration" tests/scripts/test_bench_*.py`
2. Ciclo de vida de `bench` (crea y elimina el esquema; aborta si existe uno ajeno):
   `docker compose --profile test run --rm tests python -m pytest -m integration tests/integration/test_bench_schema.py`
3. Ensayo rápido (un solo tamaño; **sobrescribe** las tablas de `docs/evidencias/mediciones/`; úsalo solo antes de la corrida completa o repite después el paso 4):
   `docker compose --profile test run --rm tests python -m scripts.benchmarks.run_benchmarks --sizes 1000 --repeats 3 --budget 10 --yes`
4. Corrida completa (tamaños 1.000, 10.000 y 100.000; hasta 15 repeticiones por serie; presupuesto de 90 s por serie):
   `docker compose --profile test run --rm tests python -m scripts.benchmarks.run_benchmarks --yes`
5. Comprobación manual del aislamiento (esperado `NULL` y `0`):
   `docker compose exec postgres psql -U <admin> -d <base> -c "SELECT to_regnamespace('bench'), (SELECT count(*) FROM live.current_event WHERE event_id LIKE 'synthetic-bench-%');"`
6. Si una corrida se interrumpe y queda un `bench` marcado: añadir `--clean` al comando del paso 4 (solo elimina el esquema marcado `SINTETICO-BENCH-TEMPORAL`).

## Tiempo

La corrida completa medida (`T087_corrida.txt`, 2026-11-12) tardó 117 s en total (`duracion_segundos=117`): 102 mediciones, salida 0, sin violaciones de aislamiento. El bucle ingenuo de la integración geográfica a 100.000 puntos domina (acumulado 101,6 s al terminar `geo`). La estimación inicial («menos de una hora») era un tope; el valor real es el medido. El tiempo puede variar con el estado de la máquina.

## Fuentes de ruido

- El stack sigue en marcha durante la medición (decisión provisional 5): el consumidor y el productor comparten CPU y base con las mediciones.
- Las mediciones corren en la VM de Docker Desktop (WSL2), no en el equipo anfitrión; `equipo.md` describe esa VM.
- Las consultas se miden desde el cliente, con ida y vuelta incluida (a 1.000 filas domina); el tiempo del servidor sale de `EXPLAIN ANALYZE`.
- Caché caliente y `ANALYZE` previo; el calentamiento se descarta. N real puede ser menor que 15 si el presupuesto de 90 s se agota (mínimo 3).
- Los valores absolutos varían entre ejecuciones; lo que debe repetirse es la estructura de las tablas y el ranking de estrategias por operación y tamaño (SC-007).
- Volver a generar `indices.md` borra las recomendaciones redactadas a mano (están anotadas al final de ese documento): hay que reponerlas.

## Equipo anfitrión

`equipo.md` lee de la máquina CPU, núcleos, RAM, SO, Python, PostgreSQL y shapely. Los campos «Modelo del equipo anfitrión» y «Potencia del equipo anfitrión (W)» son PENDIENTE (alumno): no se rellenan sin que los aporte el alumno.

## Repetición desde un clon limpio

Con el stack levantado, repetir el paso 4 y comparar la estructura de `tablas.md` (mismas filas y columnas, 0 celdas vacías) y el ranking de estrategias por operación y tamaño con los de la corrida de referencia (`resultados.json`).
