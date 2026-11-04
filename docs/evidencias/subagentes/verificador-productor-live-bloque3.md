# Verificación bloque 3 (T010-T014), 004-productor-live

Pruebas ejecutadas por el verificador: unitarias 487 passed, 53 deselected; integración (failures + cycles) 10 passed en Docker. Consumidor, contratos, sql/001_schema.sql y enunciado sin cambios (git diff vacío). Ningún archivo supera 250 líneas.

| Tarea | Veredicto | Prueba |
|---|---|---|
| T010 | VERIFICADA | cycle.py: `publish` (espera ack) y después `mark_published`; un fallo de Kafka retorna antes de marcar. Clave = `message_key` (id); `received_at` común. |
| T011 | VERIFICADA | loop.py: latido solo con ok o fetch_error; backoff con reinicio tras ok; `grep synthetic_event producer/` vacío. |
| T012 | VERIFICADA | 500/429/lento/JSON inválido: integración pasa. |
| T013 | VERIFICADA | Ciclos, reinicio, `updated` y corte ack-marca con consumidor idempotente: integración pasa. |
| T014 | VERIFICADA | A1 pasa a comprobar `is_synthetic=false` en la base; unitarias completas pasan. |

Hallazgos bloqueantes/importantes: ninguno.
- `publisher.py` mantiene `acks="all"` y `enable_idempotence=True`; solo cambió la clave a `str|None`.
- El grep `synthetic producer/` solo coincide con la columna `is_synthetic` de las exclusiones; es aceptable.
- Límite conocido: T010 sin «falla antes» documentado. Con proporcionalidad es menor: el comportamiento está cubierto por test_cycle y la integración.
- `docs/evidencias/consumidor-idempotente` restaurado tras la integración.
