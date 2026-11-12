# Quickstart: mediciones-costes (011)

Guía de validación. No incluye código; los detalles están en `plan.md`, `research.md` y `data-model.md`.

## Requisitos

- Stack levantado y sano (`docker compose up -d`), con la base cargada (`007-api` y `006-historico-2025` cerradas): `usgs_historical` = 18.302 en `live.current_event`.
- `.env` con `POSTGRES_USER`/`POSTGRES_PASSWORD` y las contraseñas de los roles (el servicio `tests` las toma de ahí).
- El stack sigue en marcha durante la medición (ruido declarado, prov. 5). Tiempo estimado de la corrida completa: menos de una hora (el bucle ingenuo a 100.000 puntos domina).

## 1. Pruebas sin Docker

```
.venv/Scripts/python.exe -m pytest -m "not integration" tests/scripts/test_bench_*.py
```

Esperado: todo en verde (estadísticos, generador determinista, costes sin valores inventados, SQL estático con `bench.`).

## 2. Ciclo de vida de `bench` (servicio `tests`)

```
docker compose --profile test run --rm tests python -m pytest -m integration tests/integration/test_bench_schema.py
```

Esperado: crea y elimina `bench`; aborta si existe uno ajeno; `--clean` solo elimina el marcado; `to_regnamespace('bench')` es NULL al final.

## 3. Ensayo rápido

```
docker compose --profile test run --rm tests python -m scripts.benchmarks.run_benchmarks --sizes 1000 --repeats 3 --budget 10 --yes
```

Esperado: genera `docs/evidencias/mediciones/` con tablas de un solo tamaño; el esquema `bench` ya no existe al terminar.

## 4. Corrida completa

```
docker compose --profile test run --rm tests python -m scripts.benchmarks.run_benchmarks --yes
```

Esperado (SC-001 a SC-005): resultados para los 3 tamaños, 0 celdas vacías, un plan por consulta de Postgres, `equipo.md` leído de la máquina, `aislamiento.md` con 0 filas de bench en `live`, `replay`, `quarantine`, `exclusion` y recuentos iguales, `costes.md` con 6 categorías y «PENDIENTE (alumno)» donde falte un dato.

## 5. Comprobación manual del aislamiento

```
docker compose exec postgres psql -U <admin> -d <base> -c "SELECT to_regnamespace('bench'), (SELECT count(*) FROM live.current_event WHERE event_id LIKE 'synthetic-bench-%');"
```

Esperado: `NULL` y `0`.

## 6. Repetición

Repetir el paso 4 desde un clon limpio: mismas tablas y mismo ranking de estrategias por operación y tamaño (los valores absolutos pueden variar, SC-007).

## Pendiente del alumno

Rellenar en `costes.md` las entradas «PENDIENTE (alumno)» (horas, potencia, precio y vida útil del equipo, €/kWh, tarifa de nube, visitas, límites de cuotas gratuitas con fecha) y el modelo de equipo anfitrión en `equipo.md`; revisar las recomendaciones sobre índices (no se edita el contrato).
