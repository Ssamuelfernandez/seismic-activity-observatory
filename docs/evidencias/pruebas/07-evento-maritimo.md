# Prueba 7: evento marítimo (sin país)

## 1. Objetivo y requisito

Tabla I, prueba 7 (C). Un evento en el mar tiene `country_id` NULL, no va a cuarentena, se muestra como «Sin país asignado» y sigue contado en el análisis. Constitución §4. FR-004, SC-003, SC-005.

## 2. Procedimiento

1. En `TempDatabase`, pasar un mensaje sintético con coordenadas en el Atlántico por `process_message`.
2. SQL: `country_id` NULL y 0 filas en cuarentena.
3. API: `/api/eventos?country_id=none` lo devuelve; `/api/estadisticas` lo suma al total y al recuento por hora.
4. Panel público con datos reales: filtro «Sin país asignado» (captura pendiente).

## 3. Esperado

`country_id` NULL, sin cuarentena; total = con país + sin país; el evento entra en el total y en el recuento por hora.

## 4. Observado

- **Sintético, SQL (`geografia_prueba7.out`)**: `synthetic-geo-atlantico` con `country_id` NULL; total 3 = 2 con país + 1 sin país. `synthetic-geo-madrid` obtiene ESP por geometría aunque `place` diga «París, Francia».
- **Sintético, API (2026-11-14)**: `test_sea_event_has_no_country_and_is_counted` pasa; 45 passed en `05-08_pytest.txt` (0 fallos).
- **Real**: `geo_real_day.out` (feed real de un día de USGS, 181 eventos): 153 con país y 28 sin país (`country_id` NULL), 0 sin geometría válida; el panel público con el filtro «Sin país asignado» no está capturado: plantilla [`07_captura_pendiente.md`](07_captura_pendiente.md), pendiente de captura del alumno (datos reales).

## 5. Evidencia

- [`../geografia-pais/geografia_prueba7.out`](../geografia-pais/geografia_prueba7.out) y [`../geografia-pais/geografia_prueba7.sql`](../geografia-pais/geografia_prueba7.sql).
- [`../geografia-pais/geo_real_day.out`](../geografia-pais/geo_real_day.out) (real) y [`../geografia-pais/geografia_pruebas5_7_kafka.out`](../geografia-pais/geografia_pruebas5_7_kafka.out).
- [`05-08_pytest.txt`](05-08_pytest.txt).
- [`07_captura_pendiente.md`](07_captura_pendiente.md).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_acceptance_api.py -k sea_event -q
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_geography.py -q
```

**Estado: Observada (sintética)** para SQL y API; la parte real en el panel (captura) queda pendiente del alumno.
