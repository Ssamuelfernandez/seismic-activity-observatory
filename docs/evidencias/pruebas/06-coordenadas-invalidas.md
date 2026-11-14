# Prueba 6: coordenadas inválidas

## 1. Objetivo y requisito

Tabla I, prueba 6 (C). Un mensaje con coordenadas inválidas va a cuarentena con el motivo y una referencia al original; no hay fila en `current_event` ni punto inventado. Constitución §6. FR-004.

## 2. Procedimiento

1. En `TempDatabase`, enviar un mensaje sintético con latitud 145 (y otros casos inválidos).
2. Consultar `quarantine`: motivo, tema, partición, offset y `original_sha256`.
3. Comprobar que no hay fila en `current_event` para ese evento.

## 3. Esperado

Una fila en cuarentena con motivo `coordinates_out_of_range` (o el motivo del contrato) y referencia al original; ninguna fila actual.

## 4. Observado

- **Sintético, consumidor (`bloque3_prueba6_cuarentena.out`)**: latitud 145 (`synthetic-faq12-e1`) a `coordinates_out_of_range`, `earthquakes.live`, partición 0, offset 7, `original_sha256` `04ea12de50c3...`; un caso por motivo del contrato (14 filas entre `live` y `replay`).
- **Sintético, geografía (`geografia_prueba6_cuarentena.out`)**: 5 filas en cuarentena: `lat-145` y `lon-nan` a `coordinates_out_of_range`, `no-point` a `invalid_geometry`, `sin-time` a `missing_time`, `sin-updated` a `missing_updated`; los eventos guardados son solo los 3 casos geográficos sintéticos.
- **Ejecución 2026-11-14**: `test_quarantine.py` (`test_latitude_145_goes_to_quarantine_only`, `test_one_case_per_contract_reason`) dentro de 45 passed en `05-08_pytest.txt`, 0 fallos.

## 5. Evidencia

- [`../consumidor-idempotente/bloque3_prueba6_cuarentena.out`](../consumidor-idempotente/bloque3_prueba6_cuarentena.out) y [`../consumidor-idempotente/bloque3_prueba6_cuarentena.sql`](../consumidor-idempotente/bloque3_prueba6_cuarentena.sql).
- [`../consumidor-idempotente/prueba6_cuarentena.out`](../consumidor-idempotente/prueba6_cuarentena.out).
- [`../geografia-pais/geografia_prueba6_cuarentena.out`](../geografia-pais/geografia_prueba6_cuarentena.out) y [`../geografia-pais/geografia_prueba6_cuarentena.sql`](../geografia-pais/geografia_prueba6_cuarentena.sql).
- [`05-08_pytest.txt`](05-08_pytest.txt).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_quarantine.py -q
```

**Estado: Observada (sintética).** No hay captura de panel prevista.
