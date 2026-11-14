# Prueba 8: reinicio del consumidor

## 1. Objetivo y requisito

Tabla I, prueba 8 (C). Un consumidor detenido y reiniciado reanuda desde el último offset confirmado y deja la misma base que una ejecución sin corte. Constitución §1. FR-004.

## 2. Procedimiento

1. Ejecución de referencia sin corte con la secuencia sintética faq12 (5 mensajes); guardar el SQL.
2. Repetir con un corte inyectado tras el commit de PostgreSQL en el offset 2 (el proceso termina con código 137 y Compose lo reinicia).
3. Comparar el SQL con corte y sin corte, y comprobar el grupo en lag 0.

## 3. Esperado

SQL idéntico; 2 actuales, 3 versiones y 0 en cuarentena; 0 versiones duplicadas.

## 4. Observado

- **Real con contenedores (2026-11-04, `prueba8_reinicio.log/.out`)**: log con `FAULT crash_after_db_commit offset=2`, tras el reinicio `decision=redelivery_ignored` en los offsets 2 y 3 y `decision=new_event` en el 4; comprobaciones PASS: «El SQL con corte es idéntico al de la ejecución sin corte», «2 actuales, 3 versiones y 0 en cuarentena», «0 versiones duplicadas», proceso terminado una vez con código 137, grupo en lag 0 y `.env` sin cambios. Los mensajes son sintéticos (`synthetic-faq12-*`) sobre Kafka real.
- **Corte simulado (`bloque4_prueba8_corte_simulado.out`)**: tras corte en el offset 2 y reinicio, `event_version` con offsets 0, 2 y 4 y `current_event` con E1 en mag 4.6 y E2 en 3.1.
- **Ejecución 2026-11-14**: `test_restart_crash.py` dentro de 45 passed en `05-08_pytest.txt`, 0 fallos.

## 5. Evidencia

- [`../consumidor-idempotente/prueba8_reinicio.log`](../consumidor-idempotente/prueba8_reinicio.log) y [`../consumidor-idempotente/prueba8_reinicio.out`](../consumidor-idempotente/prueba8_reinicio.out) (real).
- [`../consumidor-idempotente/bloque4_prueba8_corte_simulado.out`](../consumidor-idempotente/bloque4_prueba8_corte_simulado.out) y [`../consumidor-idempotente/bloque4_prueba8_corte_simulado.sql`](../consumidor-idempotente/bloque4_prueba8_corte_simulado.sql).
- [`../consumidor-idempotente/bloque6_restart_consola.txt`](../consumidor-idempotente/bloque6_restart_consola.txt).
- [`05-08_pytest.txt`](05-08_pytest.txt).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_restart_crash.py -q
```

El recorrido real con contenedores está descrito en `prueba8_reinicio.out` y `bloque6_restart_consola.txt`.

**Estado: Observada** (corte real con contenedores; datos de entrada sintéticos). No hay captura de panel.
