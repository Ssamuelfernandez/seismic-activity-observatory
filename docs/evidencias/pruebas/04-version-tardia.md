# Prueba 4: versión antigua llegada tarde

## 1. Objetivo y requisito

Tabla I, prueba 4 (C). Una versión con `updated` menor llegada tarde no cambia la fila actual ni la API, pero queda en el historial. Constitución §2. FR-004, SC-003.

## 2. Procedimiento

1. Pasar por `process_message` una versión reciente de `synthetic-acc-*` en `TempDatabase`; guardar la respuesta de `/api/eventos` y `/api/estadisticas`.
2. Pasar otra versión con `updated` menor.
3. Repetir las consultas a la API y comparar; consultar `event_version`.

## 3. Esperado

API y estadísticas idénticas antes y después; la versión tardía figura en `event_version`.

## 4. Observado

- **Sintético (2026-11-14)**: `test_late_older_version_keeps_current_and_api_unchanged` pasa (13 passed con 1 a 3 en `01-04_pytest.txt`, 0 fallos).
- **SQL FAQ12 (`bloque3_prueba3_4_versiones.out`)**: la versión tardía (E1, `updated_ms` 1793786820000, mag 4.4) entra en `event_version` (3 a 4 filas) y `current_event` mantiene 2 filas con E1 en 1793786940000 y mag 4.6.

## 5. Evidencia

- [`../consumidor-idempotente/bloque3_prueba3_4_versiones.out`](../consumidor-idempotente/bloque3_prueba3_4_versiones.out) y [`../consumidor-idempotente/bloque3_prueba3_4_versiones.sql`](../consumidor-idempotente/bloque3_prueba3_4_versiones.sql).
- [`../consumidor-idempotente/faq12_antes_despues.out`](../consumidor-idempotente/faq12_antes_despues.out).
- [`01-04_pytest.txt`](01-04_pytest.txt).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_acceptance_api.py -k late_older -q
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_faq12.py -q
```

**Estado: Observada (sintética).** No hay captura de panel prevista para esta prueba.
