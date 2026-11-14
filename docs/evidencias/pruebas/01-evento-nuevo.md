# Prueba 1: evento nuevo

## 1. Objetivo y requisito

Tabla I, prueba 1 (C). Un evento nuevo deja exactamente 1 fila actual y es visible en `/api/eventos`, en `/api/estadisticas` y en el panel. FR-004, FR-005, SC-003.

## 2. Procedimiento

Parte real (hasta PostgreSQL):
1. Contar `current_event` reales, `event_version` e `ingest_state` antes y después de un ciclo del productor que publique un evento nuevo de USGS.

Parte API (sintética, en `TempDatabase`, nunca en `live`):
2. Pasar un mensaje `synthetic-acc-*` por `process_message` y comprobar por SQL 1 fila en `current_event`.
3. Leer `/api/eventos` y `/api/estadisticas` con `request_api`: el evento aparece y el total suma 1.

Parte panel: captura del panel público con un evento real reciente (plantilla pendiente).

## 3. Esperado

1 fila actual para el `event_id`; el evento aparece en `/api/eventos` y suma 1 al total de `/api/estadisticas`.

## 4. Observado

- **Real (2026-11-04, evento `ok2026vqse`, USGS)**: `current_event` reales 192 a 193, `event_version` 196 a 198, `ingest_state` 192 a 193 (ventana 23:35:52Z a 23:39:16Z). Llega hasta PostgreSQL; no incluye API ni panel.
- **Sintética (2026-11-14, `TempDatabase`)**: `test_new_event_is_one_current_row_visible_in_api_and_stats` pasa (5 pruebas del archivo en 2.53 s en `B1_test_acceptance_api.txt`; 13 passed en `01-04_pytest.txt`, que agrupa 1 a 4).
- **Panel**: no capturado; plantilla [`01_captura_pendiente.md`](01_captura_pendiente.md), pendiente de captura del alumno.

## 5. Evidencia

- [`../productor-live/prueba1_evento_nuevo.out`](../productor-live/prueba1_evento_nuevo.out) (real).
- [`01-04_pytest.txt`](01-04_pytest.txt) y [`B1_test_acceptance_api.txt`](B1_test_acceptance_api.txt) (sintética).
- Código: `tests/integration/test_acceptance_api.py::test_new_event_is_one_current_row_visible_in_api_and_stats`.
- [`01_captura_pendiente.md`](01_captura_pendiente.md) (plantilla, datos reales).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_acceptance_api.py -k new_event -q
```

**Estado: Observada** (parte real hasta PostgreSQL) y **Observada (sintética)** (parte API). La captura del panel queda pendiente del alumno.
