# Borrador: consumidor-idempotente

Apuntes para la memoria y la defensa. Cubre C1–C8 y C13; pruebas de aceptación 2 (reenvío), 3, 4, 6 y 8. Todo lo citado existe en el repositorio; lo que no se implementó se dice en «Qué no se hizo».

## Qué se entrega

| Entregable | Dónde |
|---|---|
| Consumidor (bucle, canalización, reintentos, contadores, gancho de corte) | `consumer/` |
| Lógica pura (decodificar, validar, versión, transformar, fila de cuarentena) | `common/` (`decode.py`, `storable.py`, `validation.py`, `processing.py`, `transform.py`, `quarantine_row.py`) |
| SQL del consumidor | `consumer/queries.py` |
| Pruebas unitarias y de integración (PostgreSQL real, servicio `tests`) | `tests/` |
| Verificación con Kafka y PostgreSQL reales | `scripts/verify_consumer.py` (`faq12`, `quarantine`, `restart`) |
| Evidencias | `docs/evidencias/consumidor-idempotente/` |
| Spec, plan, investigación, tareas, bitácora | `specs/003-consumidor-idempotente/` |

## Decisiones principales

- **Un mensaje, una transacción**: escritura en PostgreSQL, línea `decision=…`, y solo después commit del offset. Si el proceso muere entre ambos commits, la reentrega se ignora (`redelivery_ignored`) gracias a `ON CONFLICT (event_id, updated_ms) DO NOTHING`. Esto es la prueba 8.
- **Versiones**: solo una `updated` estrictamente mayor sustituye al estado actual; el historial conserva todas las versiones distintas. La decisión (`decide_version_outcome`) es pura; el `SELECT … FOR UPDATE` va dentro de la transacción.
- **Cuarentena**: un mensaje inválido produce una fila con su motivo, la referencia (tema, partición, offset) y el SHA-256 de los bytes recibidos; clave de idempotencia `(original_sha256, reason)`. El saneado se decide antes del `INSERT`, inspeccionando el contenido, no por el SQLSTATE.
- **Regla de copia a cuarentena**: `source` solo si es uno de los tres valores del `CHECK`; `event_id` solo si es cadena; `is_synthetic` solo si es booleano exacto. Por eso las filas ilegibles (bytes no UTF-8 y tombstone) quedan con `is_synthetic = false` (FR-011); el resto conserva `true` si el mensaje es sintético. Se ve en `prueba6_cuarentena.out`.
- **Errores de base**: los de contenido (`db_constraint_violation`) van a cuarentena sin reintento; los de conexión se reintentan sin límite y no confirman el offset.
- **Solo el tema live**: el consumidor lee `KAFKA_TOPIC`; el replay queda fuera de alcance.
- **Gancho de prueba**: `consumer/fault_hook.py` termina el proceso una sola vez en un offset configurado (`CONSUMER_FAULT_CRASH_AT_OFFSET`), solo para mensajes con `is_synthetic = true`; vacío en producción.

## Hallazgos

- `build_quarantine_row` tiene 4 parámetros (`decoded, reason, ref, now`; los bytes van en `decoded.raw`). El plan y las tareas decían 5; corregido en `plan.md` y `tasks.md`.
- Un JSON anidado a 1500 niveles no provoca `RecursionError` en Python 3.12: se decodifica y lo rechaza la validación (`invalid_envelope` si la raíz es una lista) o la almacenabilidad (`db_constraint_violation`, profundidad > 64). El `RecursionError` solo salta con anidamientos extremos; la prueba usa 200000 niveles porque el límite del analizador en C cambia entre parches de CPython 3.12. Corregido en `research.md` §5.
- Los verificadores anotaron que `validation_envelope` importa `topic_mode` de `kafka_topics`, que arrastra `aiokafka` (rompe la pureza de lo puro); y que `validate_message` lanza `ValueError` con un tema desconocido. Quedan como decisiones provisionales de la bitácora.
- Contadores (C8): las cifras de FR-036 (5/5, 7/5 y 7/7) se concilian con SQL en `bloque4_contadores_integracion.out`, con `process_record` sobre una base temporal y no con el consumidor en Docker.

## Pruebas realizadas

- 447 pruebas recogidas: 412 unitarias y 35 de integración (`pytest_unitarias.txt`, `pytest_integracion.txt`).
- Escenarios con Kafka y PostgreSQL reales: FAQ 12 (`faq12_antes_despues.*`), reenvío (`prueba2_reenvio.out`), versiones (`prueba3_4_versiones.out`), cuarentena (`prueba6_cuarentena.out`), reinicio con corte entre commits (`prueba8_reinicio.log/.out`, 14 comprobaciones).
- Regresión de la verificación de 002 (`regresion_002.txt`) y contratos sin cambios (`bloque6_cierre_T081.txt`).

## Qué no se hizo (diferido)

Tareas marcadas `- [-]` en la sección «Diferidas» de `specs/003-consumidor-idempotente/tasks.md`: catálogo de países (`country_id` queda `NULL`), comprobación de esquema al arrancar, paridad `live`/`replay`, caída de PostgreSQL y de Kafka con Docker real (cubiertas solo con dobles), conciliación de contadores con Docker y la memoria `docs/memoria.md` §4. La spec aún describe parte de esto con MUST (FR-025, FR-026, FR-032, SC-006, SC-011, US2.5, US6) sin marcarlo como diferido: pendiente de decisión del alumno.

## Para la defensa

- Por qué el orden «PostgreSQL, luego offset» y no al revés: un corte entre ambos reentrega, nunca pierde.
- Por qué `FOR UPDATE` y no solo `ON CONFLICT`: hace falta comparar `updated_ms` con el estado actual de forma atómica.
- Por qué la cuarentena guarda el hash de los bytes recibidos y no del JSON re-serializado.
