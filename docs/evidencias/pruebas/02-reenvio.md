# Prueba 2: reenvío de la misma versión

## 1. Objetivo y requisito

Tabla I, prueba 2 (C). Reenviar la misma versión no cambia nada. Constitución §1 (al menos una vez e idempotente). FR-004.

## 2. Procedimiento

1. Anotar `count(*)` de `current_event`, `event_version`, `quarantine` y `date_dim`.
2. Reenviar 100 veces la misma versión (`test_hundred_resends_change_nothing`).
3. Repetir los recuentos y comparar.
4. En el productor: segundo ciclo con la misma respuesta de USGS (no publica nada) y reinicio sobre la misma base.

## 3. Esperado

Los recuentos antes y después son idénticos.

## 4. Observado

- **Sintético (consumidor, `bloque3_prueba2_reenvio.out`)**: antes y después de las 100 repeticiones, `current_event` = 2, `event_version` = 3, `quarantine` = 0, `date_dim` = 1.
- **Real (productor)**: tras `docker compose kill producer`, el primer ciclo dio `published=0 skipped=192` con `current_event` 194 y `event_version` 195 antes (comentario de `../productor-live/prueba2_reenvio.out`).
- **Ejecución 2026-11-14**: `test_idempotence.py` y `test_producer_cycles.py` en 13 passed (`01-04_pytest.txt`, 0 fallos).

## 5. Evidencia

- [`../consumidor-idempotente/bloque3_prueba2_reenvio.out`](../consumidor-idempotente/bloque3_prueba2_reenvio.out) y [`../consumidor-idempotente/bloque3_prueba2_reenvio.sql`](../consumidor-idempotente/bloque3_prueba2_reenvio.sql).
- [`../consumidor-idempotente/prueba2_reenvio.out`](../consumidor-idempotente/prueba2_reenvio.out).
- [`../productor-live/prueba2_reenvio.out`](../productor-live/prueba2_reenvio.out).
- [`01-04_pytest.txt`](01-04_pytest.txt).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_idempotence.py tests/integration/test_producer_cycles.py -q
```

**Estado: Observada (sintética)** para el consumidor (datos `synthetic-*` en base temporal) con contraste real del productor (hecho de reinicio). Sin captura de panel: no aplica.
