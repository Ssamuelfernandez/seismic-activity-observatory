# Prueba 3: versión con `updated` posterior

## 1. Objetivo y requisito

Tabla I, prueba 3 (C). Una versión con `updated` posterior cambia los datos actuales y las agregaciones, y la anterior queda en el historial. Constitución §2. FR-004, SC-003.

## 2. Procedimiento

1. Pasar por `process_message` una versión inicial y otra con `updated` posterior, otro país y otra hora (`synthetic-acc-*`, `TempDatabase`).
2. Leer `/api/eventos` y `/api/estadisticas`: datos nuevos y recuentos por país y por hora cambiados.
3. Consultar `event_version`: conserva ambas versiones.
4. Contraste en SQL con la secuencia FAQ12 (E1 con 4.2, 4.4 y 4.6).

## 3. Esperado

La fila actual toma la versión posterior; el recuento por país y por hora cambia; `event_version` conserva ambas.

## 4. Observado

- **Sintético (2026-11-14)**: `test_later_version_changes_current_and_aggregates` pasa (13 passed con 1 a 4 en `01-04_pytest.txt`, 0 fallos).
- **SQL FAQ12 (`bloque3_prueba3_4_versiones.out`)**: tras la versión intermedia, `event_version` pasa de 3 a 4 filas (E1: 4.2, 4.4, 4.6) y `current_event` sigue en 2 filas, con E1 en mag 4.6 y `updated_ms` 1793786940000.
- **Captura de panel**: no aplica con datos reales. Plantilla [`03_captura_pendiente.md`](03_captura_pendiente.md) que declara «datos sintéticos (TempDatabase), no visibles en el panel público; evidencia principal: SQL de T095». Pendiente del alumno si decide hacerla en un panel local etiquetado.

## 5. Evidencia

- [`../consumidor-idempotente/bloque3_prueba3_4_versiones.out`](../consumidor-idempotente/bloque3_prueba3_4_versiones.out) y [`../consumidor-idempotente/bloque3_prueba3_4_versiones.sql`](../consumidor-idempotente/bloque3_prueba3_4_versiones.sql).
- [`../consumidor-idempotente/faq12_antes_despues.out`](../consumidor-idempotente/faq12_antes_despues.out) y [`../consumidor-idempotente/bloque3_faq12.out`](../consumidor-idempotente/bloque3_faq12.out).
- [`01-04_pytest.txt`](01-04_pytest.txt).
- [`03_captura_pendiente.md`](03_captura_pendiente.md).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_acceptance_api.py -k later_version -q
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_faq12.py -q
```

**Estado: Observada (sintética).** Los datos son sintéticos por construcción; no hay versión posterior real que se pueda provocar a voluntad.
