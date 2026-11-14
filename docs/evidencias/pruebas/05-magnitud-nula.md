# Prueba 5: magnitud nula

## 1. Objetivo y requisito

Tabla I, prueba 5 (C). Una magnitud nula se conserva como NULL (no 0), la API la devuelve como `null` y el panel la muestra como ND. Constitución §5. FR-004, FR-005, SC-003, SC-005.

## 2. Procedimiento

1. En `TempDatabase`, pasar un mensaje sintético con `mag` nula por `process_message`.
2. SQL: `mag IS NULL` en `current_event` y 0 filas con `mag = 0`.
3. API: `mag` es `null` en `/api/eventos`; con `min_mag=0` el evento se cuenta como nulo excluido (`null_mag_excluded`), según `api.md`; en `/api/estadisticas` el histograma de magnitud cuenta 1 en `no_value`.
4. Panel en modo mock: ND (captura pendiente).

## 3. Esperado

`mag` NULL en SQL y `null` en la API, nunca 0; el panel lo muestra como ND.

## 4. Observado

- **No hay magnitudes nulas reales** en los datos de USGS de este proyecto: el caso es sintético (`is_synthetic = true`, `synthetic-*`) y aislado en base temporal. **ND sale del modo mock**, no de datos reales.
- **SQL (`geografia_prueba5.out`)**: `synthetic-geo-mag-nula` con `mag = NULL` en `current_event` y en `event_version`; filas con `mag = 0`: 0 en ambas tablas; el evento `synthetic-geo-negativos` conserva `mag = -0.06` y `depth_km = -0.18`.
- **API (2026-11-14)**: `test_null_magnitude_stays_null_in_db_and_api` pasa; 45 passed en `05-08_pytest.txt` (0 fallos).
- **Panel (ND)**: no capturado; plantilla [`05_captura_pendiente.md`](05_captura_pendiente.md), pendiente de captura del alumno (mock, datos sintéticos).

## 5. Evidencia

- [`../geografia-pais/geografia_prueba5.out`](../geografia-pais/geografia_prueba5.out) y [`../geografia-pais/geografia_prueba5.sql`](../geografia-pais/geografia_prueba5.sql).
- [`05-08_pytest.txt`](05-08_pytest.txt).
- Código: `tests/integration/test_acceptance_api.py::test_null_magnitude_stays_null_in_db_and_api`, `tests/integration/test_nulls_times.py`, `tests/integration/test_api_events.py`.
- [`05_captura_pendiente.md`](05_captura_pendiente.md).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_acceptance_api.py -k null_magnitude -q
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_nulls_times.py tests/integration/test_api_events.py -q
```

**Estado: Observada (sintética).** La captura de ND queda pendiente del alumno.
